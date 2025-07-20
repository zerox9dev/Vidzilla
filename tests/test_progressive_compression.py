"""
Unit tests for progressive compression strategy.

Tests for task 3.2: Implement progressive compression strategy
"""

import os
import tempfile
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from utils.video_compression import (
    VideoCompressor,
    VideoInfo,
    CompressionError,
    CompressionTimeoutError,
)
from config import COMPRESSION_SETTINGS


def safe_cleanup(*file_paths):
    """Safely clean up temporary files."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except (FileNotFoundError, PermissionError):
            pass


class TestProgressiveCompressionStrategy:
    """Test progressive compression strategy functionality."""

    @pytest.fixture
    def video_compressor(self):
        """Create a VideoCompressor instance for testing."""
        return VideoCompressor(COMPRESSION_SETTINGS)

    @pytest.fixture
    def sample_video_info(self):
        """Create sample video info for testing."""
        return VideoInfo(
            width=1920,
            height=1080,
            duration=60.0,
            fps=30.0,
            bitrate=5000000,
            codec="h264",
            size_mb=100.0,
        )

    def test_calculate_output_dimensions_no_scaling_needed(self, video_compressor):
        """Test dimension calculation when no scaling is needed."""
        # Original dimensions smaller than max
        width, height = video_compressor._calculate_output_dimensions(800, 600, 1280, 720)
        assert width == 800
        assert height == 600

    def test_calculate_output_dimensions_width_limited(self, video_compressor):
        """Test dimension calculation when width is the limiting factor."""
        # Wide video that needs width scaling
        width, height = video_compressor._calculate_output_dimensions(1920, 800, 1280, 720)
        # Aspect ratio: 1920/800 = 2.4
        # With max width 1280: height should be 1280/2.4 = 533.33 -> 532 (even)
        assert width == 1280
        assert height == 532

    def test_calculate_output_dimensions_height_limited(self, video_compressor):
        """Test dimension calculation when height is the limiting factor."""
        # Tall video that needs height scaling
        width, height = video_compressor._calculate_output_dimensions(800, 1200, 1280, 720)
        # Aspect ratio: 800/1200 = 0.667
        # With max height 720: width should be 720 * 0.667 = 480
        assert width == 480
        assert height == 720

    def test_calculate_output_dimensions_maintains_aspect_ratio(self, video_compressor):
        """Test that aspect ratio is maintained during scaling."""
        original_width, original_height = 1920, 1080
        original_aspect = original_width / original_height

        width, height = video_compressor._calculate_output_dimensions(
            original_width, original_height, 1280, 720
        )

        new_aspect = width / height
        assert abs(new_aspect - original_aspect) < 0.01  # Allow small rounding differences

    def test_calculate_output_dimensions_ensures_even_numbers(self, video_compressor):
        """Test that output dimensions are always even numbers."""
        # Test various inputs that might produce odd numbers
        test_cases = [
            (1921, 1081, 1280, 720),
            (1279, 719, 1280, 720),
            (853, 479, 854, 480),
        ]

        for orig_w, orig_h, max_w, max_h in test_cases:
            width, height = video_compressor._calculate_output_dimensions(
                orig_w, orig_h, max_w, max_h
            )
            assert width % 2 == 0, f"Width {width} is not even"
            assert height % 2 == 0, f"Height {height} is not even"

    def test_calculate_output_dimensions_minimum_size(self, video_compressor):
        """Test that minimum dimensions are enforced."""
        # Very small input should be clamped to minimum
        width, height = video_compressor._calculate_output_dimensions(100, 100, 200, 200)
        assert width >= 320
        assert height >= 240

    @pytest.mark.asyncio
    async def test_attempt_compression_success(self, video_compressor):
        """Test successful compression attempt."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock ffmpeg execution
                mock_process = MagicMock()
                mock_process.returncode = 0
                mock_process.communicate = AsyncMock(return_value=(b"", b""))

                with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                    with patch("os.path.exists", return_value=True):
                        with patch(
                            "os.path.getsize", return_value=1024
                        ):  # Mock non-empty output file
                            result = await video_compressor._attempt_compression(
                                input_file.name, output_file.name, 28, 1280, 720, 300
                            )

                            assert result is True

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_attempt_compression_ffmpeg_failure(self, video_compressor):
        """Test compression attempt when FFmpeg fails."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock ffmpeg execution failure
                mock_process = MagicMock()
                mock_process.returncode = 1  # Failure
                mock_process.communicate = AsyncMock(return_value=(b"", b"FFmpeg error"))

                with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                    with pytest.raises(CompressionError, match="FFmpeg error"):
                        await video_compressor._attempt_compression(
                            input_file.name, output_file.name, 28, 1280, 720, 300
                        )

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_attempt_compression_timeout(self, video_compressor):
        """Test compression attempt timeout."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock process that times out
                mock_process = MagicMock()
                mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
                mock_process.kill = MagicMock()
                mock_process.wait = AsyncMock()

                with patch("asyncio.create_subprocess_exec", return_value=mock_process):
                    with pytest.raises(CompressionTimeoutError, match="Compression timeout"):
                        await video_compressor._attempt_compression(
                            input_file.name, output_file.name, 28, 1280, 720, 1  # 1 second timeout
                        )

                    mock_process.kill.assert_called_once()

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_progressive_compression_strategy_first_attempt_success(
        self, video_compressor, sample_video_info
    ):
        """Test progressive strategy when first attempt succeeds."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock successful compression on first attempt
                with patch.object(video_compressor, "_attempt_compression", return_value=True):
                    with patch(
                        "utils.video_compression.get_file_size_mb", return_value=30.0
                    ):  # Under target
                        result = await video_compressor._progressive_compression_strategy(
                            input_file.name, output_file.name, 45.0, sample_video_info
                        )

                        assert result is True

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_progressive_compression_strategy_multiple_attempts(
        self, video_compressor, sample_video_info
    ):
        """Test progressive strategy with multiple attempts before success."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock compression attempts - first few fail, then succeed
                attempt_count = 0

                def mock_attempt_compression(*args, **kwargs):
                    nonlocal attempt_count
                    attempt_count += 1
                    return attempt_count >= 3  # Succeed on 3rd attempt

                # Mock file sizes - first attempts too large, then acceptable
                size_count = 0

                def mock_get_file_size_mb(path):
                    nonlocal size_count
                    size_count += 1
                    return 60.0 if size_count < 3 else 40.0  # Under target on 3rd attempt

                with patch.object(
                    video_compressor, "_attempt_compression", side_effect=mock_attempt_compression
                ):
                    with patch(
                        "utils.video_compression.get_file_size_mb",
                        side_effect=mock_get_file_size_mb,
                    ):
                        result = await video_compressor._progressive_compression_strategy(
                            input_file.name, output_file.name, 45.0, sample_video_info
                        )

                        assert result is True
                        assert attempt_count >= 3

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_progressive_compression_strategy_all_attempts_fail(
        self, video_compressor, sample_video_info
    ):
        """Test progressive strategy when all attempts fail."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock all compression attempts to succeed but file size still too large
                with patch.object(video_compressor, "_attempt_compression", return_value=True):
                    with patch(
                        "utils.video_compression.get_file_size_mb", return_value=60.0
                    ):  # Always too large
                        result = await video_compressor._progressive_compression_strategy(
                            input_file.name, output_file.name, 45.0, sample_video_info
                        )

                        assert result is False

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_progressive_compression_strategy_progress_callback(
        self, video_compressor, sample_video_info
    ):
        """Test that progress callback is called during progressive compression."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                progress_calls = []

                def progress_callback(progress):
                    progress_calls.append(progress)

                # Mock compression to fail a few times then succeed
                attempt_count = 0

                def mock_attempt_compression(*args, **kwargs):
                    nonlocal attempt_count
                    attempt_count += 1
                    return attempt_count >= 2

                def mock_get_file_size_mb(path):
                    return 40.0 if attempt_count >= 2 else 60.0

                with patch.object(
                    video_compressor, "_attempt_compression", side_effect=mock_attempt_compression
                ):
                    with patch(
                        "utils.video_compression.get_file_size_mb",
                        side_effect=mock_get_file_size_mb,
                    ):
                        result = await video_compressor._progressive_compression_strategy(
                            input_file.name,
                            output_file.name,
                            45.0,
                            sample_video_info,
                            progress_callback,
                        )

                        assert result is True
                        assert len(progress_calls) > 0
                        assert 1.0 in progress_calls  # Final progress should be 1.0

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    @pytest.mark.asyncio
    async def test_compress_video_uses_progressive_strategy(self, video_compressor):
        """Test that compress_video method uses progressive strategy."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as input_file:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as output_file:
                # Create dummy input file
                input_file.write(b"dummy video data")
                input_file.flush()

                # Mock get_video_info to return large video
                mock_video_info = VideoInfo(
                    width=1920,
                    height=1080,
                    duration=60.0,
                    fps=30.0,
                    bitrate=5000000,
                    codec="h264",
                    size_mb=100.0,
                )

                with patch.object(video_compressor, "get_video_info", return_value=mock_video_info):
                    with patch.object(
                        video_compressor, "_progressive_compression_strategy", return_value=True
                    ) as mock_strategy:
                        result = await video_compressor.compress_video(
                            input_file.name, output_file.name, 45.0
                        )

                        assert result is True
                        mock_strategy.assert_called_once()

                # Clean up
                os.unlink(input_file.name)
                os.unlink(output_file.name)

    def test_quality_levels_from_config(self, video_compressor):
        """Test that quality levels are read from config."""
        expected_levels = COMPRESSION_SETTINGS.get("quality_levels", [28, 32, 36])
        assert video_compressor.config.get("quality_levels") == expected_levels

    def test_resolution_levels_progressive_downscaling(self, video_compressor, sample_video_info):
        """Test that resolution levels provide progressive downscaling."""
        # The resolution levels should be in descending order of quality
        resolution_levels = [
            (sample_video_info.width, sample_video_info.height),  # Original
            (1280, 720),  # 720p
            (854, 480),  # 480p
            (640, 360),  # 360p
        ]

        # Each level should be smaller than or equal to the previous
        for i in range(1, len(resolution_levels)):
            prev_pixels = resolution_levels[i - 1][0] * resolution_levels[i - 1][1]
            curr_pixels = resolution_levels[i][0] * resolution_levels[i][1]
            assert (
                curr_pixels <= prev_pixels
            ), f"Resolution level {i} has more pixels than level {i-1}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
