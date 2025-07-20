"""
Tests for compression monitoring and logging system.

This module tests the monitoring, logging, and metrics tracking functionality
for the video compression system.
"""

import os
import time
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import threading

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.compression_monitoring import (
    CompressionMetrics,
    SystemMetrics,
    CompressionStatsTracker,
    CompressionOperationLogger,
    log_compression_start,
    log_compression_result,
    get_compression_stats,
    cleanup_old_metrics,
    export_compression_metrics,
    log_disk_space_warning,
    log_compression_timeout,
    log_ffmpeg_error,
    log_cleanup_operation,
    log_performance_metrics,
    compression_logger
)


class TestCompressionMetrics(unittest.TestCase):
    """Test cases for compression metrics data structures."""
    
    def test_compression_metrics_creation(self):
        """Test creating CompressionMetrics object."""
        metrics = CompressionMetrics(
            timestamp=time.time(),
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            error_type=None,
            platform="Instagram",
            video_duration=60.0,
            video_resolution="1920x1080",
            compression_method="H.264",
            disk_space_before_mb=1000.0,
            disk_space_after_mb=955.0
        )
        
        self.assertEqual(metrics.user_id, 12345)
        self.assertEqual(metrics.original_size_mb, 100.0)
        self.assertEqual(metrics.compressed_size_mb, 45.0)
        self.assertEqual(metrics.compression_ratio, 0.45)
        self.assertTrue(metrics.success)
        self.assertEqual(metrics.platform, "Instagram")
    
    def test_system_metrics_creation(self):
        """Test creating SystemMetrics object."""
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_usage_percent=45.5,
            memory_usage_percent=60.2,
            disk_usage_percent=75.0,
            available_disk_space_mb=2000.0,
            active_compressions=2,
            temp_directory_size_mb=150.0
        )
        
        self.assertEqual(metrics.cpu_usage_percent, 45.5)
        self.assertEqual(metrics.memory_usage_percent, 60.2)
        self.assertEqual(metrics.disk_usage_percent, 75.0)
        self.assertEqual(metrics.active_compressions, 2)


