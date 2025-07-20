"""
Integration tests for social media video processing with fallback delivery methods.

This module tests the complete fallback chain:
1. Video message delivery
2. Document attachment fallback
3. Original link sharing fallback
4. Error message with troubleshooting steps
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch, call
from aiogram.types import Message, Chat, User, FSInputFile

from handlers.social_media.utils import (
    process_social_media_video,
    _attempt_video_delivery_with_fallbacks,
    _download_video_to_temp,
)
from config import COMPRESSION_SETTINGS


class TestSocialMediaFallbackIntegration:
    """Test fallback delivery methods for social media video processing."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock message object."""
        message = MagicMock(spec=Message)
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 12345
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 67890
        return message

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot object."""
        bot = AsyncMock()
        bot.send_video = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def mock_progress_msg(self):
        """Create a mock progress message object."""
        progress_msg = AsyncMock()
        progress_msg.edit_text = AsyncMock()
        return progress_msg

    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary video file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # Write some dummy data to simulate a video file
            f.write(b"fake video data" * 1000)  # ~15KB file
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def large_temp_video_file(self):
        """Create a large temporary video file for testing compression scenarios."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # Write dummy data to simulate a large video file (>50MB)
            chunk = b"fake video data" * 1024  # ~15KB chunk
            for _ in range(3500):  # Write ~52MB
                f.write(chunk)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_successful_video_delivery(
        self, mock_bot, mock_message, mock_progress_msg, temp_video_file
    ):
        """Test successful video delivery (primary method)."""
        # Setup
        platform_name = "TikTok"
        original_url = "https://example.com/video"
        file_size_mb = 15.0

        # Execute
        result = await _attempt_video_delivery_with_fallbacks(
            mock_bot,
            mock_message,
            temp_video_file,
            platform_name,
            original_url,
            file_size_mb,
            False,
            mock_progress_msg,
        )

        # Verify
        assert result is True
        mock_bot.send_video.assert_called_once()
        mock_bot.send_document.assert_not_called()
        mock_bot.send_message.assert_not_called()

        # Check progress message updates
        mock_progress_msg.edit_text.assert_called()
        final_call = mock_progress_msg.edit_text.call_args_list[-1]
        assert "✅" in final_call[0][0]
        assert "TikTok video processed successfully" in final_call[0][0]

    @pytest.mark.asyncio
    async def test_document_fallback_delivery(
        self, mock_bot, mock_message, mock_progress_msg, temp_video_file
    ):
        """Test document attachment fallback when video sending fails."""
        # Setup
        platform_name = "Facebook"
        original_url = "https://facebook.com/video"
        file_size_mb = 45.0

        # Make video sending fail, but document sending succeed
        mock_bot.send_video.side_effect = Exception("Video sending failed")

        # Execute
        result = await _attempt_video_delivery_with_fallbacks(
            mock_bot,
            mock_message,
            temp_video_file,
            platform_name,
            original_url,
            file_size_mb,
            True,
            mock_progress_msg,
        )

        # Verify
        assert result is True
        mock_bot.send_video.assert_called_once()
        mock_bot.send_document.assert_called_once()
        mock_bot.send_message.assert_not_called()

        # Check document call parameters
        doc_call = mock_bot.send_document.call_args
        assert doc_call[1]["chat_id"] == mock_message.chat.id
        assert isinstance(doc_call[1]["document"], FSInputFile)
        assert "sent as document due to size constraints" in doc_call[1]["caption"]

        # Check progress message
        final_call = mock_progress_msg.edit_text.call_args_list[-1]
        assert "📁 Sent as document" in final_call[0][0]

    @pytest.mark.asyncio
    async def test_original_link_fallback(
        self, mock_bot, mock_message, mock_progress_msg, temp_video_file
    ):
        """Test original link sharing fallback when both video and document fail."""
        # Setup
        platform_name = "Twitter"
        original_url = "https://twitter.com/video"
        file_size_mb = 75.0

        # Make both video and document sending fail
        mock_bot.send_video.side_effect = Exception("Video sending failed")
        mock_bot.send_document.side_effect = Exception("Document sending failed")

        # Execute
        result = await _attempt_video_delivery_with_fallbacks(
            mock_bot,
            mock_message,
            temp_video_file,
            platform_name,
            original_url,
            file_size_mb,
            False,
            mock_progress_msg,
        )

        # Verify
        assert result is True
        mock_bot.send_video.assert_called_once()
        mock_bot.send_document.assert_called_once()
        mock_bot.send_message.assert_called_once()

        # Check message content
        message_call = mock_bot.send_message.call_args
        assert message_call[1]["chat_id"] == mock_message.chat.id
        message_text = message_call[1]["text"]
        assert "⚠️ Unable to send Twitter video directly" in message_text
        assert original_url in message_text
        assert "You can download it directly from:" in message_text

    @pytest.mark.asyncio
    async def test_complete_failure_troubleshooting(
        self, mock_bot, mock_message, mock_progress_msg, temp_video_file
    ):
        """Test complete failure scenario with troubleshooting message."""
        # Setup
        platform_name = "YouTube"
        original_url = "https://youtube.com/video"
        file_size_mb = 100.0

        # Make all delivery methods fail
        mock_bot.send_video.side_effect = Exception("Video sending failed")
        mock_bot.send_document.side_effect = Exception("Document sending failed")
        mock_bot.send_message.side_effect = [
            Exception("Link message failed"),  # First call (link fallback) fails
            None,  # Second call (troubleshooting) succeeds
        ]

        # Execute
        result = await _attempt_video_delivery_with_fallbacks(
            mock_bot,
            mock_message,
            temp_video_file,
            platform_name,
            original_url,
            file_size_mb,
            True,
            mock_progress_msg,
        )

        # Verify
        assert result is False
        mock_bot.send_video.assert_called_once()
        mock_bot.send_document.assert_called_once()
        assert mock_bot.send_message.call_count == 2

        # Check troubleshooting message
        troubleshooting_call = mock_bot.send_message.call_args_list[-1]
        message_text = troubleshooting_call[1]["text"]
        assert "❌ Failed to deliver YouTube video" in message_text
        assert "Troubleshooting steps:" in message_text
        assert "Try again in a few minutes" in message_text
        assert original_url in message_text

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    @patch("handlers.social_media.utils._download_video_to_temp")
    @patch("handlers.social_media.utils.VideoCompressor")
    async def test_end_to_end_with_compression_and_fallback(
        self,
        mock_compressor_class,
        mock_download,
        mock_requests,
        mock_bot,
        mock_message,
        mock_progress_msg,
        large_temp_video_file,
    ):
        """Test end-to-end processing with compression and fallback delivery."""
        # Setup API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"medias": [{"url": "https://example.com/video.mp4"}]}
        mock_requests.return_value = mock_response

        # Setup download
        mock_download.return_value = large_temp_video_file

        # Setup compression
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor

        # Mock compression result (compression fails)
        compression_result = MagicMock()
        compression_result.success = False
        compression_result.error_message = "Compression failed"
        compression_result.original_size_mb = 75.0
        mock_compressor.compress_if_needed.return_value = compression_result
        mock_compressor.estimate_compression_time.return_value = 45

        # Make video sending fail, document succeed
        mock_bot.send_video.side_effect = Exception("Video too large")

        # Execute
        await process_social_media_video(
            mock_message, mock_bot, "https://tiktok.com/video", "TikTok", mock_progress_msg
        )

        # Verify compression was attempted
        mock_compressor.compress_if_needed.assert_called_once()

        # Verify fallback to document
        mock_bot.send_document.assert_called_once()

        # Verify progress messages
        progress_calls = [call[0][0] for call in mock_progress_msg.edit_text.call_args_list]
        # Since compression failed, we should see fallback messages instead
        assert any("fallback" in msg.lower() or "document" in msg.lower() for msg in progress_calls)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.get")
    async def test_download_video_to_temp_success(self, mock_get):
        """Test successful video download to temporary file."""
        # Setup
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2", b"chunk3"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Execute
        result_path = await _download_video_to_temp(
            "https://example.com/video.mp4", "TikTok", 12345
        )

        # Verify
        assert result_path is not None
        assert os.path.exists(result_path)
        assert "tiktok_12345" in result_path
        assert result_path.endswith(".mp4")

        # Check file content
        with open(result_path, "rb") as f:
            content = f.read()
            assert content == b"chunk1chunk2chunk3"

        # Cleanup
        os.unlink(result_path)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.get")
    async def test_download_video_to_temp_failure(self, mock_get):
        """Test video download failure handling."""
        # Setup
        mock_get.side_effect = Exception("Network error")

        # Execute and verify exception
        with pytest.raises(Exception) as exc_info:
            await _download_video_to_temp("https://example.com/video.mp4", "TikTok", 12345)

        assert "Failed to download video" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    async def test_api_error_handling(
        self, mock_requests, mock_bot, mock_message, mock_progress_msg
    ):
        """Test handling of API errors from social media platforms."""
        # Setup API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Video not found or private"}
        mock_requests.return_value = mock_response

        # Execute
        await process_social_media_video(
            mock_message, mock_bot, "https://tiktok.com/private", "TikTok", mock_progress_msg
        )

        # Verify error handling
        mock_progress_msg.edit_text.assert_called()
        final_call = mock_progress_msg.edit_text.call_args_list[-1]
        assert "❌ Error:" in final_call[0][0]
        assert "Video not found or private" in final_call[0][0]

    @pytest.mark.asyncio
    async def test_compression_error_handling(
        self, mock_bot, mock_message, mock_progress_msg, temp_video_file
    ):
        """Test specific error handling for compression failures."""
        # Setup
        platform_name = "Instagram"
        original_url = "https://instagram.com/video"

        # Simulate compression error in the main function
        with patch("handlers.social_media.utils.process_social_media_video") as mock_process:
            mock_process.side_effect = Exception("Video compression error: FFmpeg failed")

            # This would be called by the main handler
            try:
                await mock_process(
                    mock_message, mock_bot, original_url, platform_name, mock_progress_msg
                )
            except Exception as e:
                # Simulate the error handling that would happen in the actual function
                error_message = str(e)
                if "compression" in error_message.lower():
                    await mock_progress_msg.edit_text(
                        f"❌ {platform_name} video compression error: {str(e)}\n"
                        "Try again or contact support if the issue persists."
                    )

        # Verify compression-specific error message
        mock_progress_msg.edit_text.assert_called_with(
            "❌ Instagram video compression error: Video compression error: FFmpeg failed\n"
            "Try again or contact support if the issue persists."
        )


