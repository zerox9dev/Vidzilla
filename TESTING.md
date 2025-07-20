# Testing Guide

## 🧪 Test Structure

### Test Categories

1. **Quick Tests** - Fast tests without FFmpeg dependency
2. **Full Tests** - Complete test suite with video compression
3. **Integration Tests** - End-to-end workflow testing
4. **Security Tests** - Code security and vulnerability scanning

## 🚀 Running Tests Locally

### Prerequisites

```bash
# Install FFmpeg (required for video compression tests)
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu

# Install test dependencies
pip install -r requirements-dev.txt
```

### Quick Testing (Recommended for development)

```bash
# Run only fast tests
make test-quick

# Or manually
pytest tests/test_compression_config.py tests/test_size_checking.py -v
```

### Full Test Suite

```bash
# Run all tests with coverage
make test-full

# Or manually
pytest tests/ -v --cov=utils --cov=handlers --cov-report=html
```

### Specific Test Categories

```bash
# Configuration tests
pytest tests/test_compression_config.py -v

# Video compression tests (requires FFmpeg)
pytest tests/test_video_compression.py -v

# Social media integration tests
pytest tests/test_social_media_fallback_integration.py -v

# Progressive compression tests
pytest tests/test_progressive_compression.py -v
```

## 🔧 GitHub Actions Workflows

### 1. Health Check (`health-check.yml`)
- **Trigger**: Every push/PR to main
- **Duration**: ~2 minutes
- **Purpose**: Basic syntax and structure validation
- **No external dependencies**

### 2. Tests (`tests.yml`)
- **Trigger**: Push/PR to main/develop
- **Duration**: ~10 minutes
- **Purpose**: Core functionality testing
- **Includes**: Linting, security checks, quick tests

### 3. Full Tests (`full-tests.yml`)
- **Trigger**: Manual or daily schedule
- **Duration**: ~30 minutes
- **Purpose**: Complete test suite with FFmpeg
- **Includes**: All tests with coverage

### 4. Release (`release.yml`)
- **Trigger**: Git tags (v*)
- **Duration**: ~15 minutes
- **Purpose**: Pre-release validation and Docker build

## 🐛 Troubleshooting Tests

### Common Issues

#### FFmpeg Not Found
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu

# Verify installation
ffmpeg -version
```

#### MongoDB Connection Issues
```bash
# Tests use in-memory MongoDB mock
# No real MongoDB required for testing
```

#### Timeout Issues
```bash
# Run with increased timeout
pytest tests/ --timeout=600

# Or run specific failing test
pytest tests/test_video_compression.py::TestClass::test_method -v
```

#### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/vidzilla

# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Test Environment Variables

Tests use these environment variables (automatically set):

```env
BOT_TOKEN=test_token
RAPIDAPI_KEY=test_key
MONGODB_URI=mongodb://localhost:27017/test
ADMIN_IDS=123456789
```

## 📊 Coverage Reports

### Viewing Coverage

```bash
# Generate HTML coverage report
make test-cov

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Targets

- **Overall**: >80%
- **Utils**: >85%
- **Handlers**: >75%
- **Critical paths**: >90%

## 🔒 Security Testing

### Local Security Checks

```bash
# Run bandit security scanner
bandit -r . --exclude tests/

# Check for vulnerabilities
safety check

# Check for secrets
make security-check
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🚀 Performance Testing

### Compression Performance

```bash
# Test compression with different file sizes
pytest tests/test_video_compression.py::TestVideoFormatsAndSizes -v

# Monitor compression performance
pytest tests/test_compression_monitoring.py -v
```

### Memory Usage

```bash
# Run tests with memory profiling
pytest tests/ --profile

# Monitor memory usage
python -m memory_profiler tests/test_video_compression.py
```

## 📝 Writing New Tests

### Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock

class TestNewFeature:
    """Test new feature functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {'setting': 'value'}
    
    @pytest.mark.asyncio
    async def test_async_function(self, mock_config):
        """Test async functionality."""
        # Arrange
        expected = "result"
        
        # Act
        result = await some_async_function(mock_config)
        
        # Assert
        assert result == expected
    
    def test_sync_function(self):
        """Test synchronous functionality."""
        with patch('module.dependency') as mock_dep:
            mock_dep.return_value = "mocked"
            result = some_sync_function()
            assert result == "expected"
```

### Test Guidelines

1. **Use descriptive test names**
2. **Follow Arrange-Act-Assert pattern**
3. **Mock external dependencies**
4. **Test both success and failure cases**
5. **Include edge cases**
6. **Keep tests independent**
7. **Use fixtures for common setup**

### Mocking Guidelines

```python
# Mock external APIs
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {'data': 'test'}
    # Test implementation

# Mock file operations
@patch('os.path.exists', return_value=True)
@patch('builtins.open', mock_open(read_data='test'))
def test_file_operation(mock_exists):
    # Test implementation

# Mock async operations
@patch('asyncio.sleep')
async def test_async_operation(mock_sleep):
    # Test implementation
```

## 🔄 Continuous Integration

### Workflow Optimization

1. **Cache dependencies** for faster builds
2. **Run quick tests first** to fail fast
3. **Parallel test execution** when possible
4. **Timeout protection** to prevent hanging
5. **Artifact collection** for debugging

### Monitoring Test Health

- Check test duration trends
- Monitor flaky test patterns
- Review coverage changes
- Track failure rates

## 📈 Test Metrics

### Key Metrics to Track

- **Test execution time**
- **Code coverage percentage**
- **Test failure rate**
- **Flaky test count**
- **Security vulnerability count**

### Reporting

- Coverage reports uploaded to Codecov
- Test results in GitHub Actions
- Security reports as artifacts
- Performance metrics in logs

---

**Happy Testing! 🧪**

Remember: Good tests make confident deployments possible.