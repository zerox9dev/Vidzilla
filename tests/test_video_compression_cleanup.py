"""
Unit tests for video compression cleanup and resource management functionality.
"""

import os
import tempfile
import time
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from utils.video_compression import (
    cleanup_temp_files,
    cleanup_temp_directory,
    ensure_temp_directory,
    get_directory_size_mb,
    monitor_disk_usage,
    create_temp_file,
    CompressionContext,
    VideoCompressor,
    check_disk_space,
    InsufficientDiskSpaceError,
    CompressionError
)


class TestCleanupFunctions:
    """Test cleanup utility functions."""
    
    def test_cleanup_temp_files_single_file(self):
        """Test cleaning up a single temporary file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"test content")
        
        # Verify file exists
        assert os.path.exists(temp_path)
        
        # Clean up the file
        cleanup_temp_files(temp_path)
        
        # Verify file is removed
        assert not os.path.exists(temp_path)
    
    def test_cleanup_temp_files_multiple_files(self):
        """Test cleaning up multiple temporary files."""
        temp_files = []
        
        # Create multiple temporary files
        for i in range(3):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_files.append(f.name)
                f.write(f"test content {i}".encode())
        
        # Verify all files exist
        for temp_path in temp_files:
            assert os.path.exists(temp_path)
        
        # Clean up all files
        cleanup_temp_files(*temp_files)
        
        # Verify all files are removed
        for temp_path in temp_files:
            assert not os.path.exists(temp_path)
    
    def test_cleanup_temp_files_nonexistent_file(self):
        """Test cleaning up non-existent files doesn't raise errors."""
        # Should not raise any exceptions
        cleanup_temp_files("/nonexistent/file.mp4")
        cleanup_temp_files(None, "", "/another/nonexistent/file.mp4")
    
    def test_cleanup_temp_files_permission_error(self):
        """Test handling permission errors during cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        # Mock os.unlink to raise PermissionError
        with patch('os.unlink', side_effect=PermissionError("Permission denied")):
            # Should not raise exception, just log error
            cleanup_temp_files(temp_path)
        
        # Clean up the actual file
        os.unlink(temp_path)
    
    def test_cleanup_temp_directory(self):
        """Test cleaning up old files in temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files with different ages
            old_file = os.path.join(temp_dir, "old_file.mp4")
            new_file = os.path.join(temp_dir, "new_file.mp4")
            
            # Create old file and modify its timestamp
            with open(old_file, 'w') as f:
                f.write("old content")
            
            # Set file modification time to 25 hours ago
            old_time = time.time() - (25 * 3600)
            os.utime(old_file, (old_time, old_time))
            
            # Create new file
            with open(new_file, 'w') as f:
                f.write("new content")
            
            # Clean up files older than 24 hours
            cleanup_temp_directory(temp_dir, max_age_hours=24)
            
            # Old file should be removed, new file should remain
            assert not os.path.exists(old_file)
            assert os.path.exists(new_file)
    
    def test_ensure_temp_directory_creation(self):
        """Test creating and validating temporary directory."""
        with tempfile.TemporaryDirectory() as parent_dir:
            temp_dir = os.path.join(parent_dir, "test_temp")
            
            # Directory doesn't exist initially
            assert not os.path.exists(temp_dir)
            
            # Should create directory and return True
            result = ensure_temp_directory(temp_dir)
            assert result is True
            assert os.path.exists(temp_dir)
    
    def test_ensure_temp_directory_write_test(self):
        """Test write permission validation in temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should return True for writable directory
            result = ensure_temp_directory(temp_dir)
            assert result is True
    
    def test_get_directory_size_mb(self):
        """Test calculating directory size in MB."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = os.path.join(temp_dir, "file1.txt")
            file2 = os.path.join(temp_dir, "file2.txt")
            
            with open(file1, 'w') as f:
                f.write("x" * 1024)  # 1KB
            
            with open(file2, 'w') as f:
                f.write("y" * 2048)  # 2KB
            
            size_mb = get_directory_size_mb(temp_dir)
            
            # Should be approximately 3KB = 0.003MB
            assert 0.002 < size_mb < 0.004
    
    def test_monitor_disk_usage(self):
        """Test disk usage monitoring."""
        # Test with current directory
        stats = monitor_disk_usage(".")
        
        # Should return valid statistics
        assert isinstance(stats, dict)
        assert 'total_mb' in stats
        assert 'used_mb' in stats
        assert 'available_mb' in stats
        assert 'usage_percent' in stats
        assert 'warning' in stats
        
        # Values should be reasonable
        assert stats['total_mb'] > 0
        assert stats['available_mb'] >= 0
        assert 0 <= stats['usage_percent'] <= 100


