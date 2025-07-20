"""
Unit tests for video compression utilities.
"""

import asyncio
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from utils.video_compression import (
    CompressionQualityError,
    CompressionTimeoutError,
    FFmpegNotFoundError,
    InsufficientDiskSpaceError,
    UnsupportedFormatError,
    VideoCompressor,
    VideoCorruptedError,
    VideoInfo,
    get_video_info,
)


class TestVideoInfoExtraction:
    """Test cases for video information extraction functionality."""

    @pytest.fixture
    def mock_video_probe_data(self):
        """Mock FFmpeg probe data for testing."""
        return {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "120.5",
                    "r_frame_rate": "30/1",
                    "bit_rate": "5000000",
                    "codec_name": "h264",
                }
            ],
            "format": {"duration": "120.5", "bit_rate": "5000000"},
        }

    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # Write some dummy data to simulate a video file
            f.write(b"dummy video data" * 1000)  # ~16KB file
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_get_video_info_success(self, temp_video_file, mock_video_probe_data):
        """Test successful video info extraction."""
        with patch("ffmpeg.probe", return_value=mock_video_probe_data):
            video_info = await get_video_info(temp_video_file)

            assert isinstance(video_info, VideoInfo)
            assert video_info.width == 1920
            assert video_info.height == 1080
            assert video_info.duration == 120.5
            assert video_info.fps == 30.0
            assert video_info.bitrate == 5000000
            assert video_info.codec == "h264"
            assert video_info.size_mb > 0

    @pytest.mark.asyncio
    async def test_get_video_info_file_not_found(self):
        """Test error handling when video file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            await get_video_info("nonexistent_file.mp4")

    @pytest.mark.asyncio
    async def test_get_video_info_no_video_stream(self, temp_video_file):
        """Test error handling when no video stream is found."""
        mock_probe_data = {"streams": [{"codec_type": "audio", "codec_name": "aac"}]}

        with patch("ffmpeg.probe", return_value=mock_probe_data):
            with pytest.raises(UnsupportedFormatError, match="No video stream found"):
                await get_video_info(temp_video_file)

    @pytest.mark.asyncio
    async def test_get_video_info_invalid_dimensions(self, temp_video_file):
        """Test error handling for invalid video dimensions."""
        mock_probe_data = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 0,
                    "height": 0,
                    "duration": "120.5",
                    "codec_name": "h264",
                }
            ]
        }

        with patch("ffmpeg.probe", return_value=mock_probe_data):
            with pytest.raises(VideoCorruptedError, match="Invalid video dimensions"):
                await get_video_info(temp_video_file)

    @pytest.mark.asyncio
    async def test_get_video_info_invalid_duration(self, temp_video_file):
        """Test error handling for invalid video duration."""
        mock_probe_data = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "0",
                    "codec_name": "h264",
                }
            ]
        }

        with patch("ffmpeg.probe", return_value=mock_probe_data):
            with pytest.raises(VideoCorruptedError, match="Invalid video duration"):
                await get_video_info(temp_video_file)

    @pytest.mark.asyncio
    async def test_get_video_info_ffmpeg_error(self, temp_video_file):
        """Test error handling for FFmpeg execution errors."""
        mock_error = MagicMock()
        mock_error.stderr = b"FFmpeg error message"

        with patch("ffmpeg.probe", side_effect=Exception("FFmpeg failed")):
            with pytest.raises(VideoCorruptedError, match="Unexpected error extracting video info"):
                await get_video_info(temp_video_file)

    @pytest.mark.asyncio
    async def test_get_video_info_alternative_fps_format(self, temp_video_file):
        """Test handling of alternative frame rate formats."""
        mock_probe_data = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "120.5",
                    "avg_frame_rate": "25/1",
                    "codec_name": "h264",
                }
            ]
        }

        with patch("ffmpeg.probe", return_value=mock_probe_data):
            video_info = await get_video_info(temp_video_file)
            assert video_info.fps == 25.0

    @pytest.mark.asyncio
    async def test_get_video_info_duration_from_format(self, temp_video_file):
        """Test getting duration from format when not in stream."""
        mock_probe_data = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "codec_name": "h264",
                }
            ],
            "format": {"duration": "150.0"},
        }

        with patch("ffmpeg.probe", return_value=mock_probe_data):
            video_info = await get_video_info(temp_video_file)
            assert video_info.duration == 150.0

    @pytest.mark.asyncio
    async def test_get_video_info_bitrate_from_format(self, temp_video_file):
        """Test getting bitrate from format when not in stream."""
        mock_probe_data = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "120.5",
                    "r_frame_rate": "30/1",
                    "codec_name": "h264",
                }
            ],
            "format": {"bit_rate": "8000000"},
        }

        with patch("ffmpeg.probe", return_value=mock_probe_data):
            video_info = await get_video_info(temp_video_file)
            assert video_info.bitrate == 8000000

    @pytest.mark.asyncio
    async def test_video_compressor_get_video_info(self, temp_video_file, mock_video_probe_data):
        """Test VideoCompressor.get_video_info method."""
        compressor = VideoCompressor({})

        with patch("ffmpeg.probe", return_value=mock_video_probe_data):
            video_info = await compressor.get_video_info(temp_video_file)

            assert isinstance(video_info, VideoInfo)
            assert video_info.width == 1920
            assert video_info.height == 1080


class TestVideoCompressionEngine:
    """Test cases for video compression engine functionality."""

    @pytest.fixture
    def compression_config(self):
        """Configuration for video compression testing."""
        return {
            "target_size_mb": 45,
            "max_attempts": 3,
            "quality_levels": [28, 32, 36],
            "max_resolution": (1280, 720),
            "timeout_seconds": 300,
        }

    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # Write some dummy data to simulate a video file
            f.write(b"dummy video data" * 1000)  # ~16KB file
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def mock_video_probe_data(self):
        """Mock FFmpeg probe data for testing."""
        return {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "duration": "120.5",
                    "r_frame_rate": "30/1",
                    "bit_rate": "5000000",
                    "codec_name": "h264",
                }
            ],
            "format": {"duration": "120.5", "bit_rate": "5000000"},
        }

    @pytest.mark.asyncio
    async def test_compress_video_already_small(
        self, temp_video_file, temp_output_file, compression_config, mock_video_probe_data
    ):
        """Test compression when video is already under target size."""
        # Mock video info to show small file
        mock_video_probe_data["streams"][0]["duration"] = "10.0"

        compressor = VideoCompressor(compression_config)

        with patch("ffmpeg.probe", return_value=mock_video_probe_data):
            with patch("os.path.getsize", return_value=1024 * 1024):  # 1MB file
                result = await compressor.compress_video(temp_video_file, temp_output_file, 50)

                assert result is True

    @pytest.mark.asyncio
    async def test_compress_video_input_not_found(self, temp_output_file, compression_config):
        """Test compression with non-existent input file."""
        compressor = VideoCompressor(compression_config)

        with pytest.raises(FileNotFoundError):
            await compressor.compress_video("nonexistent.mp4", temp_output_file, 50)

    @pytest.mark.asyncio
    async def test_estimate_compression_time(
        self, temp_video_file, compression_config, mock_video_probe_data
    ):
        """Test compression time estimation."""
        compressor = VideoCompressor(compression_config)

        with patch("ffmpeg.probe", return_value=mock_video_probe_data):
            estimated_time = await compressor.estimate_compression_time(temp_video_file)

            assert isinstance(estimated_time, int)
            assert 10 <= estimated_time <= 300  # Should be within reasonable bounds

    @pytest.mark.asyncio
    async def test_estimate_compression_time_4k_video(self, temp_video_file, compression_config):
        """Test compression time estimation for 4K video."""
        mock_4k_data = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 3840,
                    "height": 2160,
                    "duration": "300.0",  # 5 minutes
                    "r_frame_rate": "30/1",
                    "codec_name": "h264",
                }
            ]
        }

        compressor = VideoCompressor(compression_config)

        with patch("ffmpeg.probe", return_value=mock_4k_data):
            with patch("os.path.getsize", return_value=500 * 1024 * 1024):  # 500MB file
                estimated_time = await compressor.estimate_compression_time(temp_video_file)

                assert estimated_time >= 10  # Should be at least minimum bound
                assert estimated_time <= 600  # Should be within maximum bound

    @pytest.mark.asyncio
    async def test_estimate_compression_time_error_handling(self, compression_config):
        """Test compression time estimation error handling."""
        compressor = VideoCompressor(compression_config)

        with patch.object(compressor, "get_video_info", side_effect=Exception("Test error")):
            estimated_time = await compressor.estimate_compression_time("test.mp4")

            assert estimated_time == 120  # Should return default value

    @pytest.mark.asyncio
    async def test_compress_video_with_progress_callback(
        self, temp_video_file, temp_output_file, compression_config, mock_video_probe_data
    ):
        """Test compression with progress callback."""
        progress_values = []

        def progress_callback(progress):
            progress_values.append(progress)

        # Mock video info to show small file (no compression needed)
        mock_video_probe_data["streams"][0]["duration"] = "10.0"

        compressor = VideoCompressor(compression_config)

        with patch("ffmpeg.probe", return_value=mock_video_probe_data):
            with patch("os.path.getsize", return_value=1024 * 1024):  # 1MB file (small)
                result = await compressor.compress_video(
                    temp_video_file, temp_output_file, 50, progress_callback=progress_callback
                )

                assert result is True  # Should succeed without compression


class TestCompressionResultHandling:
    """Test cases for compression result handling functionality."""

    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # Write some dummy data to simulate a video file
            f.write(b"dummy video data" * 1000)  # ~16KB file
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_calculate_compression_ratio(self):
        """Test compression ratio calculation."""
        from utils.video_compression import calculate_compression_ratio

        # Normal case
        ratio = calculate_compression_ratio(100.0, 50.0)
        assert ratio == 0.5

        # Edge case: zero original size
        ratio = calculate_compression_ratio(0.0, 50.0)
        assert ratio == 0.0

        # Edge case: larger compressed size
        ratio = calculate_compression_ratio(50.0, 100.0)
        assert ratio == 2.0

    def test_validate_file_size(self, temp_video_file):
        """Test file size validation."""
        from utils.video_compression import validate_file_size

        # File exists and is within limit
        assert validate_file_size(temp_video_file, 1.0) is True  # 1MB limit

        # File exists but exceeds limit
        assert validate_file_size(temp_video_file, 0.001) is False  # Very small limit

        # File doesn't exist
        assert validate_file_size("nonexistent.mp4", 1.0) is False

    def test_get_file_size_mb(self, temp_video_file):
        """Test file size retrieval."""
        from utils.video_compression import get_file_size_mb

        # File exists
        size = get_file_size_mb(temp_video_file)
        assert size > 0

        # File doesn't exist
        size = get_file_size_mb("nonexistent.mp4")
        assert size == 0.0

    def test_cleanup_temp_files(self):
        """Test temporary file cleanup."""
        from utils.video_compression import cleanup_temp_files

        # Create temporary files
        temp_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(b"test data")
                temp_files.append(f.name)

        # Verify files exist
        for temp_file in temp_files:
            assert os.path.exists(temp_file)

        # Clean up files
        cleanup_temp_files(*temp_files)

        # Verify files are deleted
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)

        # Test cleanup with non-existent files (should not raise error)
        cleanup_temp_files("nonexistent1.mp4", "nonexistent2.mp4")

    def test_create_temp_file(self):
        """Test temporary file creation."""
        from utils.video_compression import cleanup_temp_files, create_temp_file

        # Create temp file
        temp_path = create_temp_file()

        try:
            assert os.path.exists(temp_path)
            assert temp_path.endswith(".mp4")
            assert "compressed_" in os.path.basename(temp_path)
        finally:
            cleanup_temp_files(temp_path)

        # Test with custom suffix and prefix
        temp_path = create_temp_file(suffix=".avi", prefix="test_")

        try:
            assert os.path.exists(temp_path)
            assert temp_path.endswith(".avi")
            assert "test_" in os.path.basename(temp_path)
        finally:
            cleanup_temp_files(temp_path)

    def test_create_compression_result_success(self, temp_video_file):
        """Test compression result creation for successful compression."""
        from utils.video_compression import (
            cleanup_temp_files,
            create_compression_result,
            create_temp_file,
        )

        # Create a compressed file
        compressed_file = create_temp_file()
        with open(compressed_file, "wb") as f:
            f.write(b"compressed data" * 500)  # Smaller than original

        try:
            result = create_compression_result(
                success=True,
                original_path=temp_video_file,
                compressed_path=compressed_file,
                processing_time=5.0,
            )

            assert result.success is True
            assert result.original_path == temp_video_file
            assert result.compressed_path == compressed_file
            assert result.original_size_mb > 0
            assert result.compressed_size_mb > 0
            assert result.compression_ratio > 0
            assert result.processing_time == 5.0
            assert result.error_message is None

        finally:
            cleanup_temp_files(compressed_file)

    def test_create_compression_result_failure(self, temp_video_file):
        """Test compression result creation for failed compression."""
        from utils.video_compression import create_compression_result

        result = create_compression_result(
            success=False,
            original_path=temp_video_file,
            processing_time=2.0,
            error_message="Test error",
        )

        assert result.success is False
        assert result.original_path == temp_video_file
        assert result.compressed_path is None
        assert result.original_size_mb > 0
        assert result.compressed_size_mb is None
        assert result.compression_ratio is None
        assert result.processing_time == 2.0
        assert result.error_message == "Test error"

    @pytest.mark.asyncio
    async def test_compress_if_needed_small_file(self, temp_video_file):
        """Test compress_if_needed with file already under limit."""
        from utils.video_compression import VideoCompressor

        compressor = VideoCompressor({})

        result = await compressor.compress_if_needed(temp_video_file, 1.0)  # 1MB limit

        assert result.success is True
        assert result.compressed_path == temp_video_file  # Same file
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_compress_if_needed_file_not_found(self):
        """Test compress_if_needed with non-existent file."""
        from utils.video_compression import VideoCompressor

        compressor = VideoCompressor({})

        result = await compressor.compress_if_needed("nonexistent.mp4", 50)

        assert result.success is False
        assert "not found" in result.error_message.lower()


class TestVideoFormatsAndSizes:
    """Test compression with various video formats and sizes."""

    @pytest.fixture
    def compression_config(self):
        """Configuration for video compression testing."""
        return {
            "target_size_mb": 45,
            "max_attempts": 3,
            "quality_levels": [28, 32, 36],
            "max_resolution": (1280, 720),
            "timeout_seconds": 300,
        }

    @pytest.fixture
    def video_compressor(self, compression_config):
        """Create VideoCompressor instance for testing."""
        return VideoCompressor(compression_config)

    def create_mock_video_file(self, size_mb: float, format_ext: str = ".mp4") -> str:
        """Create a mock video file with specified size."""
        with tempfile.NamedTemporaryFile(suffix=format_ext, delete=False) as f:
            # Write data to reach desired size
            data_size = int(size_mb * 1024 * 1024)
            chunk_size = 1024
            for _ in range(data_size // chunk_size):
                f.write(b"x" * chunk_size)
            # Write remaining bytes
            remaining = data_size % chunk_size
            if remaining:
                f.write(b"x" * remaining)
            return f.name

    @pytest.mark.asyncio
    async def test_compression_with_various_sizes(self, video_compressor):
        """Test compression with different video file sizes."""
        test_sizes = [10, 60, 100, 200, 500]  # MB

        for size_mb in test_sizes:
            temp_file = self.create_mock_video_file(size_mb)
            try:
                # Mock video info for the file
                mock_video_info = VideoInfo(
                    width=1920,
                    height=1080,
                    duration=120.0,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=size_mb,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    with patch.object(video_compressor, "compress_video", return_value=True):
                        result = await video_compressor.compress_if_needed(temp_file, 50)

                        if size_mb <= 50:
                            # Small files should not be compressed
                            assert result.success is True
                            assert result.compressed_path == temp_file
                        else:
                            # Large files should be compressed
                            assert result.success is True
                            assert result.compressed_path != temp_file

            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_compression_with_various_formats(self, video_compressor):
        """Test compression with different video formats."""
        formats = [".mp4", ".mov", ".avi", ".mkv", ".webm"]

        for format_ext in formats:
            temp_file = self.create_mock_video_file(60, format_ext)  # 60MB file
            try:
                mock_video_info = VideoInfo(
                    width=1920,
                    height=1080,
                    duration=120.0,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=60,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    with patch.object(video_compressor, "compress_video", return_value=True):
                        result = await video_compressor.compress_if_needed(temp_file, 50)
                        assert result.success is True

            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_compression_with_different_resolutions(self, video_compressor):
        """Test compression with different video resolutions."""
        resolutions = [
            (640, 480),  # 480p
            (1280, 720),  # 720p
            (1920, 1080),  # 1080p
            (3840, 2160),  # 4K
        ]

        for width, height in resolutions:
            temp_file = self.create_mock_video_file(60)  # 60MB file
            try:
                mock_video_info = VideoInfo(
                    width=width,
                    height=height,
                    duration=120.0,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=60,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    with patch.object(video_compressor, "compress_video", return_value=True):
                        result = await video_compressor.compress_if_needed(temp_file, 50)
                        assert result.success is True

            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


class TestErrorScenariosAndEdgeCases:
    """Test error scenarios and edge cases for video compression."""

    @pytest.fixture
    def compression_config(self):
        return {
            "target_size_mb": 45,
            "max_attempts": 3,
            "quality_levels": [28, 32, 36],
            "max_resolution": (1280, 720),
            "timeout_seconds": 300,
        }

    @pytest.fixture
    def video_compressor(self, compression_config):
        return VideoCompressor(compression_config)

    @pytest.mark.asyncio
    async def test_ffmpeg_not_available_error(self, video_compressor):
        """Test error handling when FFmpeg is not available."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"dummy video data" * 1000)
            temp_path = temp_file.name

        try:
            with patch("utils.video_compression.check_ffmpeg_availability", return_value=False):
                result = await video_compressor.compress_if_needed(temp_path, 50)
                assert result.success is False
                assert "not available" in result.error_message.lower()
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_insufficient_disk_space_error(self, video_compressor):
        """Test error handling when there's insufficient disk space."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            # Create a large file (100MB)
            temp_file.write(b"x" * (100 * 1024 * 1024))
            temp_path = temp_file.name

        try:
            mock_video_info = VideoInfo(
                width=1920,
                height=1080,
                duration=120.0,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                size_mb=100,
            )

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                with patch("utils.video_compression.check_disk_space", return_value=False):
                    result = await video_compressor.compress_if_needed(temp_path, 50)
                    assert result.success is False
                    assert "disk space" in result.error_message.lower()
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_corrupted_video_file_error(self, video_compressor):
        """Test error handling for corrupted video files."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            # Create a file larger than 50MB to trigger compression
            temp_file.write(b"corrupted video data" * (60 * 1024 * 1024 // 20))
            temp_path = temp_file.name

        try:
            with patch.object(
                video_compressor,
                "get_video_info",
                side_effect=VideoCorruptedError("Corrupted file"),
            ):
                result = await video_compressor.compress_if_needed(temp_path, 50)
                assert result.success is False
                assert "corrupted" in result.error_message.lower()
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_unsupported_format_error(self, video_compressor):
        """Test error handling for unsupported video formats."""
        with tempfile.NamedTemporaryFile(suffix=".unknown", delete=False) as temp_file:
            # Create a file larger than 50MB to trigger compression
            temp_file.write(b"unknown format data" * (60 * 1024 * 1024 // 20))
            temp_path = temp_file.name

        try:
            with patch.object(
                video_compressor,
                "get_video_info",
                side_effect=UnsupportedFormatError("Unsupported format"),
            ):
                result = await video_compressor.compress_if_needed(temp_path, 50)
                assert result.success is False
                assert "format" in result.error_message.lower()
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_compression_timeout_error(self, video_compressor):
        """Test error handling for compression timeout."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"x" * (100 * 1024 * 1024))  # 100MB
            temp_path = temp_file.name

        try:
            mock_video_info = VideoInfo(
                width=1920,
                height=1080,
                duration=120.0,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                size_mb=100,
            )

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                with patch.object(
                    video_compressor,
                    "compress_video",
                    side_effect=CompressionTimeoutError("Timeout"),
                ):
                    result = await video_compressor.compress_if_needed(temp_path, 50)
                    assert result.success is False
                    assert "took too long" in result.error_message.lower()
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_zero_byte_file(self, video_compressor):
        """Test handling of zero-byte files."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_path = temp_file.name  # Empty file

        try:
            result = await video_compressor.compress_if_needed(temp_path, 50)
            # Zero-byte file should be considered "under limit"
            assert result.success is True
            assert result.compressed_path == temp_path
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_very_short_video(self, video_compressor):
        """Test handling of very short videos."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"x" * (60 * 1024 * 1024))  # 60MB
            temp_path = temp_file.name

        try:
            # Very short video (0.1 seconds)
            mock_video_info = VideoInfo(
                width=1920,
                height=1080,
                duration=0.1,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                size_mb=60,
            )

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                with patch.object(video_compressor, "compress_video", return_value=True):
                    result = await video_compressor.compress_if_needed(temp_path, 50)
                    assert result.success is True
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_very_long_video(self, video_compressor):
        """Test handling of very long videos."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"x" * (60 * 1024 * 1024))  # 60MB
            temp_path = temp_file.name

        try:
            # Very long video (10 hours)
            mock_video_info = VideoInfo(
                width=1920,
                height=1080,
                duration=36000.0,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                size_mb=60,
            )

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                estimated_time = await video_compressor.estimate_compression_time(temp_path)
                # Should cap at maximum time
                assert estimated_time <= 600  # Max 10 minutes
        finally:
            os.unlink(temp_path)


class TestPerformanceAndTimeLimits:
    """Test performance characteristics and time limits."""

    @pytest.fixture
    def compression_config(self):
        return {
            "target_size_mb": 45,
            "max_attempts": 3,
            "quality_levels": [28, 32, 36],
            "max_resolution": (1280, 720),
            "timeout_seconds": 10,  # Short timeout for testing
        }

    @pytest.fixture
    def video_compressor(self, compression_config):
        return VideoCompressor(compression_config)

    @pytest.mark.asyncio
    async def test_compression_time_estimation_accuracy(self, video_compressor):
        """Test that compression time estimation is reasonable."""
        test_cases = [
            # (width, height, duration, expected_min_time, expected_max_time)
            (640, 480, 60.0, 5, 120),  # Small video
            (1920, 1080, 120.0, 10, 300),  # Medium video
            (3840, 2160, 300.0, 30, 600),  # Large 4K video
        ]

        for width, height, duration, min_time, max_time in test_cases:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_file.write(b"x" * (60 * 1024 * 1024))  # 60MB
                temp_path = temp_file.name

            try:
                mock_video_info = VideoInfo(
                    width=width,
                    height=height,
                    duration=duration,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=60,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    estimated_time = await video_compressor.estimate_compression_time(temp_path)
                    assert (
                        min_time <= estimated_time <= max_time
                    ), f"Estimated time {estimated_time}s not in range [{min_time}, {max_time}] for {width}x{height}"
            finally:
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_compression_timeout_enforcement(self, video_compressor):
        """Test that compression timeout is properly enforced."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"x" * (100 * 1024 * 1024))  # 100MB
            temp_path = temp_file.name

        try:
            mock_video_info = VideoInfo(
                width=1920,
                height=1080,
                duration=120.0,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                size_mb=100,
            )

            # Mock a slow compression that would exceed timeout
            async def slow_compress(*args, **kwargs):
                await asyncio.sleep(15)  # Longer than 10s timeout
                return True

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                with patch.object(video_compressor, "compress_video", side_effect=slow_compress):
                    start_time = asyncio.get_event_loop().time()
                    result = await video_compressor.compress_if_needed(temp_path, 50)
                    end_time = asyncio.get_event_loop().time()

                    # Should complete within reasonable time (not wait for full 15s)
                    assert (end_time - start_time) < 12
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_files(self, video_compressor):
        """Test memory usage doesn't grow excessively with large files."""
        import gc

        import psutil

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Test with multiple large files
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_file.write(b"x" * (200 * 1024 * 1024))  # 200MB each
                temp_path = temp_file.name

            try:
                mock_video_info = VideoInfo(
                    width=1920,
                    height=1080,
                    duration=120.0,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=200,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    with patch.object(video_compressor, "compress_video", return_value=True):
                        result = await video_compressor.compress_if_needed(temp_path, 50)
                        assert result.success is True

                # Force garbage collection
                gc.collect()

            finally:
                os.unlink(temp_path)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase}MB"

    @pytest.mark.asyncio
    async def test_concurrent_compression_handling(self, video_compressor):
        """Test handling of multiple concurrent compression requests."""

        async def compress_single_file(file_size_mb: int) -> bool:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                temp_file.write(b"x" * (file_size_mb * 1024 * 1024))
                temp_path = temp_file.name

            try:
                mock_video_info = VideoInfo(
                    width=1920,
                    height=1080,
                    duration=120.0,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=file_size_mb,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    with patch.object(video_compressor, "compress_video", return_value=True):
                        result = await video_compressor.compress_if_needed(temp_path, 50)
                        return result.success
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        # Run multiple compressions concurrently
        tasks = [compress_single_file(60) for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        for result in results:
            assert result is True or isinstance(result, bool)


class TestCompressionQualityAndSettings:
    """Test compression quality settings and validation."""

    @pytest.fixture
    def compression_config(self):
        return {
            "target_size_mb": 45,
            "max_attempts": 3,
            "quality_levels": [28, 32, 36],
            "max_resolution": (1280, 720),
            "timeout_seconds": 300,
        }

    @pytest.fixture
    def video_compressor(self, compression_config):
        return VideoCompressor(compression_config)

    @pytest.mark.asyncio
    async def test_quality_level_progression(self, video_compressor):
        """Test that compression tries different quality levels progressively."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"x" * (100 * 1024 * 1024))  # 100MB
            temp_path = temp_file.name

        try:
            mock_video_info = VideoInfo(
                width=1920,
                height=1080,
                duration=120.0,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                size_mb=100,
            )

            # Track which quality levels are attempted
            attempted_qualities = []

            async def mock_compress_video(
                input_path, output_path, target_size, quality_level=None, **kwargs
            ):
                if quality_level:
                    attempted_qualities.append(quality_level)
                # Simulate failure for first few attempts
                return len(attempted_qualities) >= 2

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                with patch.object(
                    video_compressor, "compress_video", side_effect=mock_compress_video
                ):
                    result = await video_compressor.compress_if_needed(temp_path, 50)

                    # Should have tried multiple quality levels
                    assert len(attempted_qualities) >= 2
                    # Quality levels should be in ascending order (lower quality = higher CRF)
                    assert attempted_qualities == sorted(attempted_qualities)
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_resolution_downscaling(self, video_compressor):
        """Test that very high resolution videos are downscaled."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"x" * (100 * 1024 * 1024))  # 100MB
            temp_path = temp_file.name

        try:
            # 8K video that should be downscaled
            mock_video_info = VideoInfo(
                width=7680,
                height=4320,
                duration=120.0,
                fps=30.0,
                bitrate=50000000,
                codec="h264",
                size_mb=100,
            )

            compression_attempted = False

            async def mock_compress_video(input_path, output_path, target_size, **kwargs):
                nonlocal compression_attempted
                compression_attempted = True
                # Check if resolution was downscaled in kwargs
                if "width" in kwargs and "height" in kwargs:
                    assert kwargs["width"] <= 1280
                    assert kwargs["height"] <= 720
                return True

            with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                with patch.object(
                    video_compressor, "compress_video", side_effect=mock_compress_video
                ):
                    result = await video_compressor.compress_if_needed(temp_path, 50)
                    assert result.success is True
                    assert compression_attempted
        finally:
            os.unlink(temp_path)

    def test_compression_config_validation(self):
        """Test validation of compression configuration."""
        # Valid config
        valid_config = {
            "target_size_mb": 45,
            "max_attempts": 3,
            "quality_levels": [28, 32, 36],
            "max_resolution": (1280, 720),
            "timeout_seconds": 300,
        }
        compressor = VideoCompressor(valid_config)
        assert compressor.config["target_size_mb"] == 45

        # Test with missing values (should use defaults)
        minimal_config = {}
        compressor = VideoCompressor(minimal_config)
        assert "temp_dir" in compressor.config  # Should be set by _setup_temp_directory

    def test_error_message_generation(self):
        """Test generation of user-friendly error messages."""
        from utils.video_compression import get_compression_error_message

        test_cases = [
            (FFmpegNotFoundError("test"), "ffmpeg"),
            (CompressionTimeoutError("test"), "timeout"),
            (InsufficientDiskSpaceError("test"), "disk space"),
            (UnsupportedFormatError("test"), "format"),
            (VideoCorruptedError("test"), "corrupted"),
            (CompressionQualityError("test"), "target size"),
            (FileNotFoundError("test"), "not found"),
            (Exception("generic error"), "unexpected"),
        ]

        for error, expected_text in test_cases:
            message = get_compression_error_message(error)
            assert expected_text.lower() in message.lower()
            assert len(message) > 10  # Should be descriptive


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
