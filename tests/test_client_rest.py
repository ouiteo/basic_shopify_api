from json import JSONDecodeError

import pytest

from basic_shopify_api import AsyncClient, Client


def test_is_authable(shopify_client: Client) -> None:
    assert shopify_client.is_authable("/admin/api/shop.json")
    assert not shopify_client.is_authable("/oauth/access_token")


def test_is_versionable(shopify_client: Client) -> None:
    assert shopify_client.is_versionable("/admin/api/shop.json")
    assert not shopify_client.is_versionable("/oauth/access_scopes")


def test_version_path(shopify_client: Client) -> None:
    assert shopify_client.version_path("/admin/api/shop.json") == "/admin/api/2020-04/shop.json"
    assert shopify_client.version_path("/admin/api/shop.json", True) == "/admin/api/2020-04/shop.json"


def test_rest_extract_link(shopify_client: Client) -> None:
    page_info = (
        "eyJsYXN0X2lkIjo0MDkwMTQ0ODQ5OTgyLCJsYXN_0X3ZhbHVlIjoiPGh0bWw-PGh0bWw-MiBZZWFyIERWRCwgQmx1LVJheSwgU2F0ZW"
        "xsaXRlLCBhbmQgQ2FibGUgRnVsbCBDaXJjbGXihKIgMTAwJSBWYWx1ZSBCYWNrIFByb2R1Y3QgUHJvdGVjdGlvbiB8IDIgYW4gc3VyI"
        "GxlcyBsZWN0ZXVycyBEVkQgZXQgQmx1LXJheSBldCBwYXNzZXJlbGxlcyBtdWx0aW3DqWRpYXMgYXZlYyByZW1pc2Ugw6AgMTAwICUg"
        "Q2VyY2xlIENvbXBsZXQ8c3VwPk1DPFwvc3VwPjxcL2h0bWw-PFwvaHRtbD4iLCJkaXJlY3Rpb24iOiJuZXh0In0"
    )

    result = shopify_client._rest_extract_link(
        {
            "link": (
                f'<https://example.myshopify.com/admin/api/unstable/products.json?page_info={page_info}>; rel="next"'
            )
        }
    )
    assert result.next == page_info
    assert result.prev is None


def test_rest_return(shopify_client: Client) -> None:
    response = shopify_client.rest("get", "/admin/api/shop.json")

    assert isinstance(response.body, dict)
    assert response.body["shop"]["name"] == "Apple Computers"
    assert response.link.next is None
    assert response.link.prev is None
    assert response.errors is None


def test_rest_error_return(shopify_client: Client) -> None:
    response = shopify_client.rest("get", "/admin/api/error.json")

    assert response.body is None
    assert response.errors == "Not found"

    response = shopify_client.rest("get", "/admin/api/errors.json")

    assert response.body is None
    assert response.errors == "Not found"

    response = shopify_client.rest("get", "/admin/api/decode_error.json")

    assert response.body is None
    assert isinstance(response.errors, JSONDecodeError)


@pytest.mark.asyncio
async def test_rest_async_return(ashopify_client: AsyncClient) -> None:
    response = await ashopify_client.rest("get", "/admin/api/shop.json")
    assert isinstance(response.body, dict)
    assert response.body["shop"]["name"] == "Apple Computers"
    assert response.link.next is None
    assert response.link.prev is None
    assert response.errors is None
