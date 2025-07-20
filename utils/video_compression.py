"""
Video compression utilities for handling large video files.

This module provides functionality to compress videos that exceed Telegram's
50MB file size limit while maintaining acceptable quality.
"""

import os
import asyncio
import logging
import shutil
import tempfile
import psutil
import signal
from dataclasses import dataclass
from typing import Optional, Callable
import ffmpeg
from pathlib import Path

# Import monitoring utilities
from utils.compression_monitoring import (
    CompressionOperationLogger,
    log_compression_start,
    log_compression_result,
    log_disk_space_warning,
    log_compression_timeout,
    log_ffmpeg_error,
    log_cleanup_operation,
    log_performance_metrics,
    compression_logger,
)

logger = logging.getLogger(__name__)


class CompressionError(Exception):
    """Base exception for video compression errors."""

    pass


class FFmpegNotFoundError(CompressionError):
    """Raised when FFmpeg is not available on the system."""

    pass


class CompressionTimeoutError(CompressionError):
    """Raised when compression exceeds the timeout limit."""

    pass


class InsufficientDiskSpaceError(CompressionError):
    """Raised when there's not enough disk space for compression."""

    pass


class UnsupportedFormatError(CompressionError):
    """Raised when video format is not supported."""

    pass


class VideoCorruptedError(CompressionError):
    """Raised when video file is corrupted or unreadable."""

    pass


class CompressionQualityError(CompressionError):
    """Raised when compression would result in unacceptable quality."""

    pass


@dataclass
class VideoInfo:
    """Container for video metadata information."""

    width: int
    height: int
    duration: float
    fps: float
    bitrate: int
    codec: str
    size_mb: float


@dataclass
class CompressionResult:
    """Container for video compression results."""

    success: bool
    original_path: str
    compressed_path: Optional[str]
    original_size_mb: float
    compressed_size_mb: Optional[float]
    compression_ratio: Optional[float]
    processing_time: float
    error_message: Optional[str]


def check_ffmpeg_availability() -> bool:
    """
    Check if FFmpeg is available on the system.

    Returns:
        True if FFmpeg is available, False otherwise
    """
    try:
        import subprocess

        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def check_disk_space(path: str, required_mb: float) -> bool:
    """
    Check if there's enough disk space for compression.

    Args:
        path: Directory path to check
        required_mb: Required space in MB

    Returns:
        True if enough space is available, False otherwise
    """
    try:
        statvfs = os.statvfs(path)
        available_bytes = statvfs.f_frsize * statvfs.f_bavail
        available_mb = available_bytes / (1024 * 1024)

        logger.info(
            f"Disk space check: {available_mb:.2f}MB available, {required_mb:.2f}MB required"
        )
        return available_mb >= required_mb
    except Exception as e:
        logger.error(f"Error checking disk space: {str(e)}")
        return False


def get_compression_error_message(error: Exception) -> str:
    """
    Generate user-friendly error messages for different compression errors.

    Args:
        error: The exception that occurred

    Returns:
        User-friendly error message
    """
    if isinstance(error, FFmpegNotFoundError):
        return "FFmpeg is not available on the system"
    elif isinstance(error, CompressionTimeoutError):
        return "Compression timeout after specified time limit"
    elif isinstance(error, InsufficientDiskSpaceError):
        return "Insufficient disk space for compression"
    elif isinstance(error, UnsupportedFormatError):
        return "Unsupported video format for compression"
    elif isinstance(error, VideoCorruptedError):
        return "Video file is corrupted or damaged"
    elif isinstance(error, CompressionQualityError):
        return "Compression failed to achieve target size"
    elif isinstance(error, FileNotFoundError):
        return "Input video file not found"
    else:
        return f"Unexpected compression error: {str(error)}"


