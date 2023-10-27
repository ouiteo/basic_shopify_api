from functools import wraps
from unittest.mock import PropertyMock, patch

from basic_shopify_api import Options, Session
from basic_shopify_api.constants import DEFAULT_MODE


def local_server_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with patch("basic_shopify_api.Session.base_url", new_callable=PropertyMock) as mock_base_url:
            mock_base_url.return_value = "http://localhost:8080"
            return func(*args, **kwargs)

    return wrapper


def async_local_server_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with patch("basic_shopify_api.Session.base_url", new_callable=PropertyMock) as mock_base_url:
            mock_base_url.return_value = "http://localhost:8080"
            return await func(*args, **kwargs)

    return wrapper


def generate_opts_and_sess(mode=DEFAULT_MODE):
    opts = Options()
    opts.mode = mode

    sess = Session("example.myshopify.com", "abc", "123")
    return (sess, opts)
