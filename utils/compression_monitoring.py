"""
Compression monitoring and logging utilities.

This module provides comprehensive monitoring, logging, and metrics tracking
for the video compression system.
"""

import os
import time
import json
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import psutil

from config import COMPRESSION_MONITORING, ADMIN_IDS


# Configure compression-specific logger
def setup_compression_logger():
    """Set up dedicated logger for compression operations."""
    logger = logging.getLogger("compression")

    # Don't add handlers if they already exist
    if logger.handlers:
        return logger

    # Set log level from configuration
    log_level = getattr(logging, COMPRESSION_MONITORING["log_level"], logging.INFO)
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler for compression logs
    if COMPRESSION_MONITORING["enable_detailed_logging"]:
        try:
            log_file = os.path.join("temp_videos", "compression.log")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")

    return logger


# Global logger instance
compression_logger = setup_compression_logger()


@dataclass
class CompressionMetrics:
    """Container for compression performance metrics."""

    timestamp: float
    user_id: Optional[int]
    original_size_mb: float
    compressed_size_mb: Optional[float]
    compression_ratio: Optional[float]
    processing_time_seconds: float
    success: bool
    error_type: Optional[str]
    platform: Optional[str]
    video_duration: Optional[float]
    video_resolution: Optional[str]
    compression_method: Optional[str]
    disk_space_before_mb: Optional[float]
    disk_space_after_mb: Optional[float]


@dataclass
class SystemMetrics:
    """Container for system performance metrics."""

    timestamp: float
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    available_disk_space_mb: float
    active_compressions: int
    temp_directory_size_mb: float