class TestCreateTempFile:
    """Test temporary file creation with resource management."""
    
    def test_create_temp_file_default(self):
        """Test creating temporary file with default parameters."""
        temp_path = create_temp_file()
        
        try:
            # File should exist and have .mp4 extension
            assert os.path.exists(temp_path)
            assert temp_path.endswith('.mp4')
            assert 'compressed_' in os.path.basename(temp_path)
        finally:
            cleanup_temp_files(temp_path)
    
    def test_create_temp_file_custom_params(self):
        """Test creating temporary file with custom parameters."""
        temp_path = create_temp_file(suffix='.avi', prefix='test_')
        
        try:
            # File should exist with custom parameters
            assert os.path.exists(temp_path)
            assert temp_path.endswith('.avi')
            assert 'test_' in os.path.basename(temp_path)
        finally:
            cleanup_temp_files(temp_path)
    
    def test_create_temp_file_custom_directory(self):
        """Test creating temporary file in custom directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = create_temp_file(temp_dir=temp_dir)
            
            try:
                # File should be in the specified directory
                assert os.path.exists(temp_path)
                assert os.path.dirname(temp_path) == temp_dir
            finally:
                cleanup_temp_files(temp_path)
    
    @patch('utils.video_compression.check_disk_space')
    def test_create_temp_file_insufficient_space(self, mock_check_disk_space):
        """Test handling insufficient disk space."""
        mock_check_disk_space.return_value = False
        
        with pytest.raises(InsufficientDiskSpaceError):
            create_temp_file()


class TestCompressionContext:
    """Test compression context manager."""
    
    def test_compression_context_basic(self):
        """Test basic compression context functionality."""
        temp_files = []
        
        # Create some temporary files
        for i in range(2):
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_files.append(f.name)
        
        # Use compression context
        with CompressionContext(temp_files) as ctx:
            # Files should exist during context
            for temp_path in temp_files:
                assert os.path.exists(temp_path)
        
        # Files should be cleaned up after context
        for temp_path in temp_files:
            assert not os.path.exists(temp_path)
    
    def test_compression_context_add_temp_file(self):
        """Test adding temporary files to context."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        with CompressionContext() as ctx:
            ctx.add_temp_file(temp_path)
            assert os.path.exists(temp_path)
        
        # File should be cleaned up
        assert not os.path.exists(temp_path)
    
    def test_compression_context_exception_handling(self):
        """Test context manager with exceptions."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            with CompressionContext([temp_path]) as ctx:
                # Raise an exception inside context
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # File should still be cleaned up despite exception
        assert not os.path.exists(temp_path)


class TestVideoCompressorResourceManagement:
    """Test VideoCompressor resource management features."""
    
    def test_video_compressor_init(self):
        """Test VideoCompressor initialization with temp directory setup."""
        config = {'temp_dir': tempfile.gettempdir()}
        compressor = VideoCompressor(config)
        
        assert 'temp_dir' in compressor.config
        assert os.path.exists(compressor.config['temp_dir'])
    
    def test_video_compressor_invalid_temp_dir(self):
        """Test VideoCompressor with invalid temp directory."""
        config = {'temp_dir': '/invalid/nonexistent/directory'}
        compressor = VideoCompressor(config)
        
        # Should fall back to system temp directory
        assert compressor.config['temp_dir'] == tempfile.gettempdir()
    
    def test_get_compression_context(self):
        """Test getting compression context from VideoCompressor."""
        config = {'temp_dir': tempfile.gettempdir()}
        compressor = VideoCompressor(config)
        
        ctx = compressor.get_compression_context()
        assert isinstance(ctx, CompressionContext)
        assert ctx.temp_files == []
    
    @pytest.mark.asyncio
    async def test_compress_if_needed_file_not_found(self):
        """Test compress_if_needed with non-existent file."""
        config = {'temp_dir': tempfile.gettempdir()}
        compressor = VideoCompressor(config)
        
        result = await compressor.compress_if_needed("/nonexistent/file.mp4")
        
        assert result.success is False
        assert "not found" in result.error_message.lower()
    
    @patch('utils.video_compression.check_ffmpeg_availability')
    @pytest.mark.asyncio
    async def test_compress_if_needed_ffmpeg_not_available(self, mock_check_ffmpeg):
        """Test compress_if_needed when FFmpeg is not available."""
        mock_check_ffmpeg.return_value = False
        
        # Create a temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            temp_video = f.name
            f.write(b"fake video content" * 1000)  # Make it somewhat large
        
        try:
            config = {'temp_dir': tempfile.gettempdir()}
            compressor = VideoCompressor(config)
            
            result = await compressor.compress_if_needed(temp_video)
            
            assert result.success is False
            assert "not available" in result.error_message.lower()
        finally:
            cleanup_temp_files(temp_video)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])