async def get_video_info(video_path: str) -> VideoInfo:
    """
    Standalone function to extract video metadata using FFmpeg.

    Args:
        video_path: Path to the video file

    Returns:
        VideoInfo object with video metadata

    Raises:
        FileNotFoundError: If video file doesn't exist
        VideoCorruptedError: If video file is corrupted or unsupported
        FFmpegNotFoundError: If FFmpeg is not available
        UnsupportedFormatError: If video format is not supported
    """
    logger.info(f"Extracting video info from: {video_path}")

    if not os.path.exists(video_path):
        error_msg = f"Video file not found: {video_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Check if FFmpeg is available
    if not check_ffmpeg_availability():
        error_msg = "FFmpeg is not available on the system"
        logger.error(error_msg)
        raise FFmpegNotFoundError(error_msg)

    try:
        # Get video file size
        file_size_bytes = os.path.getsize(video_path)
        size_mb = file_size_bytes / (1024 * 1024)
        logger.info(f"Video file size: {size_mb:.2f}MB")

        # Use ffmpeg.probe to extract video metadata with timeout
        try:
            probe = ffmpeg.probe(video_path)
        except ffmpeg.Error as e:
            stderr_output = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg probe error: {stderr_output}")

            # Check for specific error patterns
            if "Invalid data found" in stderr_output or "moov atom not found" in stderr_output:
                raise VideoCorruptedError(f"Video file is corrupted or incomplete: {video_path}")
            elif "Unknown format" in stderr_output or "Invalid argument" in stderr_output:
                raise UnsupportedFormatError(f"Unsupported video format: {video_path}")
            else:
                raise VideoCorruptedError(f"Cannot read video file: {stderr_output}")

        # Find the video stream
        video_stream = None
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream is None:
            error_msg = f"No video stream found in file: {video_path}"
            logger.error(error_msg)
            raise UnsupportedFormatError(error_msg)

        # Extract video properties with comprehensive error handling
        try:
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))

            # Handle duration - can be in stream or format
            duration = 0.0
            if "duration" in video_stream:
                duration = float(video_stream["duration"])
            elif "format" in probe and "duration" in probe["format"]:
                duration = float(probe["format"]["duration"])

            # Handle frame rate
            fps = 0.0
            if "r_frame_rate" in video_stream:
                fps_str = video_stream["r_frame_rate"]
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    if int(den) != 0:
                        fps = float(num) / float(den)
                else:
                    fps = float(fps_str)
            elif "avg_frame_rate" in video_stream:
                fps_str = video_stream["avg_frame_rate"]
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    if int(den) != 0:
                        fps = float(num) / float(den)
                else:
                    fps = float(fps_str)

            # Handle bitrate
            bitrate = 0
            if "bit_rate" in video_stream:
                bitrate = int(video_stream["bit_rate"])
            elif "format" in probe and "bit_rate" in probe["format"]:
                bitrate = int(probe["format"]["bit_rate"])

            # Get codec name
            codec = video_stream.get("codec_name", "unknown")

            # Validate extracted data
            if width <= 0 or height <= 0:
                error_msg = f"Invalid video dimensions: {width}x{height}"
                logger.error(error_msg)
                raise VideoCorruptedError(error_msg)

            if duration <= 0:
                error_msg = f"Invalid video duration: {duration}"
                logger.error(error_msg)
                raise VideoCorruptedError(error_msg)

            video_info = VideoInfo(
                width=width,
                height=height,
                duration=duration,
                fps=fps,
                bitrate=bitrate,
                codec=codec,
                size_mb=size_mb,
            )

            logger.info(
                f"Video info extracted successfully: {width}x{height}, {duration:.1f}s, {codec}"
            )
            return video_info

        except (ValueError, TypeError, KeyError) as e:
            error_msg = f"Error parsing video metadata: {str(e)}"
            logger.error(error_msg)
            raise VideoCorruptedError(error_msg)

    except (FFmpegNotFoundError, VideoCorruptedError, UnsupportedFormatError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        error_msg = f"Unexpected error extracting video info: {str(e)}"
        logger.error(error_msg)
        raise VideoCorruptedError(error_msg)


def calculate_compression_ratio(original_size_mb: float, compressed_size_mb: float) -> float:
    """
    Calculate compression ratio between original and compressed file sizes.

    Args:
        original_size_mb: Original file size in MB
        compressed_size_mb: Compressed file size in MB

    Returns:
        Compression ratio (e.g., 0.5 means 50% of original size)
    """
    if original_size_mb <= 0:
        return 0.0
    return compressed_size_mb / original_size_mb


def validate_file_size(file_path: str, max_size_mb: float) -> bool:
    """
    Validate that a file is within the specified size limit.

    Args:
        file_path: Path to the file to check
        max_size_mb: Maximum allowed size in MB

    Returns:
        True if file is within limit, False otherwise
    """
    if not os.path.exists(file_path):
        return False

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return file_size_mb <= max_size_mb


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in MB, or 0.0 if file doesn't exist
    """
    if not os.path.exists(file_path):
        return 0.0

    return os.path.getsize(file_path) / (1024 * 1024)


def check_video_size_against_limit(
    video_path: str, size_limit_mb: float = 50.0
) -> tuple[bool, float]:
    """
    Check if video file size exceeds the specified limit.

    Args:
        video_path: Path to the video file
        size_limit_mb: Size limit in MB (default: 50MB for Telegram)

    Returns:
        Tuple of (needs_compression, file_size_mb)
        - needs_compression: True if file exceeds limit, False otherwise
        - file_size_mb: Actual file size in MB
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False, 0.0

    file_size_mb = get_file_size_mb(video_path)
    needs_compression = file_size_mb > size_limit_mb

    logger.info(
        f"Video size check: {file_size_mb:.2f}MB {'>' if needs_compression else '<='} {size_limit_mb}MB limit"
    )

    return needs_compression, file_size_mb


def should_compress_video(video_path: str, max_size_mb: float = 50.0) -> bool:
    """
    Determine if a video file should be compressed based on size limit.

    Args:
        video_path: Path to the video file
        max_size_mb: Maximum allowed size in MB

    Returns:
        True if video should be compressed, False otherwise
    """
    needs_compression, _ = check_video_size_against_limit(video_path, max_size_mb)
    return needs_compression


def cleanup_temp_files(*file_paths: str) -> None:
    """
    Clean up temporary files safely with comprehensive error handling.

    Args:
        *file_paths: Variable number of file paths to clean up
    """
    if not file_paths:
        return

    compression_logger.info(f"Cleaning up {len(file_paths)} temporary files")

    files_cleaned = 0
    total_size_freed = 0.0

    for file_path in file_paths:
        if not file_path:
            continue

        try:
            if os.path.exists(file_path):
                # Check if file is actually a file (not a directory)
                if os.path.isfile(file_path):
                    # Get file size before deletion for logging
                    try:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        os.unlink(file_path)
                        files_cleaned += 1
                        total_size_freed += file_size_mb
                        compression_logger.info(
                            f"Cleaned up temporary file: {file_path} ({file_size_mb:.2f}MB)"
                        )
                    except PermissionError:
                        compression_logger.error(f"Permission denied cleaning up file: {file_path}")
                    except OSError as e:
                        compression_logger.error(f"OS error cleaning up file {file_path}: {str(e)}")
                elif os.path.isdir(file_path):
                    compression_logger.warning(
                        f"Skipping directory cleanup (expected file): {file_path}"
                    )
                else:
                    compression_logger.warning(f"Unknown file type, skipping cleanup: {file_path}")
            else:
                compression_logger.debug(
                    f"Temporary file already removed or doesn't exist: {file_path}"
                )

        except Exception as e:
            compression_logger.error(
                f"Unexpected error cleaning up temporary file {file_path}: {str(e)}"
            )

    # Log cleanup operation summary
    if files_cleaned > 0:
        log_cleanup_operation(files_cleaned, total_size_freed)


def cleanup_temp_directory(temp_dir: str, max_age_hours: int = 24) -> None:
    """
    Clean up old temporary files in the specified directory.

    Args:
        temp_dir: Directory to clean up
        max_age_hours: Maximum age of files to keep (in hours)
    """
    if not os.path.exists(temp_dir):
        compression_logger.debug(f"Temporary directory doesn't exist: {temp_dir}")
        return

    compression_logger.info(
        f"Cleaning up temporary directory: {temp_dir} (files older than {max_age_hours}h)"
    )

    import time

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    cleaned_size_mb = 0.0

    try:
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)

            try:
                if os.path.isfile(file_path):
                    # Check file age
                    file_age = current_time - os.path.getmtime(file_path)

                    if file_age > max_age_seconds:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        os.unlink(file_path)
                        cleaned_count += 1
                        cleaned_size_mb += file_size_mb
                        compression_logger.debug(
                            f"Cleaned up old temp file: {filename} ({file_size_mb:.2f}MB, {file_age/3600:.1f}h old)"
                        )

            except Exception as e:
                compression_logger.warning(f"Error cleaning up temp file {filename}: {str(e)}")

        # Log cleanup operation summary
        log_cleanup_operation(cleaned_count, cleaned_size_mb)

    except Exception as e:
        compression_logger.error(f"Error cleaning up temporary directory {temp_dir}: {str(e)}")


