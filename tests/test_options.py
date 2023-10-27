import pytest

from basic_shopify_api import Options


def test_options_version() -> None:
    opts = Options()
    opts.version = "unstable"
    assert opts.version == "unstable"


def test_options_failed_version() -> None:
    with pytest.raises(ValueError):
        opts = Options()
        opts.version = "oops"


def test_options_type() -> None:
    opts = Options()

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
        opts = Options()
        opts.mode = "oops"