class TestCompressionStatsTracker(unittest.TestCase):
    """Test cases for compression statistics tracking."""
    
    def setUp(self):
        """Set up test environment."""
        self.tracker = CompressionStatsTracker()
    
    def test_record_compression_start(self):
        """Test recording compression start."""
        initial_active = self.tracker.active_compressions
        
        self.tracker.record_compression_start(
            user_id=12345,
            original_size_mb=100.0,
            platform="Instagram"
        )
        
        self.assertEqual(self.tracker.active_compressions, initial_active + 1)
    
    def test_record_successful_compression(self):
        """Test recording successful compression result."""
        metrics = CompressionMetrics(
            timestamp=time.time(),
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            error_type=None,
            platform="Instagram",
            video_duration=60.0,
            video_resolution="1920x1080",
            compression_method="H.264",
            disk_space_before_mb=1000.0,
            disk_space_after_mb=955.0
        )
        
        initial_success = self.tracker.success_count
        initial_total_time = self.tracker.total_processing_time
        initial_size_saved = self.tracker.total_size_saved_mb
        
        self.tracker.record_compression_result(metrics)
        
        self.assertEqual(self.tracker.success_count, initial_success + 1)
        self.assertEqual(self.tracker.total_processing_time, initial_total_time + 30.0)
        self.assertEqual(self.tracker.total_size_saved_mb, initial_size_saved + 55.0)
        self.assertIn(metrics, self.tracker.metrics_history)
    
    def test_record_failed_compression(self):
        """Test recording failed compression result."""
        metrics = CompressionMetrics(
            timestamp=time.time(),
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=None,
            compression_ratio=None,
            processing_time_seconds=15.0,
            success=False,
            error_type="FFmpegError",
            platform="Instagram",
            video_duration=None,
            video_resolution=None,
            compression_method=None,
            disk_space_before_mb=1000.0,
            disk_space_after_mb=1000.0
        )
        
        initial_failure = self.tracker.failure_count
        initial_total_time = self.tracker.total_processing_time
        
        self.tracker.record_compression_result(metrics)
        
        self.assertEqual(self.tracker.failure_count, initial_failure + 1)
        self.assertEqual(self.tracker.total_processing_time, initial_total_time + 15.0)
        self.assertIn(metrics, self.tracker.metrics_history)
    
    def test_get_performance_stats_empty(self):
        """Test getting performance stats with no data."""
        stats = self.tracker.get_performance_stats(24)
        
        self.assertEqual(stats['total_operations'], 0)
        self.assertEqual(stats['success_rate'], 0.0)
        self.assertEqual(stats['average_processing_time'], 0.0)
        self.assertEqual(stats['total_size_saved_mb'], 0.0)
        self.assertEqual(stats['error_breakdown'], {})
        self.assertEqual(stats['platform_breakdown'], {})
    
    def test_get_performance_stats_with_data(self):
        """Test getting performance stats with sample data."""
        # Add some sample metrics
        current_time = time.time()
        
        # Successful compression
        success_metrics = CompressionMetrics(
            timestamp=current_time,
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            error_type=None,
            platform="Instagram",
            video_duration=60.0,
            video_resolution="1920x1080",
            compression_method="H.264",
            disk_space_before_mb=1000.0,
            disk_space_after_mb=955.0
        )
        
        # Failed compression
        failure_metrics = CompressionMetrics(
            timestamp=current_time,
            user_id=67890,
            original_size_mb=80.0,
            compressed_size_mb=None,
            compression_ratio=None,
            processing_time_seconds=10.0,
            success=False,
            error_type="TimeoutError",
            platform="TikTok",
            video_duration=None,
            video_resolution=None,
            compression_method=None,
            disk_space_before_mb=1000.0,
            disk_space_after_mb=1000.0
        )
        
        self.tracker.record_compression_result(success_metrics)
        self.tracker.record_compression_result(failure_metrics)
        
        stats = self.tracker.get_performance_stats(24)
        
        self.assertEqual(stats['total_operations'], 2)
        self.assertEqual(stats['successful_operations'], 1)
        self.assertEqual(stats['failed_operations'], 1)
        self.assertEqual(stats['success_rate'], 50.0)
        self.assertEqual(stats['average_processing_time'], 20.0)  # (30 + 10) / 2
        self.assertEqual(stats['total_size_saved_mb'], 55.0)  # 100 - 45
        self.assertEqual(stats['error_breakdown']['TimeoutError'], 1)
        self.assertEqual(stats['platform_breakdown']['Instagram'], 1)
        self.assertEqual(stats['platform_breakdown']['TikTok'], 1)
    
    def test_cleanup_old_metrics(self):
        """Test cleaning up old metrics."""
        # Add old metric (more than retention period)
        old_time = time.time() - (31 * 24 * 3600)  # 31 days ago
        old_metrics = CompressionMetrics(
            timestamp=old_time,
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            error_type=None,
            platform="Instagram",
            video_duration=60.0,
            video_resolution="1920x1080",
            compression_method="H.264",
            disk_space_before_mb=1000.0,
            disk_space_after_mb=955.0
        )
        
        # Add recent metric
        recent_metrics = CompressionMetrics(
            timestamp=time.time(),
            user_id=67890,
            original_size_mb=80.0,
            compressed_size_mb=40.0,
            compression_ratio=0.5,
            processing_time_seconds=25.0,
            success=True,
            error_type=None,
            platform="TikTok",
            video_duration=45.0,
            video_resolution="1280x720",
            compression_method="H.264",
            disk_space_before_mb=1000.0,
            disk_space_after_mb=960.0
        )
        
        self.tracker.record_compression_result(old_metrics)
        self.tracker.record_compression_result(recent_metrics)
        
        self.assertEqual(len(self.tracker.metrics_history), 2)
        
        # Clean up old metrics
        self.tracker.cleanup_old_metrics()
        
        # Should only have recent metric
        self.assertEqual(len(self.tracker.metrics_history), 1)
        self.assertEqual(self.tracker.metrics_history[0].user_id, 67890)
    
    def test_export_metrics(self):
        """Test exporting metrics to JSON file."""
        # Add sample metric
        metrics = CompressionMetrics(
            timestamp=time.time(),
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            error_type=None,
            platform="Instagram",
            video_duration=60.0,
            video_resolution="1920x1080",
            compression_method="H.264",
            disk_space_before_mb=1000.0,
            disk_space_after_mb=955.0
        )
        
        self.tracker.record_compression_result(metrics)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.tracker.export_metrics(temp_file, hours=24)
            
            # Verify file was created and contains expected data
            self.assertTrue(os.path.exists(temp_file))
            
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            self.assertIn('export_timestamp', data)
            self.assertIn('summary_stats', data)
            self.assertIn('compression_metrics', data)
            self.assertEqual(data['period_hours'], 24)
            self.assertEqual(len(data['compression_metrics']), 1)
            self.assertEqual(data['compression_metrics'][0]['user_id'], 12345)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestCompressionOperationLogger(unittest.TestCase):
    """Test cases for compression operation logger context manager."""
    
    @patch('utils.compression_monitoring.log_compression_start')
    @patch('utils.compression_monitoring.log_compression_result')
    def test_successful_operation(self, mock_log_result, mock_log_start):
        """Test logging successful compression operation."""
        with CompressionOperationLogger(
            user_id=12345,
            original_size_mb=100.0,
            platform="Instagram"
        ) as logger:
            # Simulate successful compression
            logger.set_result(
                success=True,
                compressed_size_mb=45.0,
                compression_ratio=0.45,
                video_duration=60.0,
                video_resolution="1920x1080",
                compression_method="H.264"
            )
            logger.set_disk_space(1000.0, 955.0)
        
        # Verify start was logged
        mock_log_start.assert_called_once_with(12345, 100.0, "Instagram")
        
        # Verify result was logged
        mock_log_result.assert_called_once()
        call_args = mock_log_result.call_args[1]
        self.assertEqual(call_args['user_id'], 12345)
        self.assertEqual(call_args['original_size_mb'], 100.0)
        self.assertEqual(call_args['compressed_size_mb'], 45.0)
        self.assertTrue(call_args['success'])
        self.assertEqual(call_args['platform'], "Instagram")
    
    @patch('utils.compression_monitoring.log_compression_start')
    @patch('utils.compression_monitoring.log_compression_result')
    def test_failed_operation_with_exception(self, mock_log_result, mock_log_start):
        """Test logging failed compression operation with exception."""
        try:
            with CompressionOperationLogger(
                user_id=12345,
                original_size_mb=100.0,
                platform="Instagram"
            ) as logger:
                # Simulate failure
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
        
        # Verify start was logged
        mock_log_start.assert_called_once_with(12345, 100.0, "Instagram")
        
        # Verify result was logged with failure
        mock_log_result.assert_called_once()
        call_args = mock_log_result.call_args[1]
        self.assertEqual(call_args['user_id'], 12345)
        self.assertFalse(call_args['success'])
        self.assertEqual(call_args['error_type'], "ValueError")


