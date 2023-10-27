from basic_shopify_api import Client
from basic_shopify_api.constants import ACCESS_TOKEN_HEADER, ALT_MODE


def test_build_headers(shopify_client: Client) -> None:
    headers = shopify_client._build_headers({})
    assert headers[ACCESS_TOKEN_HEADER] == "123"

    shopify_client.options.mode = ALT_MODE
    headers = shopify_client._build_headers({})
    assert ACCESS_TOKEN_HEADER not in headers


def test_build_request(shopify_client: Client) -> None:
    request = shopify_client._build_request(
        method="get",
        path="/admin/api/shop.json",
        params={"fields": "id"},
    )
    assert "params" in request
    assert "2020-04" in request["url"]

    request = shopify_client._build_request(
        method="post",
        path="/admin/api/shop.json",
        params={"fields": "id"},
    )
    assert "json" in request