def ensure_temp_directory(temp_dir: str) -> bool:
    """
    Ensure temporary directory exists and is writable.

    Args:
        temp_dir: Directory path to check/create

    Returns:
        True if directory is ready for use, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)

        # Test write permissions
        test_file = os.path.join(temp_dir, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.unlink(test_file)
            logger.debug(f"Temporary directory ready: {temp_dir}")
            return True
        except Exception as e:
            logger.error(f"Cannot write to temporary directory {temp_dir}: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Cannot create temporary directory {temp_dir}: {str(e)}")
        return False


def get_directory_size_mb(directory: str) -> float:
    """
    Calculate total size of directory in MB.

    Args:
        directory: Directory path

    Returns:
        Total size in MB
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    # Skip files that can't be accessed
                    continue
    except Exception as e:
        logger.error(f"Error calculating directory size for {directory}: {str(e)}")
        return 0.0

    return total_size / (1024 * 1024)


def monitor_disk_usage(path: str, warning_threshold_percent: float = 90.0) -> dict:
    """
    Monitor disk usage and return usage statistics.

    Args:
        path: Path to check disk usage for
        warning_threshold_percent: Threshold for warning about low disk space

    Returns:
        Dictionary with disk usage statistics
    """
    try:
        statvfs = os.statvfs(path)

        total_bytes = statvfs.f_frsize * statvfs.f_blocks
        available_bytes = statvfs.f_frsize * statvfs.f_bavail
        used_bytes = total_bytes - available_bytes

        total_mb = total_bytes / (1024 * 1024)
        available_mb = available_bytes / (1024 * 1024)
        used_mb = used_bytes / (1024 * 1024)

        usage_percent = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0

        usage_stats = {
            "total_mb": total_mb,
            "used_mb": used_mb,
            "available_mb": available_mb,
            "usage_percent": usage_percent,
            "warning": usage_percent >= warning_threshold_percent,
        }

        if usage_stats["warning"]:
            logger.warning(
                f"Disk usage warning: {usage_percent:.1f}% used ({available_mb:.2f}MB available)"
            )
        else:
            logger.debug(f"Disk usage: {usage_percent:.1f}% used ({available_mb:.2f}MB available)")

        return usage_stats

    except Exception as e:
        logger.error(f"Error monitoring disk usage for {path}: {str(e)}")
        return {
            "total_mb": 0,
            "used_mb": 0,
            "available_mb": 0,
            "usage_percent": 0,
            "warning": True,  # Assume warning if we can't check
        }