class TestLoggingFunctions(unittest.TestCase):
    """Test cases for logging utility functions."""
    
    @patch('utils.compression_monitoring.compression_logger')
    def test_log_disk_space_warning(self, mock_logger):
        """Test disk space warning logging."""
        log_disk_space_warning("/tmp", 95.5, 100.0)
        
        mock_logger.warning.assert_called_once_with(
            "Disk space warning for /tmp: 95.5% used, 100.00MB available"
        )
    
    @patch('utils.compression_monitoring.compression_logger')
    def test_log_compression_timeout(self, mock_logger):
        """Test compression timeout logging."""
        log_compression_timeout("/path/to/video.mp4", 300)
        
        mock_logger.error.assert_called_once_with(
            "Compression timeout after 300s for video: /path/to/video.mp4"
        )
    
    @patch('utils.compression_monitoring.compression_logger')
    def test_log_ffmpeg_error(self, mock_logger):
        """Test FFmpeg error logging."""
        log_ffmpeg_error("/path/to/video.mp4", "Invalid codec")
        
        mock_logger.error.assert_called_once_with(
            "FFmpeg error for /path/to/video.mp4: Invalid codec"
        )
    
    @patch('utils.compression_monitoring.compression_logger')
    def test_log_cleanup_operation(self, mock_logger):
        """Test cleanup operation logging."""
        log_cleanup_operation(5, 250.5)
        
        mock_logger.info.assert_called_once_with(
            "Cleanup completed: 5 files removed, 250.50MB freed"
        )
    
    @patch('utils.compression_monitoring.compression_logger')
    def test_log_cleanup_operation_no_files(self, mock_logger):
        """Test cleanup operation logging with no files cleaned."""
        log_cleanup_operation(0, 0.0)
        
        # Should not log anything when no files were cleaned
        mock_logger.info.assert_not_called()
    
    @patch('utils.compression_monitoring.compression_logger')
    def test_log_performance_metrics(self, mock_logger):
        """Test performance metrics logging."""
        log_performance_metrics("compression", 30.5, 100.0, True)
        
        mock_logger.info.assert_called_once_with(
            "Performance - compression: SUCCESS, "
            "Duration: 30.50s, "
            "Size: 100.00MB, "
            "Rate: 3.28MB/s"
        )


