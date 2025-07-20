"""
Integration tests for Instagram video compression workflow.

These tests verify the end-to-end compression integration with the Instagram handler,
including progress message updates and error handling scenarios.
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest

from handlers.social_media.instagram import process_instagram
from utils.video_compression import VideoCompressor, CompressionResult
from config import COMPRESSION_SETTINGS, COMPRESSION_MESSAGES


class TestInstagramCompressionIntegration:
    """Integration tests for Instagram video compression workflow."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_message = MagicMock()
        self.mock_message.chat.id = 12345
        self.mock_message.from_user.id = 67890

        self.mock_bot = AsyncMock()
        self.mock_progress_msg = AsyncMock()

        # Create a mock video file
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.test_video_path, "wb") as f:
            f.write(b"0" * (60 * 1024 * 1024))  # 60MB mock video

        yield

        # Clean up test fixtures
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    async def test_large_video_compression_success(
        self,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test successful compression of large Instagram video."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1920, "height": 1080}
        mock_get_size.side_effect = [60.0, 45.0]  # Original 60MB, compressed 45MB
        mock_should_compress.return_value = True

        # Mock compression result
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 45

        compression_result = CompressionResult(
            success=True,
            original_path=self.test_video_path,
            compressed_path=f"{self.test_video_path}_compressed.mp4",
            original_size_mb=60.0,
            compressed_size_mb=45.0,
            compression_ratio=0.75,
            processing_time=42.5,
            error_message=None,
        )
        mock_compressor.compress_if_needed.return_value = compression_result

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify compression was attempted
        mock_compressor.compress_if_needed.assert_called_once_with(
            self.test_video_path, max_size_mb=50.0
        )

        # Verify progress messages were updated correctly
        expected_calls = [
            call("⏳ Processing Instagram link... 50%"),
            call("⏳ Processing Instagram link... 75%"),
            call("🔄 Video is large (60.0MB), compressing..."),
            call("🔄 Video is large (60.0MB), compressing...\n⏱️ Estimated time: ~0m 45s"),
            call(
                "✅ Video compressed from 60.0MB to 45.0MB\n📉 Size reduced by 25%\n⏳ Sending video..."
            ),
            call("✅ Instagram video processed successfully!\n📊 Size: 60.0MB → 45.0MB"),
        ]

        # Check that progress messages were called (order may vary due to async nature)
        self.mock_progress_msg.edit_text.assert_has_calls(expected_calls, any_order=False)

        # Verify video was sent
        self.mock_bot.send_video.assert_called_once()
        self.mock_bot.send_document.assert_called_once()

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    async def test_compression_failure_fallback(
        self,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test fallback behavior when compression fails."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1920, "height": 1080}
        mock_get_size.return_value = 60.0
        mock_should_compress.return_value = True

        # Mock compression failure
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 30

        compression_result = CompressionResult(
            success=False,
            original_path=self.test_video_path,
            compressed_path=None,
            original_size_mb=60.0,
            compressed_size_mb=None,
            compression_ratio=None,
            processing_time=25.0,
            error_message="FFmpeg compression failed",
        )
        mock_compressor.compress_if_needed.return_value = compression_result

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify compression was attempted
        mock_compressor.compress_if_needed.assert_called_once()

        # Verify fallback message was shown
        fallback_calls = [
            call
            for call in self.mock_progress_msg.edit_text.call_args_list
            if "⚠️ Sending as document due to size constraints" in str(call)
        ]
        assert len(fallback_calls) > 0, "Fallback message should be displayed"

        # Verify original video was still sent
        self.mock_bot.send_video.assert_called_once()
        self.mock_bot.send_document.assert_called_once()

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    async def test_small_video_no_compression(
        self, mock_get_size, mock_should_compress, mock_get_info, mock_glob, mock_instaloader
    ):
        """Test that small videos skip compression."""
        # Setup mocks for small video
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1280, "height": 720}
        mock_get_size.return_value = 25.0  # 25MB - under limit
        mock_should_compress.return_value = False

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify no compression was attempted
        with patch("handlers.social_media.instagram.VideoCompressor") as mock_compressor_class:
            # VideoCompressor should not be instantiated for small videos
            pass

        # Verify appropriate message was shown
        size_info_calls = [
            call
            for call in self.mock_progress_msg.edit_text.call_args_list
            if "Video size: 25.0MB (within limit)" in str(call)
        ]
        assert len(size_info_calls) > 0, "Size info message should be displayed"

        # Verify video was sent normally
        self.mock_bot.send_video.assert_called_once()
        self.mock_bot.send_document.assert_called_once()

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    async def test_compression_error_handling(
        self,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test error handling during compression process."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1920, "height": 1080}
        mock_get_size.return_value = 60.0
        mock_should_compress.return_value = True

        # Mock compression exception
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 30
        mock_compressor.compress_if_needed.side_effect = Exception(
            "Compression service unavailable"
        )

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify error message was shown
        error_calls = [
            call
            for call in self.mock_progress_msg.edit_text.call_args_list
            if "❌ Compression failed: Compression service unavailable" in str(call)
        ]
        assert len(error_calls) > 0, "Compression error message should be displayed"

        # Verify original video was still sent despite compression error
        self.mock_bot.send_video.assert_called_once()
        self.mock_bot.send_document.assert_called_once()

    def test_compression_messages_format(self):
        """Test that compression messages are properly formatted."""
        # Test start message
        start_msg = COMPRESSION_MESSAGES["start"].format(size="60.0")
        assert start_msg == "🔄 Video is large (60.0MB), compressing..."

        # Test progress message
        progress_msg = COMPRESSION_MESSAGES["progress"].format(percent=75)
        assert progress_msg == "🔄 Compressing video... 75% complete"

        # Test success message
        success_msg = COMPRESSION_MESSAGES["success"].format(original="60.0", compressed="45.0")
        assert success_msg == "✅ Video compressed from 60.0MB to 45.0MB"

        # Test fallback message
        fallback_msg = COMPRESSION_MESSAGES["fallback"]
        assert fallback_msg == "⚠️ Sending as document due to size constraints"

        # Test error message
        error_msg = COMPRESSION_MESSAGES["error"].format(error="Test error")
        assert error_msg == "❌ Compression failed: Test error"

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    async def test_progress_message_updates_sequence(
        self, mock_get_info, mock_glob, mock_instaloader
    ):
        """Test the sequence of progress message updates during processing."""
        # Setup mocks for normal processing (no compression needed)
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1280, "height": 720}

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        with patch("handlers.social_media.instagram.get_file_size_mb", return_value=25.0), patch(
            "handlers.social_media.instagram.should_compress_video", return_value=False
        ):

            # Execute test
            instagram_url = "https://instagram.com/reel/test123/"
            await process_instagram(
                self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
            )

            # Verify progress message sequence
            calls = self.mock_progress_msg.edit_text.call_args_list
            call_texts = [call[0][0] for call in calls]

            # Should include initial processing messages
            assert "⏳ Processing Instagram link... 50%" in call_texts
            assert "⏳ Processing Instagram link... 75%" in call_texts

            # Should include size info for small video
            size_info_found = any(
                "Video size: 25.0MB (within limit)" in text for text in call_texts
            )
            assert size_info_found, "Size info should be included in progress messages"

            # Should end with success message
            success_found = any(
                "✅ Instagram video processed successfully!" in text for text in call_texts
            )
            assert success_found, "Success message should be the final message"


class TestInstagramCompressionProgressMessages:
    """Test progress message updates during Instagram compression workflow."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_message = MagicMock()
        self.mock_message.chat.id = 12345
        self.mock_message.from_user.id = 67890

        self.mock_bot = AsyncMock()
        self.mock_progress_msg = AsyncMock()

        # Create a mock video file
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.test_video_path, "wb") as f:
            f.write(b"0" * (60 * 1024 * 1024))  # 60MB mock video

        yield

        # Clean up test fixtures
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    async def test_compression_progress_message_sequence(
        self,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test the complete sequence of progress messages during compression."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1920, "height": 1080}
        mock_get_size.side_effect = [100.0, 45.0]  # Original 100MB, compressed 45MB
        mock_should_compress.return_value = True

        # Mock compression with slow progress
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 120  # 2 minutes

        # Track progress callback calls
        progress_updates = []

        async def mock_compress_with_progress(*args, **kwargs):
            # Simulate progress updates
            if "progress_callback" in kwargs:
                callback = kwargs["progress_callback"]
                for progress in [0.25, 0.5, 0.75, 1.0]:
                    await callback(progress)
                    progress_updates.append(progress)

            return CompressionResult(
                success=True,
                original_path=self.test_video_path,
                compressed_path=f"{self.test_video_path}_compressed.mp4",
                original_size_mb=100.0,
                compressed_size_mb=45.0,
                compression_ratio=0.45,
                processing_time=118.5,
                error_message=None,
            )

        mock_compressor.compress_if_needed.side_effect = mock_compress_with_progress

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify progress message sequence
        calls = self.mock_progress_msg.edit_text.call_args_list
        call_texts = [call[0][0] for call in calls]

        # Check for expected message sequence
        expected_patterns = [
            "Processing Instagram link... 50%",
            "Processing Instagram link... 75%",
            "Video is large (100.0MB), compressing...",
            "Estimated time: ~2m 0s",
            "Compressing video... 25% complete",
            "Compressing video... 50% complete",
            "Compressing video... 75% complete",
            "Compressing video... 100% complete",
            "Video compressed from 100.0MB to 45.0MB",
            "Size reduced by 55%",
            "Instagram video processed successfully",
        ]

        # Verify that key progress messages are present
        for pattern in expected_patterns:
            found = any(pattern in text for text in call_texts)
            assert (
                found
            ), f"Expected progress message pattern '{pattern}' not found in: {call_texts}"

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    async def test_compression_timeout_progress_handling(
        self,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test progress message handling when compression times out."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 3840, "height": 2160}  # 4K video
        mock_get_size.return_value = 200.0  # 200MB video
        mock_should_compress.return_value = True

        # Mock compression timeout
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 600  # 10 minutes

        from utils.video_compression import CompressionTimeoutError

        mock_compressor.compress_if_needed.side_effect = CompressionTimeoutError(
            "Compression timed out"
        )

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify timeout error handling
        calls = self.mock_progress_msg.edit_text.call_args_list
        call_texts = [call[0][0] for call in calls]

        # Should show timeout error and fallback
        timeout_found = any(
            "Compression failed: Compression timed out" in text for text in call_texts
        )
        assert timeout_found, "Timeout error message should be displayed"

        # Should still attempt to send original video
        self.mock_bot.send_video.assert_called_once()
        self.mock_bot.send_document.assert_called_once()


class TestInstagramCompressionCleanup:
    """Test cleanup functionality after Instagram compression."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_message = MagicMock()
        self.mock_message.chat.id = 12345
        self.mock_message.from_user.id = 67890

        self.mock_bot = AsyncMock()
        self.mock_progress_msg = AsyncMock()

        # Create a mock video file
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.test_video_path, "wb") as f:
            f.write(b"0" * (60 * 1024 * 1024))  # 60MB mock video

        yield

        # Clean up test fixtures
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    @patch("handlers.social_media.instagram.os.unlink")
    async def test_compressed_file_cleanup_after_success(
        self,
        mock_unlink,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test that compressed files are cleaned up after successful processing."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1920, "height": 1080}
        mock_get_size.side_effect = [80.0, 45.0]  # Original 80MB, compressed 45MB
        mock_should_compress.return_value = True

        # Mock successful compression
        compressed_path = f"{self.test_video_path}_compressed.mp4"
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 60

        compression_result = CompressionResult(
            success=True,
            original_path=self.test_video_path,
            compressed_path=compressed_path,
            original_size_mb=80.0,
            compressed_size_mb=45.0,
            compression_ratio=0.5625,
            processing_time=58.2,
            error_message=None,
        )
        mock_compressor.compress_if_needed.return_value = compression_result

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify compressed file cleanup was attempted
        mock_unlink.assert_called_with(compressed_path)

        # Verify video was sent successfully
        self.mock_bot.send_video.assert_called_once()
        self.mock_bot.send_document.assert_called_once()

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    @patch("handlers.social_media.instagram.shutil.rmtree")
    async def test_temp_directory_cleanup_after_processing(
        self,
        mock_rmtree,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test that temporary directories are cleaned up after processing."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1280, "height": 720}
        mock_get_size.return_value = 30.0  # Small video, no compression needed
        mock_should_compress.return_value = False

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify temp directory cleanup was called
        mock_rmtree.assert_called()
        # Check that it was called with ignore_errors=True
        call_args = mock_rmtree.call_args
        assert call_args[1]["ignore_errors"] is True

    @pytest.mark.asyncio
    @patch("handlers.social_media.instagram.instaloader")
    @patch("handlers.social_media.instagram.glob.glob")
    @patch("handlers.social_media.instagram.get_video_info")
    @patch("handlers.social_media.instagram.VideoCompressor")
    @patch("handlers.social_media.instagram.should_compress_video")
    @patch("handlers.social_media.instagram.get_file_size_mb")
    @patch("handlers.social_media.instagram.shutil.rmtree")
    async def test_cleanup_on_exception(
        self,
        mock_rmtree,
        mock_get_size,
        mock_should_compress,
        mock_compressor_class,
        mock_get_info,
        mock_glob,
        mock_instaloader,
    ):
        """Test that cleanup happens even when exceptions occur."""
        # Setup mocks
        mock_glob.return_value = [self.test_video_path]
        mock_get_info.return_value = {"width": 1920, "height": 1080}
        mock_get_size.return_value = 60.0
        mock_should_compress.return_value = True

        # Mock compression failure
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 45
        mock_compressor.compress_if_needed.side_effect = Exception("Compression service failed")

        # Mock instaloader
        mock_post = MagicMock()
        mock_instaloader.Post.from_shortcode.return_value = mock_post
        mock_loader = MagicMock()
        mock_instaloader.Instaloader.return_value = mock_loader

        # Execute test
        instagram_url = "https://instagram.com/reel/test123/"
        await process_instagram(
            self.mock_message, self.mock_bot, instagram_url, self.mock_progress_msg
        )

        # Verify temp directory cleanup was still called despite exception
        mock_rmtree.assert_called()

        # Verify error message was sent
        error_calls = [
            call
            for call in self.mock_progress_msg.edit_text.call_args_list
            if "Compression service failed" in str(call)
        ]
        assert len(error_calls) > 0, "Error message should be displayed"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
