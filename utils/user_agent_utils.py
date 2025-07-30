"""
User Agent utility module for generating fake user agents across the application.
"""

from fake_useragent import UserAgent
import logging

logger = logging.getLogger(__name__)

# Global UserAgent instance
_ua = None

def get_user_agent_instance():
    """Get or create a UserAgent instance with error handling."""
    global _ua
    if _ua is None:
        try:
            _ua = UserAgent()
        except Exception as e:
            logger.warning(f"Failed to initialize UserAgent with real data: {e}")
            # Fallback to a static list if the service is down
            _ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    return _ua

def get_random_user_agent():
    """Get a random user agent string."""
    try:
        ua = get_user_agent_instance()
        return ua.random
    except Exception as e:
        logger.warning(f"Failed to get random user agent: {e}")
        # Fallback user agent
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_chrome_user_agent():
    """Get a Chrome user agent string."""
    try:
        ua = get_user_agent_instance()
        return ua.chrome
    except Exception as e:
        logger.warning(f"Failed to get Chrome user agent: {e}")
        # Fallback Chrome user agent
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_firefox_user_agent():
    """Get a Firefox user agent string."""
    try:
        ua = get_user_agent_instance()
        return ua.firefox
    except Exception as e:
        logger.warning(f"Failed to get Firefox user agent: {e}")
        # Fallback Firefox user agent
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'

def get_safari_user_agent():
    """Get a Safari user agent string."""
    try:
        ua = get_user_agent_instance()
        return ua.safari
    except Exception as e:
        logger.warning(f"Failed to get Safari user agent: {e}")
        # Fallback Safari user agent
        return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'

def get_platform_specific_user_agent(platform_name: str):
    """
    Get a platform-specific user agent.

    Args:
        platform_name: Name of the platform (Instagram, TikTok, etc.)

    Returns:
        Appropriate user agent string for the platform
    """
    platform_lower = platform_name.lower()

    # Platform-specific preferences
    if 'instagram' in platform_lower:
        # Instagram works better with Chrome
        return get_chrome_user_agent()
    elif 'tiktok' in platform_lower:
        # TikTok works better with Chrome
        return get_chrome_user_agent()
    elif 'twitter' in platform_lower or 'x.com' in platform_lower:
        # Twitter/X works well with various browsers
        return get_random_user_agent()
    elif 'facebook' in platform_lower:
        # Facebook works well with Chrome
        return get_chrome_user_agent()
    elif 'youtube' in platform_lower:
        # YouTube works with any browser
        return get_random_user_agent()
    else:
        # Default to random for other platforms
        return get_random_user_agent()

def get_http_headers_with_user_agent(platform_name: str = "", additional_headers: dict = None):
    """
    Get HTTP headers with a fake user agent.

    Args:
        platform_name: Name of the platform for specific user agent selection
        additional_headers: Additional headers to include

    Returns:
        Dictionary of HTTP headers including User-Agent
    """
    headers = {
        'User-Agent': get_platform_specific_user_agent(platform_name)
    }

    if additional_headers:
        headers.update(additional_headers)

    return headers
