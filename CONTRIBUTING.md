# Contributing to Vidzilla

Thank you for your interest in contributing to Vidzilla! This document provides guidelines and information for contributors.

## 🚀 Quick Start for Contributors

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   ```

2. **Set up development environment:**
   ```bash
   python -m venv .myebv
   source .myebv/bin/activate  # Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install FFmpeg (required for video processing):**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # Windows - Download from https://ffmpeg.org/
   ```

4. **Set up configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

5. **Run tests to verify setup:**
   ```bash
   python -m pytest tests/ -v
   ```

## 📋 How to Contribute

### 🐛 Reporting Bugs

**Before submitting a bug report:**
- Check existing issues to avoid duplicates
- Test with the latest version
- Gather relevant information

**Bug report should include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Error logs and screenshots
- System information (OS, Python version)
- Bot configuration (without sensitive data)

**Example bug report:**
```markdown
**Bug**: Video compression fails for files >100MB

**Steps to reproduce:**
1. Send Instagram reel URL with large video
2. Bot starts compression process
3. Process fails after timeout

**Expected**: Video should be compressed successfully
**Actual**: Timeout error after 300 seconds

**Error logs:**
```
[Include relevant log entries]
```

**System info:**
- OS: Ubuntu 20.04
- Python: 3.11.2
- FFmpeg: 4.4.2
```

### 💡 Suggesting Features

**Before suggesting a feature:**
- Check if it already exists or is planned
- Consider if it fits the project scope
- Think about implementation complexity

**Feature request should include:**
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Any breaking changes

### 🔧 Code Contributions

#### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes:**
   ```bash
   # Run all tests
   python -m pytest tests/ -v
   
   # Run specific test categories
   python -m pytest tests/test_video_compression.py -v
   python -m pytest tests/test_social_media_fallback_integration.py -v
   
   # Test with coverage
   python -m pytest tests/ --cov=utils --cov=handlers
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add support for new platform XYZ"
   ```

5. **Push and create pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

#### Coding Standards

**Python Style:**
- Follow PEP 8 style guide
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable and function names

**Code Organization:**
```
vidzilla/
├── handlers/           # Bot command handlers
│   ├── social_media/  # Platform-specific handlers
│   └── admin.py       # Admin commands
├── utils/             # Utility functions
│   ├── video_compression.py
│   └── user_management.py
├── tests/             # Test files
└── config.py          # Configuration management
```

**Documentation:**
- Add docstrings to all functions and classes
- Include type hints and parameter descriptions
- Update README.md for user-facing changes
- Add inline comments for complex logic

**Example function:**
```python
async def compress_video(self, input_path: str, output_path: str, 
                        target_size_mb: float = 50.0,
                        progress_callback: Optional[Callable] = None) -> bool:
    """
    Compress video file to target size using FFmpeg.
    
    Args:
        input_path: Path to input video file
        output_path: Path for compressed output
        target_size_mb: Target file size in MB
        progress_callback: Optional callback for progress updates
        
    Returns:
        True if compression successful, False otherwise
        
    Raises:
        CompressionError: If compression fails
        FileNotFoundError: If input file doesn't exist
    """
```

#### Testing Guidelines

**Test Categories:**
- **Unit tests**: Test individual functions
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

**Test Structure:**
```python
class TestVideoCompression:
    """Test video compression functionality."""
    
    @pytest.fixture
    def video_compressor(self):
        """Create VideoCompressor instance for testing."""
        config = {'target_size_mb': 45, 'max_attempts': 3}
        return VideoCompressor(config)
    
    @pytest.mark.asyncio
    async def test_compress_video_success(self, video_compressor):
        """Test successful video compression."""
        # Arrange
        input_file = create_test_video(size_mb=100)
        
        # Act
        result = await video_compressor.compress_if_needed(input_file)
        
        # Assert
        assert result.success is True
        assert result.compressed_size_mb < 50
```

**Test Requirements:**
- All new features must have tests
- Maintain >80% code coverage
- Use meaningful test names
- Test both success and failure cases
- Mock external dependencies

## 🏗️ Project Architecture

### Core Components

**Bot Framework:**
- `bot.py` - Main bot application
- `handlers/` - Command and message handlers
- `config.py` - Configuration management

**Video Processing:**
- `utils/video_compression.py` - FFmpeg integration
- `utils/compression_monitoring.py` - Performance tracking
- `handlers/social_media/` - Platform-specific downloaders

**Data Management:**
- `utils/user_management.py` - User data and MongoDB
- `utils/stripe_utils.py` - Payment processing

### Key Design Principles

1. **Async-First**: All I/O operations are asynchronous
2. **Resource Management**: Automatic cleanup of temporary files
3. **Error Handling**: Comprehensive error recovery
4. **Monitoring**: Built-in performance and health monitoring
5. **Scalability**: Designed for high-traffic deployment

### Adding New Platforms

To add support for a new video platform:

1. **Add platform identifier to config.py:**
   ```python
   PLATFORM_IDENTIFIERS = {
       'newplatform.com': 'NewPlatform',
       # ... existing platforms
   }
   ```

2. **Create platform handler (if needed):**
   ```python
   # handlers/social_media/newplatform.py
   async def process_newplatform(message, bot, url, progress_msg=None):
       # Implementation
   ```

3. **Update detection logic:**
   ```python
   # handlers/social_media/utils.py
   if 'newplatform.com' in url:
       await process_newplatform(message, bot, url, progress_msg)
   ```

4. **Add tests:**
   ```python
   # tests/test_newplatform.py
   class TestNewPlatform:
       # Test cases
   ```

5. **Update documentation:**
   - Add to README.md supported platforms list
   - Update help command text

## 🔍 Code Review Process

### Pull Request Requirements

**Before submitting:**
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No sensitive data in commits
- [ ] Meaningful commit messages

**PR Description should include:**
- Summary of changes
- Related issue numbers
- Testing performed
- Breaking changes (if any)
- Screenshots (for UI changes)

### Review Criteria

**Code Quality:**
- Follows project conventions
- Proper error handling
- Efficient algorithms
- Security considerations

**Testing:**
- Adequate test coverage
- Tests pass consistently
- Edge cases covered

**Documentation:**
- Code is well-documented
- User-facing changes documented
- API changes documented

## 🚀 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version numbers**
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Update documentation**
5. **Create release tag**
6. **Deploy to production**

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Code Reviews**: Pull request discussions

### Development Questions

For development-related questions:
1. Check existing documentation
2. Search closed issues and PRs
3. Ask in GitHub Discussions
4. Create detailed issue if needed

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

### Types of Contributions

We value all types of contributions:
- 🐛 **Bug fixes**
- 🚀 **New features**
- 📚 **Documentation improvements**
- 🧪 **Test coverage**
- 🎨 **UI/UX improvements**
- 🌍 **Translations**
- 📊 **Performance optimizations**

---

**Thank you for contributing to Vidzilla! 🎉**

Every contribution, no matter how small, helps make the project better for everyone.