class TestModuleFunctions(unittest.TestCase):
    """Test cases for module-level functions."""
    
    @patch('utils.compression_monitoring.stats_tracker')
    def test_log_compression_start(self, mock_tracker):
        """Test log_compression_start function."""
        log_compression_start(12345, 100.0, "Instagram")
        
        mock_tracker.record_compression_start.assert_called_once_with(
            12345, 100.0, "Instagram"
        )
    
    @patch('utils.compression_monitoring.stats_tracker')
    def test_log_compression_result(self, mock_tracker):
        """Test log_compression_result function."""
        log_compression_result(
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            platform="Instagram"
        )
        
        mock_tracker.record_compression_result.assert_called_once()
        call_args = mock_tracker.record_compression_result.call_args[0][0]
        self.assertEqual(call_args.user_id, 12345)
        self.assertEqual(call_args.original_size_mb, 100.0)
        self.assertEqual(call_args.compressed_size_mb, 45.0)
        self.assertTrue(call_args.success)
    
    @patch('utils.compression_monitoring.stats_tracker')
    def test_get_compression_stats(self, mock_tracker):
        """Test get_compression_stats function."""
        mock_tracker.get_performance_stats.return_value = {'test': 'data'}
        
        result = get_compression_stats(24)
        
        mock_tracker.get_performance_stats.assert_called_once_with(24)
        self.assertEqual(result, {'test': 'data'})
    
    @patch('utils.compression_monitoring.stats_tracker')
    def test_cleanup_old_metrics(self, mock_tracker):
        """Test cleanup_old_metrics function."""
        cleanup_old_metrics()
        
        mock_tracker.cleanup_old_metrics.assert_called_once()
    
    @patch('utils.compression_monitoring.stats_tracker')
    def test_export_compression_metrics(self, mock_tracker):
        """Test export_compression_metrics function."""
        export_compression_metrics("/tmp/metrics.json", 48)
        
        mock_tracker.export_metrics.assert_called_once_with("/tmp/metrics.json", 48)


if __name__ == '__main__':
    unittest.main()