def create_temp_file(
    suffix: str = ".mp4", prefix: str = "compressed_", temp_dir: Optional[str] = None
) -> str:
    """
    Create a temporary file for compression output with proper resource management.

    Args:
        suffix: File extension (default: '.mp4')
        prefix: File prefix (default: 'compressed_')
        temp_dir: Specific temporary directory to use (optional)

    Returns:
        Path to the created temporary file

    Raises:
        CompressionError: If temporary file cannot be created
    """
    try:
        # Use specified temp directory or system default
        if temp_dir:
            if not ensure_temp_directory(temp_dir):
                raise CompressionError(f"Cannot use temporary directory: {temp_dir}")
        else:
            temp_dir = tempfile.gettempdir()

        # Clean up old files in temp directory before creating new ones
        cleanup_temp_directory(temp_dir, max_age_hours=24)

        # Check disk space before creating temp file
        if not check_disk_space(temp_dir, 100):  # Require at least 100MB free
            raise InsufficientDiskSpaceError("Insufficient disk space for temporary file creation")

        # Create temp file and immediately close it to get just the path
        with tempfile.NamedTemporaryFile(
            suffix=suffix, prefix=prefix, dir=temp_dir, delete=False
        ) as f:
            temp_path = f.name

        logger.debug(f"Created temporary file: {temp_path}")
        return temp_path

    except (InsufficientDiskSpaceError, CompressionError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        error_msg = f"Failed to create temporary file: {str(e)}"
        logger.error(error_msg)
        raise CompressionError(error_msg)


def create_compression_result(
    success: bool,
    original_path: str,
    compressed_path: Optional[str] = None,
    processing_time: float = 0.0,
    error_message: Optional[str] = None,
) -> CompressionResult:
    """
    Create a CompressionResult object with calculated metrics.

    Args:
        success: Whether compression was successful
        original_path: Path to original video file
        compressed_path: Path to compressed video file (if successful)
        processing_time: Time taken for compression in seconds
        error_message: Error message if compression failed

    Returns:
        CompressionResult object with all metrics calculated
    """
    original_size_mb = get_file_size_mb(original_path)
    compressed_size_mb = None
    compression_ratio = None

    if success and compressed_path and os.path.exists(compressed_path):
        compressed_size_mb = get_file_size_mb(compressed_path)
        compression_ratio = calculate_compression_ratio(original_size_mb, compressed_size_mb)

    return CompressionResult(
        success=success,
        original_path=original_path,
        compressed_path=compressed_path,
        original_size_mb=original_size_mb,
        compressed_size_mb=compressed_size_mb,
        compression_ratio=compression_ratio,
        processing_time=processing_time,
        error_message=error_message,
    )


class CompressionContext:
    """Context manager for video compression operations with automatic cleanup."""

    def __init__(self, temp_files: list = None):
        """Initialize compression context."""
        self.temp_files = temp_files or []
        self.start_time = None

    def add_temp_file(self, file_path: str):
        """Add a temporary file to be cleaned up."""
        if file_path and file_path not in self.temp_files:
            self.temp_files.append(file_path)

    def __enter__(self):
        """Enter compression context."""
        import time

        self.start_time = time.time()
        logger.debug("Entered compression context")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit compression context and clean up resources."""
        import time

        # Clean up all temporary files
        if self.temp_files:
            logger.info(
                f"Cleaning up {len(self.temp_files)} temporary files from compression context"
            )
            cleanup_temp_files(*self.temp_files)

        # Log compression context duration
        if self.start_time:
            duration = time.time() - self.start_time
            logger.debug(f"Compression context duration: {duration:.2f}s")

        # Log any exceptions that occurred
        if exc_type:
            logger.error(
                f"Compression context exited with exception: {exc_type.__name__}: {exc_val}"
            )

        return False  # Don't suppress exceptions


class VideoCompressor:
    """Main video compression service with comprehensive resource management."""

    def __init__(self, config: dict):
        """Initialize the video compressor with configuration."""
        self.config = config
        self._setup_temp_directory()

    def _setup_temp_directory(self):
        """Set up and validate temporary directory."""
        temp_dir = self.config.get("temp_dir")
        if temp_dir:
            if not ensure_temp_directory(temp_dir):
                logger.warning(
                    f"Cannot use configured temp directory {temp_dir}, falling back to system default"
                )
                self.config["temp_dir"] = tempfile.gettempdir()
        else:
            self.config["temp_dir"] = tempfile.gettempdir()

        logger.info(f"Using temporary directory: {self.config['temp_dir']}")

    def get_compression_context(self) -> CompressionContext:
        """Get a new compression context for resource management."""
        return CompressionContext()

    async def compress_if_needed(
        self,
        video_path: str,
        max_size_mb: float = 50.0,
        user_id: Optional[int] = None,
        platform: Optional[str] = None,
    ) -> CompressionResult:
        """
        Compress video if it exceeds the specified size limit.

        This method implements the core decision logic for video compression:
        1. Check if file exists and FFmpeg is available
        2. Check disk space availability
        3. Check file size against limit
        4. Skip compression if file is already under limit
        5. Perform compression if file exceeds limit

        Args:
            video_path: Path to the input video file
            max_size_mb: Maximum allowed file size in MB (default: 50MB for Telegram)
            user_id: Optional user ID for monitoring
            platform: Optional platform name for monitoring

        Returns:
            CompressionResult with compression details
        """
        import time

        start_time = time.time()

        compression_logger.info(
            f"Starting compression check for: {video_path} (limit: {max_size_mb}MB)"
        )

        # Get initial file size for monitoring
        initial_file_size = get_file_size_mb(video_path) if os.path.exists(video_path) else 0.0

        # Monitor disk usage before starting
        disk_stats = monitor_disk_usage(self.config["temp_dir"])
        if disk_stats["warning"]:
            log_disk_space_warning(
                self.config["temp_dir"], disk_stats["usage_percent"], disk_stats["available_mb"]
            )

        # Use monitoring context for comprehensive logging
        with CompressionOperationLogger(
            user_id=user_id, original_size_mb=initial_file_size, platform=platform
        ) as monitor:

            # Set initial disk space
            monitor.set_disk_space(disk_stats["available_mb"], None)

            # Use compression context for automatic resource cleanup
            with self.get_compression_context() as ctx:
                try:
                    # Check if file exists
                    if not os.path.exists(video_path):
                        error_msg = f"Input video file not found: {video_path}"
                        logger.error(error_msg)
                        raise FileNotFoundError(error_msg)

                    # Check if FFmpeg is available
                    if not check_ffmpeg_availability():
                        error_msg = "FFmpeg is not available on the system"
                        compression_logger.error(error_msg)
                        raise FFmpegNotFoundError(error_msg)

                    # Check if compression is needed based on file size
                    needs_compression, file_size_mb = check_video_size_against_limit(
                        video_path, max_size_mb
                    )

                    if not needs_compression:
                        # File is already within limit, no compression needed
                        compression_logger.info(
                            f"Video {video_path} ({file_size_mb:.2f}MB) is already under {max_size_mb}MB limit - skipping compression"
                        )

                        # Set monitoring result for no compression needed
                        monitor.set_result(
                            success=True,
                            compressed_size_mb=file_size_mb,
                            compression_ratio=1.0,
                            compression_method="none",
                        )

                        return create_compression_result(
                            success=True,
                            original_path=video_path,
                            compressed_path=video_path,  # Same file, no compression performed
                            processing_time=time.time() - start_time,
                        )

                    # Check disk space before starting compression
                    # Estimate required space as 2x original file size for safety
                    required_space_mb = file_size_mb * 2

                    if not check_disk_space(self.config["temp_dir"], required_space_mb):
                        error_msg = f"Insufficient disk space for compression. Required: {required_space_mb:.2f}MB"
                        compression_logger.error(error_msg)
                        log_disk_space_warning(
                            self.config["temp_dir"],
                            disk_stats["usage_percent"],
                            disk_stats["available_mb"],
                        )
                        raise InsufficientDiskSpaceError(error_msg)

                    # File needs compression
                    compression_logger.info(
                        f"Video {video_path} ({file_size_mb:.2f}MB) exceeds {max_size_mb}MB limit - starting compression"
                    )

                    # Get video info for monitoring
                    try:
                        video_info = await get_video_info(video_path)
                        monitor.set_result(
                            success=False,  # Will be updated on success
                            video_duration=video_info.duration,
                            video_resolution=f"{video_info.width}x{video_info.height}",
                            compression_method="H.264",
                        )
                    except Exception as e:
                        compression_logger.warning(
                            f"Could not extract video info for monitoring: {e}"
                        )

                    temp_output = create_temp_file(temp_dir=self.config["temp_dir"])
                    ctx.add_temp_file(temp_output)  # Add to context for cleanup

                    # Use target size slightly below limit to ensure we stay under
                    target_size_mb = self.config.get("target_size_mb", max_size_mb * 0.9)

                    # Attempt compression with comprehensive error handling
                    compression_success = await self.compress_video(
                        video_path, temp_output, target_size_mb
                    )

                    if compression_success and validate_file_size(temp_output, max_size_mb):
                        compressed_size_mb = get_file_size_mb(temp_output)
                        compression_ratio = calculate_compression_ratio(
                            file_size_mb, compressed_size_mb
                        )

                        compression_logger.info(
                            f"Compression successful: {file_size_mb:.2f}MB -> {compressed_size_mb:.2f}MB"
                        )

                        # Update monitoring with success
                        final_disk_stats = monitor_disk_usage(self.config["temp_dir"])
                        monitor.set_result(
                            success=True,
                            compressed_size_mb=compressed_size_mb,
                            compression_ratio=compression_ratio,
                            compression_method="H.264",
                        )
                        monitor.set_disk_space(
                            disk_stats["available_mb"], final_disk_stats["available_mb"]
                        )

                        # Log performance metrics
                        log_performance_metrics(
                            "video_compression", time.time() - start_time, file_size_mb, True
                        )

                        # Remove from cleanup context since we're returning it
                        ctx.temp_files.remove(temp_output)

                        return create_compression_result(
                            success=True,
                            original_path=video_path,
                            compressed_path=temp_output,
                            processing_time=time.time() - start_time,
                        )
                    else:
                        error_msg = "Compression failed to achieve target size"
                        compression_logger.error(f"{error_msg} for {video_path}")
                        raise CompressionQualityError(error_msg)

                except (
                    FFmpegNotFoundError,
                    CompressionTimeoutError,
                    InsufficientDiskSpaceError,
                    UnsupportedFormatError,
                    VideoCorruptedError,
                    CompressionQualityError,
                ) as e:
                    # Handle known compression errors
                    compression_logger.error(f"Compression error for {video_path}: {str(e)}")

                    # Log specific error types
                    if isinstance(e, CompressionTimeoutError):
                        log_compression_timeout(video_path, self.config.get("timeout_seconds", 300))
                    elif isinstance(e, FFmpegNotFoundError):
                        log_ffmpeg_error(video_path, str(e))

                    # Log performance metrics for failed operation
                    log_performance_metrics(
                        "video_compression", time.time() - start_time, initial_file_size, False
                    )

                    return create_compression_result(
                        success=False,
                        original_path=video_path,
                        processing_time=time.time() - start_time,
                        error_message=get_compression_error_message(e),
                    )
                except FileNotFoundError as e:
                    compression_logger.error(f"File not found error for {video_path}: {str(e)}")

                    # Log performance metrics for failed operation
                    log_performance_metrics(
                        "video_compression", time.time() - start_time, initial_file_size, False
                    )

                    return create_compression_result(
                        success=False,
                        original_path=video_path,
                        processing_time=time.time() - start_time,
                        error_message=get_compression_error_message(e),
                    )
                except Exception as e:
                    # Handle unexpected errors
                    compression_logger.error(
                        f"Unexpected error in compress_if_needed for {video_path}: {str(e)}",
                        exc_info=True,
                    )

                    # Log performance metrics for failed operation
                    log_performance_metrics(
                        "video_compression", time.time() - start_time, initial_file_size, False
                    )

                    return create_compression_result(
                        success=False,
                        original_path=video_path,
                        processing_time=time.time() - start_time,
                        error_message=f"Unexpected compression error: {str(e)}",
                    )

    async def get_video_info(self, video_path: str) -> VideoInfo:
        """
        Extract video metadata using FFmpeg.

        Args:
            video_path: Path to the video file

        Returns:
            VideoInfo object with video metadata
        """
        return await get_video_info(video_path)

    async def compress_video(
        self,
        input_path: str,
        output_path: str,
        target_size_mb: float,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """
        Compress video to target size using progressive compression strategy.

        Progressive strategy:
        1. Try multiple CRF quality levels (28, 32, 36)
        2. If quality levels fail, try resolution downscaling
        3. Combine quality reduction with resolution reduction for very large videos

        Args:
            input_path: Path to input video
            output_path: Path for compressed output
            target_size_mb: Target file size in MB
            progress_callback: Optional callback for progress updates (0.0 to 1.0)

        Returns:
            True if compression successful, False otherwise

        Raises:
            FileNotFoundError: If input file doesn't exist
            FFmpegNotFoundError: If FFmpeg is not available
            VideoCorruptedError: If video file is corrupted
            UnsupportedFormatError: If video format is not supported
            CompressionTimeoutError: If compression times out
        """
        logger.info(
            f"Starting video compression: {input_path} -> {output_path} (target: {target_size_mb}MB)"
        )

        if not os.path.exists(input_path):
            error_msg = f"Input video file not found: {input_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not check_ffmpeg_availability():
            error_msg = "FFmpeg is not available on the system"
            logger.error(error_msg)
            raise FFmpegNotFoundError(error_msg)

        try:
            # Get video info first with error handling
            video_info = await self.get_video_info(input_path)
            logger.info(
                f"Video info: {video_info.width}x{video_info.height}, {video_info.duration:.1f}s, {video_info.size_mb:.2f}MB"
            )

            # If video is already smaller than target, just copy it
            if video_info.size_mb <= target_size_mb:
                logger.info(
                    f"Video already under target size ({video_info.size_mb}MB <= {target_size_mb}MB)"
                )
                if input_path != output_path:
                    try:
                        shutil.copy2(input_path, output_path)
                        logger.info(f"Copied video file to output path: {output_path}")
                    except Exception as e:
                        logger.error(f"Failed to copy video file: {str(e)}")
                        raise CompressionError(f"Failed to copy video file: {str(e)}")
                return True

            # Progressive compression strategy with comprehensive error handling
            success = await self._progressive_compression_strategy(
                input_path, output_path, target_size_mb, video_info, progress_callback
            )

            if success:
                logger.info(f"Video compression completed successfully: {output_path}")
            else:
                logger.error(f"Video compression failed for: {input_path}")

            return success

        except (
            FFmpegNotFoundError,
            VideoCorruptedError,
            UnsupportedFormatError,
            CompressionTimeoutError,
        ):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error during video compression: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CompressionError(error_msg)

    async def _progressive_compression_strategy(
        self,
        input_path: str,
        output_path: str,
        target_size_mb: float,
        video_info: VideoInfo,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """
        Implement progressive compression strategy with multiple fallback levels.

        Strategy:
        1. Try CRF quality levels (28, 32, 36) at original resolution
        2. If still too large, try resolution downscaling with quality levels
        3. Final attempt with aggressive downscaling

        Args:
            input_path: Path to input video
            output_path: Path for compressed output
            target_size_mb: Target file size in MB
            video_info: Video metadata
            progress_callback: Optional progress callback

        Returns:
            True if any compression attempt succeeds, False otherwise

        Raises:
            CompressionTimeoutError: If all attempts timeout
            CompressionQualityError: If compression would result in unacceptable quality
        """
        quality_levels = self.config.get("quality_levels", [28, 32, 36])
        max_resolution = self.config.get("max_resolution", (1280, 720))
        timeout_seconds = self.config.get("timeout_seconds", 300)

        logger.info(f"Starting progressive compression strategy for {input_path}")
        logger.info(f"Target size: {target_size_mb}MB, Original size: {video_info.size_mb:.2f}MB")

        # Define resolution levels for progressive downscaling
        resolution_levels = [
            (video_info.width, video_info.height),  # Original resolution
            max_resolution,  # Config max resolution (1280x720)
            (854, 480),  # 480p
            (640, 360),  # 360p (aggressive fallback)
        ]

        # Filter out resolution levels that are larger than original
        valid_resolution_levels = []
        for max_width, max_height in resolution_levels:
            if max_width <= video_info.width or max_height <= video_info.height:
                valid_resolution_levels.append((max_width, max_height))

        if not valid_resolution_levels:
            valid_resolution_levels = [(video_info.width, video_info.height)]

        total_attempts = len(quality_levels) * len(valid_resolution_levels)
        current_attempt = 0
        last_error = None
        timeout_count = 0

        logger.info(
            f"Will try {total_attempts} compression attempts across {len(valid_resolution_levels)} resolution levels"
        )

        # Try each resolution level with each quality level
        for res_idx, (max_width, max_height) in enumerate(valid_resolution_levels):
            logger.info(
                f"Trying resolution level {res_idx + 1}/{len(valid_resolution_levels)}: {max_width}x{max_height}"
            )

            for quality_idx, crf in enumerate(quality_levels):
                current_attempt += 1
                logger.info(
                    f"Compression attempt {current_attempt}/{total_attempts}: CRF {crf} at max {max_width}x{max_height}"
                )

                if progress_callback:
                    try:
                        progress_callback(current_attempt / total_attempts)
                    except Exception as callback_error:
                        logger.warning(f"Progress callback error: {str(callback_error)}")

                # Calculate output dimensions maintaining aspect ratio
                output_width, output_height = self._calculate_output_dimensions(
                    video_info.width, video_info.height, max_width, max_height
                )

                # Check if this would result in unacceptably small resolution
                min_acceptable_pixels = 320 * 240  # Minimum acceptable resolution
                if output_width * output_height < min_acceptable_pixels:
                    logger.warning(
                        f"Skipping attempt with too small resolution: {output_width}x{output_height}"
                    )
                    continue

                try:
                    success = await self._attempt_compression(
                        input_path, output_path, crf, output_width, output_height, timeout_seconds
                    )

                    if success:
                        # Check if output meets size requirement
                        output_size_mb = get_file_size_mb(output_path)
                        logger.info(f"Compressed video size: {output_size_mb:.2f}MB")

                        if output_size_mb <= target_size_mb:
                            if progress_callback:
                                try:
                                    progress_callback(1.0)
                                except Exception:
                                    pass

                            compression_ratio = output_size_mb / video_info.size_mb
                            logger.info(
                                f"Progressive compression successful: {video_info.size_mb:.2f}MB -> {output_size_mb:.2f}MB (ratio: {compression_ratio:.2f})"
                            )
                            logger.info(
                                f"Final settings: CRF {crf}, resolution {output_width}x{output_height}"
                            )
                            return True
                        else:
                            logger.info(
                                f"Attempt {current_attempt} still too large: {output_size_mb:.2f}MB > {target_size_mb}MB"
                            )
                            # Clean up the oversized output file
                            try:
                                cleanup_temp_files(output_path)
                            except Exception as cleanup_error:
                                logger.warning(
                                    f"Failed to cleanup oversized output file: {cleanup_error}"
                                )

                except CompressionTimeoutError as e:
                    timeout_count += 1
                    last_error = e
                    logger.error(f"Timeout during compression attempt {current_attempt}: {str(e)}")

                    # If we've had too many timeouts, give up
                    if timeout_count >= 3:
                        logger.error("Too many compression timeouts, aborting progressive strategy")
                        raise CompressionTimeoutError("Multiple compression attempts timed out")

                    continue

                except (FileNotFoundError, UnsupportedFormatError, CompressionError) as e:
                    last_error = e
                    logger.error(f"Error during compression attempt {current_attempt}: {str(e)}")
                    continue

                except Exception as e:
                    last_error = e
                    logger.error(
                        f"Unexpected error during compression attempt {current_attempt}: {str(e)}",
                        exc_info=True,
                    )
                    continue

        # If all progressive attempts failed
        logger.error(
            f"All {total_attempts} progressive compression attempts failed for {input_path}"
        )

        # Determine the most appropriate error to raise
        if timeout_count > 0:
            raise CompressionTimeoutError("All compression attempts timed out")
        elif last_error:
            # Re-raise the last error we encountered
            raise last_error
        else:
            raise CompressionQualityError(
                "Unable to compress video to target size with acceptable quality"
            )

    def _calculate_output_dimensions(
        self, original_width: int, original_height: int, max_width: int, max_height: int
    ) -> tuple[int, int]:
        """
        Calculate output dimensions maintaining aspect ratio within max constraints.

        Args:
            original_width: Original video width
            original_height: Original video height
            max_width: Maximum allowed width
            max_height: Maximum allowed height

        Returns:
            Tuple of (output_width, output_height)
        """
        # Don't upscale - use original dimensions if they're smaller
        output_width = min(original_width, max_width)
        output_height = min(original_height, max_height)

        # Maintain aspect ratio
        aspect_ratio = original_width / original_height

        # Check if we need to adjust to maintain aspect ratio
        if output_width / output_height > aspect_ratio:
            # Width is too large relative to height
            output_width = int(output_height * aspect_ratio)
        else:
            # Height is too large relative to width
            output_height = int(output_width / aspect_ratio)

        # Ensure dimensions are even (required for some codecs)
        output_width = output_width - (output_width % 2)
        output_height = output_height - (output_height % 2)

        # Ensure minimum dimensions
        output_width = max(output_width, 320)
        output_height = max(output_height, 240)

        return output_width, output_height

    async def _attempt_compression(
        self,
        input_path: str,
        output_path: str,
        crf: int,
        output_width: int,
        output_height: int,
        timeout_seconds: int,
    ) -> bool:
        """
        Attempt a single compression with specified parameters.

        Args:
            input_path: Input video path
            output_path: Output video path
            crf: CRF quality value
            output_width: Target width
            output_height: Target height
            timeout_seconds: Compression timeout

        Returns:
            True if compression completed successfully, False otherwise

        Raises:
            CompressionTimeoutError: If compression times out
            FFmpegNotFoundError: If FFmpeg execution fails
            CompressionError: For other compression errors
        """
        logger.info(
            f"Attempting compression: CRF {crf}, {output_width}x{output_height}, timeout {timeout_seconds}s"
        )

        process = None
        try:
            # Build FFmpeg command with error handling
            try:
                stream = ffmpeg.input(input_path)

                # Apply video filters
                stream = ffmpeg.filter(stream, "scale", output_width, output_height)

                # Output with compression settings
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    vcodec="libx264",
                    crf=crf,
                    preset="medium",
                    acodec="aac",
                    audio_bitrate="128k",
                    format="mp4",
                    loglevel="error",  # Reduce FFmpeg output verbosity
                )

                # Compile FFmpeg command
                cmd = ffmpeg.compile(stream, overwrite_output=True)
                logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            except Exception as e:
                error_msg = f"Failed to build FFmpeg command: {str(e)}"
                logger.error(error_msg)
                raise CompressionError(error_msg)

            # Run compression with timeout and process monitoring
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                logger.info(f"Started FFmpeg process (PID: {process.pid})")

                # Wait for process completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )

                # Check process return code
                if process.returncode != 0:
                    stderr_text = stderr.decode() if stderr else "No error output"
                    logger.error(
                        f"FFmpeg compression failed (return code {process.returncode}): {stderr_text}"
                    )

                    # Check for specific FFmpeg errors
                    stderr_lower = stderr_text.lower()
                    if "no such file or directory" in stderr_lower:
                        raise FileNotFoundError("Input file not found during compression")
                    elif any(
                        error in stderr_lower
                        for error in [
                            "invalid argument",
                            "unknown encoder",
                            "invalid data",
                            "moov atom not found",
                        ]
                    ):
                        raise UnsupportedFormatError("Unsupported video format or codec")
                    elif "permission denied" in stderr_lower:
                        raise CompressionError("Permission denied accessing video file")
                    elif "disk full" in stderr_lower or "no space left" in stderr_lower:
                        raise InsufficientDiskSpaceError(
                            "Insufficient disk space during compression"
                        )
                    elif "killed" in stderr_lower or "terminated" in stderr_lower:
                        raise CompressionTimeoutError("Compression was terminated")
                    else:
                        raise CompressionError(f"FFmpeg error: {stderr_text}")

                # Check if output file was created and has reasonable size
                if not os.path.exists(output_path):
                    error_msg = f"Output file was not created: {output_path}"
                    logger.error(error_msg)
                    raise CompressionError(error_msg)

                output_size = os.path.getsize(output_path)
                if output_size == 0:
                    error_msg = f"Output file is empty: {output_path}"
                    logger.error(error_msg)
                    raise CompressionError(error_msg)

                output_size_mb = output_size / (1024 * 1024)
                logger.info(f"Compression attempt successful: output size {output_size_mb:.2f}MB")
                return True

            except asyncio.TimeoutError:
                error_msg = f"Compression timeout after {timeout_seconds} seconds"
                logger.error(error_msg)

                # Kill the process if it's still running
                if process and process.returncode is None:
                    try:
                        logger.info(f"Killing FFmpeg process (PID: {process.pid})")
                        process.kill()
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except Exception as kill_error:
                        logger.error(f"Error killing FFmpeg process: {str(kill_error)}")

                raise CompressionTimeoutError(error_msg)

        except (
            CompressionTimeoutError,
            FileNotFoundError,
            UnsupportedFormatError,
            CompressionError,
        ):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error during compression attempt: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Clean up process if needed
            if process and process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass

            raise CompressionError(error_msg)

    async def estimate_compression_time(self, video_path: str) -> int:
        """
        Estimate compression time based on video properties.

        Args:
            video_path: Path to the video file

        Returns:
            Estimated compression time in seconds

        Raises:
            FileNotFoundError: If video file doesn't exist
            VideoCorruptedError: If video file is corrupted
        """
        logger.info(f"Estimating compression time for: {video_path}")

        try:
            video_info = await self.get_video_info(video_path)

            # Base estimation: ~1 second per MB for medium preset
            base_time = video_info.size_mb * 1.0

            # Adjust for resolution (higher resolution takes longer)
            resolution_factor = 1.0
            total_pixels = video_info.width * video_info.height
            if total_pixels > 3840 * 2160:  # 4K+
                resolution_factor = 3.0
            elif total_pixels > 1920 * 1080:  # 1080p+
                resolution_factor = 2.0
            elif total_pixels > 1280 * 720:  # 720p+
                resolution_factor = 1.5

            # Adjust for duration (longer videos take proportionally longer)
            duration_factor = max(1.0, video_info.duration / 60.0)  # Minutes

            # Adjust for codec complexity
            codec_factor = 1.0
            if video_info.codec in ["hevc", "h265", "av1"]:
                codec_factor = 1.8  # More complex codecs take longer to decode
            elif video_info.codec in ["vp9", "vp8"]:
                codec_factor = 1.3

            # Adjust for frame rate (higher FPS takes longer)
            fps_factor = 1.0
            if video_info.fps > 60:
                fps_factor = 1.5
            elif video_info.fps > 30:
                fps_factor = 1.2

            estimated_time = (
                base_time * resolution_factor * duration_factor * codec_factor * fps_factor
            )

            # Add some buffer and ensure minimum/maximum bounds
            estimated_time = max(10, min(600, int(estimated_time * 1.3)))  # 10s to 10min range

            logger.info(
                f"Compression time estimation: {estimated_time}s (base: {base_time:.1f}s, "
                f"resolution: {resolution_factor}x, duration: {duration_factor:.1f}x, "
                f"codec: {codec_factor}x, fps: {fps_factor}x)"
            )

            return estimated_time

        except (
            FileNotFoundError,
            VideoCorruptedError,
            UnsupportedFormatError,
            FFmpegNotFoundError,
        ):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error estimating compression time: {str(e)}", exc_info=True)
            # Return a reasonable default instead of failing
            return 120  # Default to 2 minutes if estimation fails