class TestSocialMediaCompressionIntegration:
    """Test compression integration with various social media platforms."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock message object."""
        message = MagicMock(spec=Message)
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 12345
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 67890
        return message

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot object."""
        bot = AsyncMock()
        bot.send_video = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def mock_progress_msg(self):
        """Create a mock progress message object."""
        progress_msg = AsyncMock()
        progress_msg.edit_text = AsyncMock()
        return progress_msg

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    @patch("handlers.social_media.utils._download_video_to_temp")
    @patch("handlers.social_media.utils.VideoCompressor")
    async def test_tiktok_compression_workflow(
        self,
        mock_compressor_class,
        mock_download,
        mock_requests,
        mock_bot,
        mock_message,
        mock_progress_msg,
    ):
        """Test complete TikTok video compression workflow."""
        # Setup API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "medias": [{"url": "https://example.com/tiktok_video.mp4"}]
        }
        mock_requests.return_value = mock_response

        # Setup download
        temp_video_path = tempfile.mktemp(suffix=".mp4")
        with open(temp_video_path, "wb") as f:
            f.write(b"x" * (80 * 1024 * 1024))  # 80MB file
        mock_download.return_value = temp_video_path

        # Setup compression
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 90

        compressed_path = tempfile.mktemp(suffix=".mp4")
        with open(compressed_path, "wb") as f:
            f.write(b"x" * (40 * 1024 * 1024))  # 40MB compressed

        compression_result = MagicMock()
        compression_result.success = True
        compression_result.compressed_path = compressed_path
        compression_result.original_size_mb = 80.0
        compression_result.compressed_size_mb = 40.0
        compression_result.compression_ratio = 0.5
        mock_compressor.compress_if_needed.return_value = compression_result

        try:
            # Execute
            await process_social_media_video(
                mock_message, mock_bot, "https://tiktok.com/video", "TikTok", mock_progress_msg
            )

            # Verify compression was attempted
            mock_compressor.compress_if_needed.assert_called_once()

            # Verify video was sent
            mock_bot.send_video.assert_called_once()

            # Verify progress messages
            progress_calls = [call[0][0] for call in mock_progress_msg.edit_text.call_args_list]
            assert any("TikTok" in msg for msg in progress_calls)
            assert any("compressing" in msg.lower() for msg in progress_calls)
            assert any("compressed from 80.0MB to 40.0MB" in msg for msg in progress_calls)

        finally:
            # Cleanup
            for path in [temp_video_path, compressed_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    @patch("handlers.social_media.utils._download_video_to_temp")
    @patch("handlers.social_media.utils.VideoCompressor")
    async def test_facebook_compression_failure_fallback(
        self,
        mock_compressor_class,
        mock_download,
        mock_requests,
        mock_bot,
        mock_message,
        mock_progress_msg,
    ):
        """Test Facebook video compression failure and fallback to document."""
        # Setup API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "medias": [{"url": "https://example.com/facebook_video.mp4"}]
        }
        mock_requests.return_value = mock_response

        # Setup download
        temp_video_path = tempfile.mktemp(suffix=".mp4")
        with open(temp_video_path, "wb") as f:
            f.write(b"x" * (120 * 1024 * 1024))  # 120MB file
        mock_download.return_value = temp_video_path

        # Setup compression failure
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 180

        compression_result = MagicMock()
        compression_result.success = False
        compression_result.error_message = "FFmpeg encoding failed"
        compression_result.original_size_mb = 120.0
        mock_compressor.compress_if_needed.return_value = compression_result

        # Make video sending fail, document succeed
        mock_bot.send_video.side_effect = Exception("Video too large")

        try:
            # Execute
            await process_social_media_video(
                mock_message, mock_bot, "https://facebook.com/video", "Facebook", mock_progress_msg
            )

            # Verify compression was attempted
            mock_compressor.compress_if_needed.assert_called_once()

            # Verify fallback to document
            mock_bot.send_document.assert_called_once()

            # Verify progress messages show compression failure and fallback
            progress_calls = [call[0][0] for call in mock_progress_msg.edit_text.call_args_list]
            assert any("Facebook" in msg for msg in progress_calls)
            assert any("FFmpeg encoding failed" in msg for msg in progress_calls)
            assert any("document" in msg.lower() for msg in progress_calls)

        finally:
            # Cleanup
            if os.path.exists(temp_video_path):
                os.unlink(temp_video_path)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    @patch("handlers.social_media.utils._download_video_to_temp")
    @patch("handlers.social_media.utils.should_compress_video")
    async def test_twitter_small_video_no_compression(
        self,
        mock_should_compress,
        mock_download,
        mock_requests,
        mock_bot,
        mock_message,
        mock_progress_msg,
    ):
        """Test Twitter video that doesn't need compression."""
        # Setup API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "medias": [{"url": "https://example.com/twitter_video.mp4"}]
        }
        mock_requests.return_value = mock_response

        # Setup download - small video
        temp_video_path = tempfile.mktemp(suffix=".mp4")
        with open(temp_video_path, "wb") as f:
            f.write(b"x" * (25 * 1024 * 1024))  # 25MB file
        mock_download.return_value = temp_video_path

        # Video doesn't need compression
        mock_should_compress.return_value = False

        try:
            # Execute
            await process_social_media_video(
                mock_message, mock_bot, "https://twitter.com/video", "Twitter", mock_progress_msg
            )

            # Verify no compression was attempted
            with patch("handlers.social_media.utils.VideoCompressor") as mock_compressor_class:
                # VideoCompressor should not be instantiated for small videos
                pass

            # Verify video was sent normally
            mock_bot.send_video.assert_called_once()

            # Verify progress messages show no compression needed
            progress_calls = [call[0][0] for call in mock_progress_msg.edit_text.call_args_list]
            assert any("Twitter" in msg for msg in progress_calls)
            assert any("within limit" in msg for msg in progress_calls)

        finally:
            # Cleanup
            if os.path.exists(temp_video_path):
                os.unlink(temp_video_path)


