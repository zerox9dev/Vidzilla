

from fake_useragent import UserAgent
import logging

logger = logging.getLogger(__name__)

# Global UserAgent instance
_ua = None

def get_user_agent_instance():
    global _ua
    if _ua is None:
        try:
            _ua = UserAgent()
        except Exception as e:
            logger.warning(f"Failed to initialize UserAgent with real data: {e}")
            # Fallback to a static list if the service is down
            _ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    return _ua

def _get_user_agent_with_fallback(user_agent_type: str, default_fallback: str):
    try:
        ua = get_user_agent_instance()
        return getattr(ua, user_agent_type)
    except Exception as e:
        logger.warning(f"Failed to get {user_agent_type} user agent: {e}")
        return default_fallback


def get_random_user_agent():
    return _get_user_agent_with_fallback('random', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

def get_chrome_user_agent():
    return _get_user_agent_with_fallback('chrome', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

def get_firefox_user_agent():
    return _get_user_agent_with_fallback('firefox', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0')

def get_safari_user_agent():
    return _get_user_agent_with_fallback('safari', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15')

def get_platform_specific_user_agent(platform_name: str):
    # Use Chrome user agent for all platforms for maximum compatibility
    return get_chrome_user_agent()

def get_http_headers_with_user_agent(platform_name: str = "", additional_headers: dict = None):
    headers = {
        'User-Agent': get_platform_specific_user_agent(platform_name)
    }

    if additional_headers:
        headers.update(additional_headers)

    return headers
