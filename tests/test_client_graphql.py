import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from basic_shopify_api import AsyncClient, Client

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_graphql_return(shopify_client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://example.myshopify.com/admin/api/2020-04/graphql.json",
        method="POST",
        status_code=200,
        json=json.load(open(FIXTURES_DIR / "graphql" / "post_graphql.json")),
    )

    response = shopify_client.graphql("{ shop { name } }")

    assert isinstance(response.body, dict)
    assert response.body["data"]["shop"]["name"] == "Apple Computers"
    assert response.errors is None


@pytest.mark.asyncio
async def test_graphql_async_return(ashopify_client: AsyncClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://example.myshopify.com/admin/api/2020-04/graphql.json",
        method="POST",
        status_code=200,
        json=json.load(open(FIXTURES_DIR / "graphql" / "post_graphql.json")),
    )

    response = await ashopify_client.graphql("{ shop { name } }")

    assert isinstance(response.body, dict)
    assert response.body["data"]["shop"]["name"] == "Apple Computers"
    assert response.errors is None
