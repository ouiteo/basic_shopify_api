import pytest

from basic_shopify_api import Config


def test_options_version() -> None:
    opts = Config()
    opts.version = "unstable"
    assert opts.version == "unstable"


def test_options_failed_version() -> None:
    with pytest.raises(ValueError):
        opts = Config()
        opts.version = "oops"


def test_options_type() -> None:
    opts = Config()

    # Public test
    opts.mode = "public"
    assert opts.mode == "public"
    assert opts.is_public is True
    assert opts.is_private is False

    # Private test
    opts.mode = "private"
    assert opts.mode == "private"
    assert opts.is_public is False
    assert opts.is_private is True


def test_options_failed_type() -> None:
    with pytest.raises(ValueError):
        opts = Config()
        opts.mode = "oops"
