"""
Tests for compression configuration system.

This module tests the configuration loading, validation, and environment variable support
for the video compression system.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add the project root to the path so we can import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config


class TestCompressionConfiguration(unittest.TestCase):
    """Test cases for compression configuration system."""

    def setUp(self):
        """Set up test environment."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_default_compression_settings(self):
        """Test that default compression settings are loaded correctly."""
        # Clear environment variables to test defaults
        for key in list(os.environ.keys()):
            if key.startswith("COMPRESSION_"):
                del os.environ[key]

        # Reload config module to get fresh settings
        import importlib

        importlib.reload(config)

        settings = config.COMPRESSION_SETTINGS

        # Test default values
        self.assertEqual(settings["target_size_mb"], 45.0)
        self.assertEqual(settings["max_attempts"], 3)
        self.assertEqual(settings["quality_levels"], [28, 32, 36])
        self.assertEqual(settings["max_resolution"], (1280, 720))
        self.assertEqual(settings["timeout_seconds"], 300)
        self.assertEqual(settings["min_quality_crf"], 18)
        self.assertEqual(settings["max_quality_crf"], 40)
        self.assertEqual(settings["disk_space_threshold_mb"], 1000.0)
        self.assertEqual(settings["cleanup_temp_files_hours"], 24)
        self.assertTrue(settings["enable_progress_callbacks"])
        self.assertTrue(settings["enable_resolution_downscaling"])
        self.assertEqual(settings["max_concurrent_compressions"], 2)
        self.assertEqual(settings["ffmpeg_preset"], "medium")
        self.assertFalse(settings["enable_hardware_acceleration"])

    def test_environment_variable_override(self):
        """Test that environment variables override default settings."""
        # Set environment variables
        os.environ["COMPRESSION_TARGET_SIZE_MB"] = "40"
        os.environ["COMPRESSION_MAX_ATTEMPTS"] = "5"
        os.environ["COMPRESSION_QUALITY_LEVELS"] = "20,25,30,35"
        os.environ["COMPRESSION_MAX_RESOLUTION"] = "1920,1080"
        os.environ["COMPRESSION_TIMEOUT_SECONDS"] = "600"
        os.environ["COMPRESSION_MIN_QUALITY_CRF"] = "15"
        os.environ["COMPRESSION_MAX_QUALITY_CRF"] = "45"
        os.environ["COMPRESSION_DISK_SPACE_THRESHOLD_MB"] = "2000"
        os.environ["COMPRESSION_CLEANUP_TEMP_FILES_HOURS"] = "48"
        os.environ["COMPRESSION_ENABLE_PROGRESS_CALLBACKS"] = "false"
        os.environ["COMPRESSION_ENABLE_RESOLUTION_DOWNSCALING"] = "false"
        os.environ["COMPRESSION_MAX_CONCURRENT"] = "4"
        os.environ["COMPRESSION_FFMPEG_PRESET"] = "fast"
        os.environ["COMPRESSION_ENABLE_HARDWARE_ACCEL"] = "true"

        # Reload config module to get updated settings
        import importlib

        importlib.reload(config)

        settings = config.COMPRESSION_SETTINGS

        # Test overridden values
        self.assertEqual(settings["target_size_mb"], 40.0)
        self.assertEqual(settings["max_attempts"], 5)
        self.assertEqual(settings["quality_levels"], [20, 25, 30, 35])
        self.assertEqual(settings["max_resolution"], (1920, 1080))
        self.assertEqual(settings["timeout_seconds"], 600)
        self.assertEqual(settings["min_quality_crf"], 15)
        self.assertEqual(settings["max_quality_crf"], 45)
        self.assertEqual(settings["disk_space_threshold_mb"], 2000.0)
        self.assertEqual(settings["cleanup_temp_files_hours"], 48)
        self.assertFalse(settings["enable_progress_callbacks"])
        self.assertFalse(settings["enable_resolution_downscaling"])
        self.assertEqual(settings["max_concurrent_compressions"], 4)
        self.assertEqual(settings["ffmpeg_preset"], "fast")
        self.assertTrue(settings["enable_hardware_acceleration"])

    def test_default_monitoring_settings(self):
        """Test that default monitoring settings are loaded correctly."""
        # Clear environment variables to test defaults
        for key in list(os.environ.keys()):
            if key.startswith("COMPRESSION_"):
                del os.environ[key]

        # Reload config module to get fresh settings
        import importlib

        importlib.reload(config)

        monitoring = config.COMPRESSION_MONITORING

        # Test default values
        self.assertTrue(monitoring["enable_detailed_logging"])
        self.assertEqual(monitoring["log_level"], "INFO")
        self.assertTrue(monitoring["enable_performance_metrics"])
        self.assertEqual(monitoring["metrics_retention_days"], 30)
        self.assertTrue(monitoring["enable_disk_space_monitoring"])
        self.assertEqual(monitoring["disk_space_warning_threshold"], 90.0)
        self.assertTrue(monitoring["enable_admin_notifications"])
        self.assertEqual(monitoring["admin_notification_threshold_failures"], 5)
        self.assertTrue(monitoring["enable_compression_stats_tracking"])
        self.assertEqual(monitoring["stats_log_interval_minutes"], 60)

    def test_monitoring_environment_variables(self):
        """Test that monitoring environment variables work correctly."""
        # Set environment variables
        os.environ["COMPRESSION_ENABLE_DETAILED_LOGGING"] = "false"
        os.environ["COMPRESSION_LOG_LEVEL"] = "DEBUG"
        os.environ["COMPRESSION_ENABLE_PERFORMANCE_METRICS"] = "false"
        os.environ["COMPRESSION_METRICS_RETENTION_DAYS"] = "60"
        os.environ["COMPRESSION_ENABLE_DISK_MONITORING"] = "false"
        os.environ["COMPRESSION_DISK_WARNING_THRESHOLD"] = "85.0"
        os.environ["COMPRESSION_ENABLE_ADMIN_NOTIFICATIONS"] = "false"
        os.environ["COMPRESSION_ADMIN_NOTIFICATION_THRESHOLD"] = "10"
        os.environ["COMPRESSION_ENABLE_STATS_TRACKING"] = "false"
        os.environ["COMPRESSION_STATS_LOG_INTERVAL"] = "30"

        # Reload config module to get updated settings
        import importlib

        importlib.reload(config)

        monitoring = config.COMPRESSION_MONITORING

        # Test overridden values
        self.assertFalse(monitoring["enable_detailed_logging"])
        self.assertEqual(monitoring["log_level"], "DEBUG")
        self.assertFalse(monitoring["enable_performance_metrics"])
        self.assertEqual(monitoring["metrics_retention_days"], 60)
        self.assertFalse(monitoring["enable_disk_space_monitoring"])
        self.assertEqual(monitoring["disk_space_warning_threshold"], 85.0)
        self.assertFalse(monitoring["enable_admin_notifications"])
        self.assertEqual(monitoring["admin_notification_threshold_failures"], 10)
        self.assertFalse(monitoring["enable_compression_stats_tracking"])
        self.assertEqual(monitoring["stats_log_interval_minutes"], 30)

    @patch("logging.getLogger")
    def test_config_validation_valid(self, mock_logger):
        """Test configuration validation with valid settings."""
        # Set up valid environment variables
        os.environ["COMPRESSION_TARGET_SIZE_MB"] = "45"
        os.environ["COMPRESSION_MAX_ATTEMPTS"] = "3"
        os.environ["COMPRESSION_QUALITY_LEVELS"] = "28,32,36"
        os.environ["COMPRESSION_MAX_RESOLUTION"] = "1280,720"
        os.environ["COMPRESSION_TIMEOUT_SECONDS"] = "300"
        os.environ["COMPRESSION_MIN_QUALITY_CRF"] = "18"
        os.environ["COMPRESSION_MAX_QUALITY_CRF"] = "40"

        # Reload config module
        import importlib

        importlib.reload(config)

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Test validation
        result = config.validate_compression_config()

        self.assertTrue(result)
        mock_logger_instance.info.assert_called_with("Compression configuration validation passed")

    @patch("logging.getLogger")
    def test_config_validation_invalid_target_size(self, mock_logger):
        """Test configuration validation with invalid target size."""
        # Set invalid target size
        os.environ["COMPRESSION_TARGET_SIZE_MB"] = "0"

        # Reload config module
        import importlib

        importlib.reload(config)

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Test validation
        result = config.validate_compression_config()

        self.assertFalse(result)
        mock_logger_instance.warning.assert_any_call(
            "Invalid target_size_mb: 0.0. Should be between 1-100MB"
        )

    @patch("logging.getLogger")
    def test_config_validation_invalid_quality_levels(self, mock_logger):
        """Test configuration validation with invalid quality levels."""
        # Set invalid quality levels
        os.environ["COMPRESSION_QUALITY_LEVELS"] = "60,70,80"  # CRF values > 51

        # Reload config module
        import importlib

        importlib.reload(config)

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Test validation
        result = config.validate_compression_config()

        self.assertFalse(result)
        mock_logger_instance.warning.assert_any_call(
            "Invalid quality_levels: [60, 70, 80]. CRF values should be between 0-51"
        )

    @patch("logging.getLogger")
    def test_config_validation_invalid_resolution(self, mock_logger):
        """Test configuration validation with invalid resolution."""
        # Set invalid resolution
        os.environ["COMPRESSION_MAX_RESOLUTION"] = "0,720"

        # Reload config module
        import importlib

        importlib.reload(config)

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Test validation
        result = config.validate_compression_config()

        self.assertFalse(result)
        mock_logger_instance.warning.assert_any_call(
            "Invalid max_resolution: (0, 720). Should be (width, height) with positive values"
        )

    @patch("logging.getLogger")
    def test_config_validation_crf_range_error(self, mock_logger):
        """Test configuration validation with invalid CRF range."""
        # Set min CRF >= max CRF
        os.environ["COMPRESSION_MIN_QUALITY_CRF"] = "30"
        os.environ["COMPRESSION_MAX_QUALITY_CRF"] = "25"

        # Reload config module
        import importlib

        importlib.reload(config)

        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Test validation
        result = config.validate_compression_config()

        self.assertFalse(result)
        mock_logger_instance.warning.assert_any_call(
            "min_quality_crf (30) should be less than max_quality_crf (25)"
        )

    def test_get_compression_config(self):
        """Test get_compression_config function returns complete configuration."""
        # Reload config module
        import importlib

        importlib.reload(config)

        config_dict = config.get_compression_config()

        # Test structure
        self.assertIn("settings", config_dict)
        self.assertIn("monitoring", config_dict)
        self.assertIn("messages", config_dict)

        # Test that settings are included
        self.assertIn("target_size_mb", config_dict["settings"])
        self.assertIn("max_attempts", config_dict["settings"])
        self.assertIn("quality_levels", config_dict["settings"])

        # Test that monitoring is included
        self.assertIn("enable_detailed_logging", config_dict["monitoring"])
        self.assertIn("log_level", config_dict["monitoring"])

        # Test that messages are included
        self.assertIn("start", config_dict["messages"])
        self.assertIn("success", config_dict["messages"])
        self.assertIn("error", config_dict["messages"])

    def test_temp_directory_creation(self):
        """Test that temp directory is created and accessible."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set custom temp directory
            os.environ["COMPRESSION_TEMP_DIR"] = temp_dir

            # Reload config module
            import importlib

            importlib.reload(config)

            # Test that directory exists
            self.assertTrue(os.path.exists(config.COMPRESSION_SETTINGS["temp_dir"]))
            self.assertEqual(config.COMPRESSION_SETTINGS["temp_dir"], temp_dir)

    def test_boolean_environment_variables(self):
        """Test that boolean environment variables are parsed correctly."""
        # Test various boolean representations
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("yes", False),  # Only 'true' should be True
            ("1", False),  # Only 'true' should be True
            ("", False),  # Empty string should be False
        ]

        for env_value, expected in test_cases:
            with self.subTest(env_value=env_value, expected=expected):
                os.environ["COMPRESSION_ENABLE_PROGRESS_CALLBACKS"] = env_value

                # Reload config module
                import importlib

                importlib.reload(config)

                self.assertEqual(
                    config.COMPRESSION_SETTINGS["enable_progress_callbacks"],
                    expected,
                    f"Environment value '{env_value}' should result in {expected}",
                )


if __name__ == "__main__":
    unittest.main()
