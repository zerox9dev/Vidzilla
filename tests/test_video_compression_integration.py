"""
Integration tests for video compression with monitoring.

This module tests the integration between video compression and monitoring systems.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_compression_config
from utils.compression_monitoring import get_compression_stats, stats_tracker
from utils.video_compression import VideoCompressor


class TestVideoCompressionMonitoringIntegration(unittest.TestCase):
    """Test cases for video compression monitoring integration."""

    def setUp(self):
        """Set up test environment."""
        self.config = get_compression_config()["settings"]
        self.compressor = VideoCompressor(self.config)

        # Clear stats tracker for clean tests
        stats_tracker.metrics_history.clear()
        stats_tracker.success_count = 0
        stats_tracker.failure_count = 0
        stats_tracker.total_processing_time = 0.0
        stats_tracker.total_size_saved_mb = 0.0

    @patch("utils.video_compression.check_ffmpeg_availability")
    @patch("utils.video_compression.get_video_info")
    @patch("utils.video_compression.os.path.exists")
    @patch("utils.video_compression.get_file_size_mb")
    @patch("utils.video_compression.check_video_size_against_limit")
    def test_compression_monitoring_no_compression_needed(
        self, mock_size_check, mock_file_size, mock_exists, mock_video_info, mock_ffmpeg
    ):
        """Test monitoring when no compression is needed."""
        # Mock setup
        mock_ffmpeg.return_value = True
        mock_exists.return_value = True
        mock_file_size.return_value = 30.0  # Under 50MB limit
        mock_size_check.return_value = (False, 30.0)  # No compression needed

        # Test compression
        import asyncio

        async def run_test():
            result = await self.compressor.compress_if_needed(
                "/fake/video.mp4", max_size_mb=50.0, user_id=12345, platform="Instagram"
            )
            return result

        result = asyncio.run(run_test())

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.original_size_mb, 30.0)

        # Verify monitoring was called
        stats = get_compression_stats(1)
        self.assertEqual(stats["total_operations"], 1)
        self.assertEqual(stats["successful_operations"], 1)
        self.assertEqual(stats["success_rate"], 100.0)

    @patch("utils.video_compression.check_ffmpeg_availability")
    @patch("utils.video_compression.os.path.exists")
    @patch("utils.video_compression.get_file_size_mb")
    def test_compression_monitoring_ffmpeg_not_available(
        self, mock_file_size, mock_exists, mock_ffmpeg
    ):
        """Test monitoring when FFmpeg is not available."""
        # Mock setup
        mock_ffmpeg.return_value = False
        mock_exists.return_value = True
        mock_file_size.return_value = 80.0

        # Test compression (should be async but we'll test the sync parts)
        import asyncio

        async def run_test():
            result = await self.compressor.compress_if_needed(
                "/fake/video.mp4", max_size_mb=50.0, user_id=12345, platform="Instagram"
            )
            return result

        result = asyncio.run(run_test())

        # Verify result
        self.assertFalse(result.success)
        self.assertIn("not available", result.error_message)

        # Verify monitoring tracked the failure
        stats = get_compression_stats(1)
        self.assertEqual(stats["total_operations"], 1)
        self.assertEqual(stats["failed_operations"], 1)
        self.assertEqual(stats["success_rate"], 0.0)

    @patch("utils.video_compression.check_ffmpeg_availability")
    @patch("utils.video_compression.os.path.exists")
    def test_compression_monitoring_file_not_found(self, mock_exists, mock_ffmpeg):
        """Test monitoring when file is not found."""
        # Mock setup
        mock_ffmpeg.return_value = True
        mock_exists.return_value = False

        # Test compression
        import asyncio

        async def run_test():
            result = await self.compressor.compress_if_needed(
                "/fake/nonexistent.mp4", max_size_mb=50.0, user_id=12345, platform="Instagram"
            )
            return result

        result = asyncio.run(run_test())

        # Verify result
        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message)

        # Verify monitoring tracked the failure
        stats = get_compression_stats(1)
        self.assertEqual(stats["total_operations"], 1)
        self.assertEqual(stats["failed_operations"], 1)
        self.assertEqual(stats["success_rate"], 0.0)

    def test_configuration_integration(self):
        """Test that compression configuration integrates with monitoring."""
        config = get_compression_config()

        # Verify configuration structure
        self.assertIn("settings", config)
        self.assertIn("monitoring", config)
        self.assertIn("messages", config)

        # Verify monitoring settings
        monitoring = config["monitoring"]
        self.assertIn("enable_detailed_logging", monitoring)
        self.assertIn("enable_performance_metrics", monitoring)
        self.assertIn("enable_compression_stats_tracking", monitoring)

        # Verify compressor uses the configuration
        self.assertEqual(self.compressor.config, config["settings"])

    def test_stats_tracker_integration(self):
        """Test that stats tracker integrates properly."""
        # Simulate some compression operations
        from utils.compression_monitoring import log_compression_result

        # Log successful compression
        log_compression_result(
            user_id=12345,
            original_size_mb=100.0,
            compressed_size_mb=45.0,
            compression_ratio=0.45,
            processing_time_seconds=30.0,
            success=True,
            platform="Instagram",
        )

        # Log failed compression
        log_compression_result(
            user_id=67890,
            original_size_mb=80.0,
            compressed_size_mb=None,
            compression_ratio=None,
            processing_time_seconds=15.0,
            success=False,
            error_type="TimeoutError",
            platform="TikTok",
        )

        # Verify stats
        stats = get_compression_stats(1)
        self.assertEqual(stats["total_operations"], 2)
        self.assertEqual(stats["successful_operations"], 1)
        self.assertEqual(stats["failed_operations"], 1)
        self.assertEqual(stats["success_rate"], 50.0)
        self.assertEqual(stats["average_processing_time"], 22.5)  # (30 + 15) / 2
        self.assertEqual(stats["total_size_saved_mb"], 55.0)  # 100 - 45

        # Verify error breakdown
        self.assertEqual(stats["error_breakdown"]["TimeoutError"], 1)

        # Verify platform breakdown
        self.assertEqual(stats["platform_breakdown"]["Instagram"], 1)
        self.assertEqual(stats["platform_breakdown"]["TikTok"], 1)


if __name__ == "__main__":
    unittest.main()