class CompressionStatsTracker:
    """Tracks compression statistics and performance metrics."""

    def __init__(self):
        """Initialize the stats tracker."""
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 operations
        self.system_metrics_history: deque = deque(maxlen=100)  # Keep last 100 system snapshots
        self.failure_count = 0
        self.success_count = 0
        self.total_processing_time = 0.0
        self.total_size_saved_mb = 0.0
        self.last_admin_notification = 0
        self.active_compressions = 0
        self.lock = threading.Lock()
        self._monitoring_started = False

        # Start background monitoring if enabled
        if COMPRESSION_MONITORING["enable_compression_stats_tracking"]:
            self._start_background_monitoring()

    def _start_background_monitoring(self):
        """Start background thread for system monitoring."""
        if self._monitoring_started:
            return

        def monitor_loop():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(COMPRESSION_MONITORING["stats_log_interval_minutes"] * 60)
                except Exception as e:
                    compression_logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        self._monitoring_started = True
        compression_logger.info("Started background system monitoring")

    def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Get temp directory size
            temp_dir_size = self._get_temp_directory_size()

            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=(disk.used / disk.total) * 100,
                available_disk_space_mb=disk.free / (1024 * 1024),
                active_compressions=self.active_compressions,
                temp_directory_size_mb=temp_dir_size,
            )

            with self.lock:
                self.system_metrics_history.append(metrics)

            # Log system metrics if detailed logging is enabled
            if COMPRESSION_MONITORING["enable_detailed_logging"]:
                compression_logger.info(
                    f"System metrics - CPU: {cpu_percent:.1f}%, "
                    f"Memory: {memory.percent:.1f}%, "
                    f"Disk: {(disk.used / disk.total) * 100:.1f}%, "
                    f"Active compressions: {self.active_compressions}, "
                    f"Temp dir size: {temp_dir_size:.2f}MB"
                )

            # Check for warnings
            self._check_system_warnings(metrics)

        except Exception as e:
            compression_logger.error(f"Error collecting system metrics: {e}")

    def _get_temp_directory_size(self) -> float:
        """Calculate total size of temporary directory in MB."""
        try:
            from utils.video_compression import get_directory_size_mb
            from config import COMPRESSION_SETTINGS

            return get_directory_size_mb(COMPRESSION_SETTINGS["temp_dir"])
        except Exception as e:
            compression_logger.warning(f"Could not calculate temp directory size: {e}")
            return 0.0

    def _check_system_warnings(self, metrics: SystemMetrics):
        """Check system metrics for warning conditions."""
        warnings = []

        if metrics.disk_usage_percent >= COMPRESSION_MONITORING["disk_space_warning_threshold"]:
            warnings.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")

        if metrics.memory_usage_percent >= 90.0:
            warnings.append(f"High memory usage: {metrics.memory_usage_percent:.1f}%")

        if metrics.cpu_usage_percent >= 90.0:
            warnings.append(f"High CPU usage: {metrics.cpu_usage_percent:.1f}%")

        if metrics.temp_directory_size_mb >= 1000.0:  # 1GB
            warnings.append(f"Large temp directory: {metrics.temp_directory_size_mb:.2f}MB")

        if warnings:
            warning_msg = "System warnings: " + ", ".join(warnings)
            compression_logger.warning(warning_msg)

            # Send admin notification if enabled and threshold reached
            if (
                COMPRESSION_MONITORING["enable_admin_notifications"]
                and time.time() - self.last_admin_notification > 3600
            ):  # Max 1 notification per hour
                self._send_admin_notification(warning_msg)

    def record_compression_start(
        self,
        user_id: Optional[int] = None,
        original_size_mb: float = 0.0,
        platform: Optional[str] = None,
    ):
        """Record the start of a compression operation."""
        with self.lock:
            self.active_compressions += 1

        if COMPRESSION_MONITORING["enable_detailed_logging"]:
            compression_logger.info(
                f"Compression started - User: {user_id}, "
                f"Size: {original_size_mb:.2f}MB, "
                f"Platform: {platform}, "
                f"Active: {self.active_compressions}"
            )

    def record_compression_result(self, metrics: CompressionMetrics):
        """Record the result of a compression operation."""
        with self.lock:
            self.active_compressions = max(0, self.active_compressions - 1)
            self.metrics_history.append(metrics)

            if metrics.success:
                self.success_count += 1
                if metrics.compressed_size_mb and metrics.original_size_mb:
                    size_saved = metrics.original_size_mb - metrics.compressed_size_mb
                    self.total_size_saved_mb += max(0, size_saved)
            else:
                self.failure_count += 1

            self.total_processing_time += metrics.processing_time_seconds

        # Log compression result
        if COMPRESSION_MONITORING["enable_detailed_logging"]:
            status = "SUCCESS" if metrics.success else "FAILED"
            compression_logger.info(
                f"Compression {status} - "
                f"User: {metrics.user_id}, "
                f"Size: {metrics.original_size_mb:.2f}MB -> {metrics.compressed_size_mb or 0:.2f}MB, "
                f"Time: {metrics.processing_time_seconds:.2f}s, "
                f"Platform: {metrics.platform}, "
                f"Error: {metrics.error_type or 'None'}"
            )

        # Check for admin notification threshold
        if (
            not metrics.success
            and COMPRESSION_MONITORING["enable_admin_notifications"]
            and self.failure_count % COMPRESSION_MONITORING["admin_notification_threshold_failures"]
            == 0
        ):
            self._send_admin_notification(
                f"Compression failure threshold reached: {self.failure_count} failures"
            )

    def get_performance_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for the specified time period."""
        cutoff_time = time.time() - (hours * 3600)

        with self.lock:
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
            recent_system_metrics = [
                m for m in self.system_metrics_history if m.timestamp >= cutoff_time
            ]

        if not recent_metrics:
            return {
                "period_hours": hours,
                "total_operations": 0,
                "success_rate": 0.0,
                "average_processing_time": 0.0,
                "total_size_saved_mb": 0.0,
                "average_compression_ratio": 0.0,
                "error_breakdown": {},
                "platform_breakdown": {},
                "system_performance": {},
            }

        # Calculate statistics
        total_ops = len(recent_metrics)
        successful_ops = sum(1 for m in recent_metrics if m.success)
        success_rate = (successful_ops / total_ops) * 100 if total_ops > 0 else 0

        avg_processing_time = sum(m.processing_time_seconds for m in recent_metrics) / total_ops

        total_size_saved = sum(
            (m.original_size_mb - (m.compressed_size_mb or 0))
            for m in recent_metrics
            if m.success and m.compressed_size_mb
        )

        compression_ratios = [
            m.compression_ratio for m in recent_metrics if m.success and m.compression_ratio
        ]
        avg_compression_ratio = (
            sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0
        )

        # Error breakdown
        error_breakdown = defaultdict(int)
        for m in recent_metrics:
            if not m.success and m.error_type:
                error_breakdown[m.error_type] += 1

        # Platform breakdown
        platform_breakdown = defaultdict(int)
        for m in recent_metrics:
            if m.platform:
                platform_breakdown[m.platform] += 1

        # System performance
        system_performance = {}
        if recent_system_metrics:
            system_performance = {
                "avg_cpu_usage": sum(m.cpu_usage_percent for m in recent_system_metrics)
                / len(recent_system_metrics),
                "avg_memory_usage": sum(m.memory_usage_percent for m in recent_system_metrics)
                / len(recent_system_metrics),
                "avg_disk_usage": sum(m.disk_usage_percent for m in recent_system_metrics)
                / len(recent_system_metrics),
                "min_available_disk_mb": min(
                    m.available_disk_space_mb for m in recent_system_metrics
                ),
                "max_active_compressions": max(
                    m.active_compressions for m in recent_system_metrics
                ),
                "avg_temp_dir_size_mb": sum(m.temp_directory_size_mb for m in recent_system_metrics)
                / len(recent_system_metrics),
            }

        return {
            "period_hours": hours,
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": total_ops - successful_ops,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time,
            "total_size_saved_mb": total_size_saved,
            "average_compression_ratio": avg_compression_ratio,
            "error_breakdown": dict(error_breakdown),
            "platform_breakdown": dict(platform_breakdown),
            "system_performance": system_performance,
        }

    def _send_admin_notification(self, message: str):
        """Send notification to administrators."""
        try:
            # This would integrate with the bot's messaging system
            # For now, just log the notification
            compression_logger.warning(f"ADMIN NOTIFICATION: {message}")
            self.last_admin_notification = time.time()

            # In a real implementation, you would send this via the bot:
            # for admin_id in ADMIN_IDS:
            #     bot.send_message(admin_id, f"🚨 Compression System Alert: {message}")

        except Exception as e:
            compression_logger.error(f"Failed to send admin notification: {e}")

    def cleanup_old_metrics(self):
        """Clean up old metrics based on retention policy."""
        retention_seconds = COMPRESSION_MONITORING["metrics_retention_days"] * 24 * 3600
        cutoff_time = time.time() - retention_seconds

        with self.lock:
            # Clean up compression metrics
            original_count = len(self.metrics_history)
            self.metrics_history = deque(
                (m for m in self.metrics_history if m.timestamp >= cutoff_time),
                maxlen=self.metrics_history.maxlen,
            )

            # Clean up system metrics
            original_system_count = len(self.system_metrics_history)
            self.system_metrics_history = deque(
                (m for m in self.system_metrics_history if m.timestamp >= cutoff_time),
                maxlen=self.system_metrics_history.maxlen,
            )

        cleaned_count = original_count - len(self.metrics_history)
        cleaned_system_count = original_system_count - len(self.system_metrics_history)

        if cleaned_count > 0 or cleaned_system_count > 0:
            compression_logger.info(
                f"Cleaned up {cleaned_count} compression metrics and "
                f"{cleaned_system_count} system metrics older than {COMPRESSION_MONITORING['metrics_retention_days']} days"
            )

    def export_metrics(self, filepath: str, hours: int = 24):
        """Export metrics to JSON file."""
        try:
            stats = self.get_performance_stats(hours)

            # Add raw metrics for detailed analysis
            cutoff_time = time.time() - (hours * 3600)
            with self.lock:
                recent_metrics = [
                    asdict(m) for m in self.metrics_history if m.timestamp >= cutoff_time
                ]
                recent_system_metrics = [
                    asdict(m) for m in self.system_metrics_history if m.timestamp >= cutoff_time
                ]

            export_data = {
                "export_timestamp": time.time(),
                "export_date": datetime.now().isoformat(),
                "period_hours": hours,
                "summary_stats": stats,
                "compression_metrics": recent_metrics,
                "system_metrics": recent_system_metrics,
            }

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2)

            compression_logger.info(f"Exported metrics to {filepath}")

        except Exception as e:
            compression_logger.error(f"Failed to export metrics: {e}")


# Global stats tracker instance
stats_tracker = CompressionStatsTracker()


def log_compression_start(
    user_id: Optional[int] = None, original_size_mb: float = 0.0, platform: Optional[str] = None
):
    """Log the start of a compression operation."""
    if COMPRESSION_MONITORING["enable_compression_stats_tracking"]:
        stats_tracker.record_compression_start(user_id, original_size_mb, platform)


def log_compression_result(
    user_id: Optional[int] = None,
    original_size_mb: float = 0.0,
    compressed_size_mb: Optional[float] = None,
    compression_ratio: Optional[float] = None,
    processing_time_seconds: float = 0.0,
    success: bool = False,
    error_type: Optional[str] = None,
    platform: Optional[str] = None,
    video_duration: Optional[float] = None,
    video_resolution: Optional[str] = None,
    compression_method: Optional[str] = None,
    disk_space_before_mb: Optional[float] = None,
    disk_space_after_mb: Optional[float] = None,
):
    """Log the result of a compression operation."""
    if COMPRESSION_MONITORING["enable_compression_stats_tracking"]:
        metrics = CompressionMetrics(
            timestamp=time.time(),
            user_id=user_id,
            original_size_mb=original_size_mb,
            compressed_size_mb=compressed_size_mb,
            compression_ratio=compression_ratio,
            processing_time_seconds=processing_time_seconds,
            success=success,
            error_type=error_type,
            platform=platform,
            video_duration=video_duration,
            video_resolution=video_resolution,
            compression_method=compression_method,
            disk_space_before_mb=disk_space_before_mb,
            disk_space_after_mb=disk_space_after_mb,
        )
        stats_tracker.record_compression_result(metrics)


def get_compression_stats(hours: int = 24) -> Dict[str, Any]:
    """Get compression performance statistics."""
    if COMPRESSION_MONITORING["enable_performance_metrics"]:
        return stats_tracker.get_performance_stats(hours)
    return {}


def cleanup_old_metrics():
    """Clean up old metrics based on retention policy."""
    if COMPRESSION_MONITORING["enable_compression_stats_tracking"]:
        stats_tracker.cleanup_old_metrics()


def export_compression_metrics(filepath: str, hours: int = 24):
    """Export compression metrics to file."""
    if COMPRESSION_MONITORING["enable_performance_metrics"]:
        stats_tracker.export_metrics(filepath, hours)


def log_disk_space_warning(path: str, usage_percent: float, available_mb: float):
    """Log disk space warning."""
    compression_logger.warning(
        f"Disk space warning for {path}: {usage_percent:.1f}% used, "
        f"{available_mb:.2f}MB available"
    )


def log_compression_timeout(video_path: str, timeout_seconds: int):
    """Log compression timeout."""
    compression_logger.error(
        f"Compression timeout after {timeout_seconds}s for video: {video_path}"
    )


def log_ffmpeg_error(video_path: str, error_message: str):
    """Log FFmpeg-related errors."""
    compression_logger.error(f"FFmpeg error for {video_path}: {error_message}")


def log_cleanup_operation(files_cleaned: int, size_freed_mb: float):
    """Log cleanup operations."""
    if files_cleaned > 0:
        compression_logger.info(
            f"Cleanup completed: {files_cleaned} files removed, " f"{size_freed_mb:.2f}MB freed"
        )


def log_performance_metrics(
    operation: str, duration_seconds: float, file_size_mb: float, success: bool
):
    """Log performance metrics for operations."""
    if COMPRESSION_MONITORING["enable_performance_metrics"]:
        status = "SUCCESS" if success else "FAILED"
        rate_mbps = file_size_mb / duration_seconds if duration_seconds > 0 else 0

        compression_logger.info(
            f"Performance - {operation}: {status}, "
            f"Duration: {duration_seconds:.2f}s, "
            f"Size: {file_size_mb:.2f}MB, "
            f"Rate: {rate_mbps:.2f}MB/s"
        )


# Context manager for compression operation logging
class CompressionOperationLogger:
    """Context manager for logging compression operations."""

    def __init__(
        self,
        user_id: Optional[int] = None,
        original_size_mb: float = 0.0,
        platform: Optional[str] = None,
    ):
        """Initialize compression operation logger."""
        self.user_id = user_id
        self.original_size_mb = original_size_mb
        self.platform = platform
        self.start_time = None
        self.success = False
        self.error_type = None
        self.compressed_size_mb = None
        self.compression_ratio = None
        self.video_duration = None
        self.video_resolution = None
        self.compression_method = None
        self.disk_space_before_mb = None
        self.disk_space_after_mb = None

    def __enter__(self):
        """Enter compression operation context."""
        self.start_time = time.time()
        log_compression_start(self.user_id, self.original_size_mb, self.platform)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit compression operation context."""
        processing_time = time.time() - self.start_time if self.start_time else 0.0

        if exc_type:
            self.success = False
            self.error_type = exc_type.__name__

        log_compression_result(
            user_id=self.user_id,
            original_size_mb=self.original_size_mb,
            compressed_size_mb=self.compressed_size_mb,
            compression_ratio=self.compression_ratio,
            processing_time_seconds=processing_time,
            success=self.success,
            error_type=self.error_type,
            platform=self.platform,
            video_duration=self.video_duration,
            video_resolution=self.video_resolution,
            compression_method=self.compression_method,
            disk_space_before_mb=self.disk_space_before_mb,
            disk_space_after_mb=self.disk_space_after_mb,
        )

        return False  # Don't suppress exceptions

    def set_result(
        self,
        success: bool,
        compressed_size_mb: Optional[float] = None,
        compression_ratio: Optional[float] = None,
        video_duration: Optional[float] = None,
        video_resolution: Optional[str] = None,
        compression_method: Optional[str] = None,
    ):
        """Set compression result details."""
        self.success = success
        self.compressed_size_mb = compressed_size_mb
        self.compression_ratio = compression_ratio
        self.video_duration = video_duration
        self.video_resolution = video_resolution
        self.compression_method = compression_method

    def set_disk_space(self, before_mb: Optional[float], after_mb: Optional[float]):
        """Set disk space measurements."""
        self.disk_space_before_mb = before_mb
        self.disk_space_after_mb = after_mb