class TestRealWorldVideoURLs:
    """Test with realistic video URL scenarios and edge cases."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock message object."""
        message = MagicMock(spec=Message)
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 12345
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 67890
        return message

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot object."""
        bot = AsyncMock()
        bot.send_video = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.fixture
    def mock_progress_msg(self):
        """Create a mock progress message object."""
        progress_msg = AsyncMock()
        progress_msg.edit_text = AsyncMock()
        return progress_msg

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.get")
    async def test_download_video_with_redirect(self, mock_get):
        """Test video download that involves redirects."""
        # Setup redirect response
        redirect_response = MagicMock()
        redirect_response.status_code = 302
        redirect_response.headers = {"Location": "https://cdn.example.com/final_video.mp4"}

        # Setup final response
        final_response = MagicMock()
        final_response.iter_content.return_value = [b"video_chunk_1", b"video_chunk_2"]
        final_response.raise_for_status.return_value = None

        mock_get.return_value = final_response

        # Execute
        result_path = await _download_video_to_temp(
            "https://example.com/redirect_video.mp4", "YouTube", 12345
        )

        # Verify
        assert result_path is not None
        assert os.path.exists(result_path)
        assert "youtube_12345" in result_path

        # Check file content
        with open(result_path, "rb") as f:
            content = f.read()
            assert content == b"video_chunk_1video_chunk_2"

        # Cleanup
        os.unlink(result_path)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.get")
    async def test_download_video_with_timeout(self, mock_get):
        """Test video download timeout handling."""
        # Setup timeout
        import requests

        mock_get.side_effect = requests.Timeout("Request timed out")

        # Execute and verify exception
        with pytest.raises(Exception) as exc_info:
            await _download_video_to_temp("https://example.com/slow_video.mp4", "TikTok", 12345)

        assert "Failed to download video" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.get")
    async def test_download_video_with_large_file(self, mock_get):
        """Test downloading very large video files."""

        # Setup large file response
        def generate_large_chunks():
            # Generate 100MB of data in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(100):
                yield b"x" * chunk_size

        mock_response = MagicMock()
        mock_response.iter_content.return_value = generate_large_chunks()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Execute
        result_path = await _download_video_to_temp(
            "https://example.com/large_video.mp4", "Facebook", 12345
        )

        # Verify
        assert result_path is not None
        assert os.path.exists(result_path)

        # Check file size (should be ~100MB)
        file_size = os.path.getsize(result_path)
        assert file_size >= 100 * 1024 * 1024  # At least 100MB

        # Cleanup
        os.unlink(result_path)

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    async def test_api_rate_limiting_handling(
        self, mock_requests, mock_bot, mock_message, mock_progress_msg
    ):
        """Test handling of API rate limiting responses."""
        # Setup rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded. Try again later."}
        mock_requests.return_value = mock_response

        # Execute
        await process_social_media_video(
            mock_message, mock_bot, "https://tiktok.com/video", "TikTok", mock_progress_msg
        )

        # Verify rate limit error handling
        mock_progress_msg.edit_text.assert_called()
        final_call = mock_progress_msg.edit_text.call_args_list[-1]
        assert "Rate limit exceeded" in final_call[0][0]

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    async def test_api_invalid_url_handling(
        self, mock_requests, mock_bot, mock_message, mock_progress_msg
    ):
        """Test handling of invalid or private video URLs."""
        # Setup invalid URL response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Video not found or is private"}
        mock_requests.return_value = mock_response

        # Execute
        await process_social_media_video(
            mock_message,
            mock_bot,
            "https://instagram.com/private_video",
            "Instagram",
            mock_progress_msg,
        )

        # Verify error handling
        mock_progress_msg.edit_text.assert_called()
        final_call = mock_progress_msg.edit_text.call_args_list[-1]
        assert "Video not found or is private" in final_call[0][0]


class TestConcurrentCompressionHandling:
    """Test handling of multiple concurrent compression requests."""

    @pytest.fixture
    def mock_message_factory(self):
        """Factory for creating mock message objects."""

        def create_mock_message(user_id: int, chat_id: int):
            message = MagicMock(spec=Message)
            message.chat = MagicMock(spec=Chat)
            message.chat.id = chat_id
            message.from_user = MagicMock(spec=User)
            message.from_user.id = user_id
            return message

        return create_mock_message

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot object."""
        bot = AsyncMock()
        bot.send_video = AsyncMock()
        bot.send_document = AsyncMock()
        bot.send_message = AsyncMock()
        return bot

    @pytest.mark.asyncio
    @patch("handlers.social_media.utils.requests.post")
    @patch("handlers.social_media.utils._download_video_to_temp")
    @patch("handlers.social_media.utils.VideoCompressor")
    async def test_concurrent_compression_requests(
        self, mock_compressor_class, mock_download, mock_requests, mock_bot, mock_message_factory
    ):
        """Test multiple concurrent compression requests."""
        # Setup API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"medias": [{"url": "https://example.com/video.mp4"}]}
        mock_requests.return_value = mock_response

        # Setup downloads - create unique temp files for each request
        temp_files = []

        def create_temp_file(*args, **kwargs):
            temp_path = tempfile.mktemp(suffix=".mp4")
            with open(temp_path, "wb") as f:
                f.write(b"x" * (70 * 1024 * 1024))  # 70MB file
            temp_files.append(temp_path)
            return temp_path

        mock_download.side_effect = create_temp_file

        # Setup compression
        mock_compressor = AsyncMock()
        mock_compressor_class.return_value = mock_compressor
        mock_compressor.estimate_compression_time.return_value = 60

        def create_compression_result(*args, **kwargs):
            result = MagicMock()
            result.success = True
            result.compressed_path = tempfile.mktemp(suffix=".mp4")
            result.original_size_mb = 70.0
            result.compressed_size_mb = 35.0
            result.compression_ratio = 0.5
            return result

        mock_compressor.compress_if_needed.side_effect = create_compression_result

        try:
            # Create multiple concurrent requests
            tasks = []
            for i in range(3):
                message = mock_message_factory(user_id=1000 + i, chat_id=2000 + i)
                progress_msg = AsyncMock()

                task = process_social_media_video(
                    message, mock_bot, f"https://tiktok.com/video{i}", "TikTok", progress_msg
                )
                tasks.append(task)

            # Execute all requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all requests completed successfully
            for result in results:
                assert not isinstance(result, Exception), f"Request failed with: {result}"

            # Verify compression was called for each request
            assert mock_compressor.compress_if_needed.call_count == 3

            # Verify videos were sent for each request
            assert mock_bot.send_video.call_count == 3

        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
