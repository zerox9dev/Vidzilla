"""
Unit tests for video size checking and compression decision logic.

Tests for task 3.1: Create file size detection system
"""

import os
import tempfile
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from utils.video_compression import (
    check_video_size_against_limit,
    should_compress_video,
    get_file_size_mb,
    VideoCompressor,
    create_compression_result,
)
from config import COMPRESSION_SETTINGS


class TestFileSizeDetection:
    """Test file size detection functionality."""

    def test_get_file_size_mb_existing_file(self):
        """Test getting file size for existing file."""
        # Create a temporary file with known size
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 1MB of data (1024 * 1024 bytes)
            data = b"0" * (1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            file_size_mb = get_file_size_mb(temp_file.name)

            # Should be approximately 1MB
            assert abs(file_size_mb - 1.0) < 0.01

        # Clean up
        os.unlink(temp_file.name)

    def test_get_file_size_mb_nonexistent_file(self):
        """Test getting file size for non-existent file."""
        file_size_mb = get_file_size_mb("/nonexistent/file.mp4")
        assert file_size_mb == 0.0

    def test_check_video_size_against_limit_under_limit(self):
        """Test size checking for file under limit."""
        # Create a small temporary file (less than 50MB)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 10MB of data
            data = b"0" * (10 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            needs_compression, file_size_mb = check_video_size_against_limit(temp_file.name, 50.0)

            assert needs_compression is False
            assert abs(file_size_mb - 10.0) < 0.1

        # Clean up
        os.unlink(temp_file.name)

    def test_check_video_size_against_limit_over_limit(self):
        """Test size checking for file over limit."""
        # Create a large temporary file (more than 50MB)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 60MB of data
            data = b"0" * (60 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            needs_compression, file_size_mb = check_video_size_against_limit(temp_file.name, 50.0)

            assert needs_compression is True
            assert abs(file_size_mb - 60.0) < 0.1

        # Clean up
        os.unlink(temp_file.name)

    def test_check_video_size_against_limit_exactly_at_limit(self):
        """Test size checking for file exactly at limit."""
        # Create a file exactly at the limit
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write exactly 50MB of data
            data = b"0" * (50 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            needs_compression, file_size_mb = check_video_size_against_limit(temp_file.name, 50.0)

            assert needs_compression is False  # Should be False for exactly at limit
            assert abs(file_size_mb - 50.0) < 0.1

        # Clean up
        os.unlink(temp_file.name)

    def test_check_video_size_against_limit_nonexistent_file(self):
        """Test size checking for non-existent file."""
        needs_compression, file_size_mb = check_video_size_against_limit(
            "/nonexistent/file.mp4", 50.0
        )

        assert needs_compression is False
        assert file_size_mb == 0.0

    def test_should_compress_video_true(self):
        """Test should_compress_video returns True for large files."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 60MB of data
            data = b"0" * (60 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            result = should_compress_video(temp_file.name, 50.0)
            assert result is True

        # Clean up
        os.unlink(temp_file.name)

    def test_should_compress_video_false(self):
        """Test should_compress_video returns False for small files."""
        # Create a small temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write 10MB of data
            data = b"0" * (10 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            result = should_compress_video(temp_file.name, 50.0)
            assert result is False

        # Clean up
        os.unlink(temp_file.name)

    def test_custom_size_limits(self):
        """Test size checking with custom limits."""
        # Create a 30MB file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            data = b"0" * (30 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            # Test with 25MB limit (should need compression)
            needs_compression, _ = check_video_size_against_limit(temp_file.name, 25.0)
            assert needs_compression is True

            # Test with 35MB limit (should not need compression)
            needs_compression, _ = check_video_size_against_limit(temp_file.name, 35.0)
            assert needs_compression is False

        # Clean up
        os.unlink(temp_file.name)


class TestCompressionDecisionLogic:
    """Test compression decision logic in VideoCompressor."""

    @pytest.fixture
    def video_compressor(self):
        """Create a VideoCompressor instance for testing."""
        return VideoCompressor(COMPRESSION_SETTINGS)

    @pytest.mark.asyncio
    async def test_compress_if_needed_file_not_found(self, video_compressor):
        """Test compress_if_needed with non-existent file."""
        result = await video_compressor.compress_if_needed("/nonexistent/file.mp4")

        assert result.success is False
        assert "Input video file not found" in result.error_message
        assert result.original_path == "/nonexistent/file.mp4"
        assert result.compressed_path is None

    @pytest.mark.asyncio
    async def test_compress_if_needed_file_under_limit(self, video_compressor):
        """Test compress_if_needed with file under size limit."""
        # Create a small temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            # Write 10MB of data
            data = b"0" * (10 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            result = await video_compressor.compress_if_needed(temp_file.name, 50.0)

            assert result.success is True
            assert result.original_path == temp_file.name
            assert result.compressed_path == temp_file.name  # Same file, no compression
            assert result.error_message is None
            assert abs(result.original_size_mb - 10.0) < 0.1

        # Clean up
        os.unlink(temp_file.name)

    @pytest.mark.asyncio
    async def test_compress_if_needed_file_over_limit_compression_fails(self, video_compressor):
        """Test compress_if_needed with file over limit but compression fails."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            # Write 60MB of data
            data = b"0" * (60 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            # Mock the compress_video method to return False (compression failed)
            with patch.object(video_compressor, "compress_video", return_value=False):
                result = await video_compressor.compress_if_needed(temp_file.name, 50.0)

                assert result.success is False
                assert result.original_path == temp_file.name
                assert result.compressed_path is None
                assert "Compression failed to achieve target size" in result.error_message
                assert abs(result.original_size_mb - 60.0) < 0.1

        # Clean up
        os.unlink(temp_file.name)

    @pytest.mark.asyncio
    async def test_compress_if_needed_compression_exception(self, video_compressor):
        """Test compress_if_needed when compression raises exception."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            # Write 60MB of data
            data = b"0" * (60 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            # Mock the compress_video method to raise an exception
            with patch.object(
                video_compressor, "compress_video", side_effect=Exception("FFmpeg error")
            ):
                result = await video_compressor.compress_if_needed(temp_file.name, 50.0)

                assert result.success is False
                assert result.original_path == temp_file.name
                assert result.compressed_path is None
                assert "Unexpected compression error: FFmpeg error" in result.error_message

        # Clean up
        os.unlink(temp_file.name)

    @pytest.mark.asyncio
    async def test_compress_if_needed_uses_target_size_from_config(self, video_compressor):
        """Test that compress_if_needed uses target_size_mb from config."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            # Write 60MB of data
            data = b"0" * (60 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            # Mock the compress_video method to capture the target size parameter
            compress_video_mock = MagicMock(return_value=True)

            with patch.object(video_compressor, "compress_video", compress_video_mock):
                with patch("utils.video_compression.validate_file_size", return_value=True):
                    await video_compressor.compress_if_needed(temp_file.name, 50.0)

                    # Check that compress_video was called with the target size from config
                    compress_video_mock.assert_called_once()
                    args = compress_video_mock.call_args[0]
                    target_size_used = args[2]  # Third argument is target_size_mb

                    expected_target = COMPRESSION_SETTINGS.get("target_size_mb", 45.0)
                    assert target_size_used == expected_target

        # Clean up
        os.unlink(temp_file.name)

    def test_default_size_limit(self, video_compressor):
        """Test that default size limit is 50MB."""
        # Create a 55MB file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            data = b"0" * (55 * 1024 * 1024)
            temp_file.write(data)
            temp_file.flush()

            # Test with default limit (should need compression)
            needs_compression = should_compress_video(temp_file.name)
            assert needs_compression is True

        # Clean up
        os.unlink(temp_file.name)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
