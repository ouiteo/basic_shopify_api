import json
import re
from http import HTTPStatus
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from basic_shopify_api.clients.async_client import AsyncClient
from basic_shopify_api.clients.client import Client

from ..basic_shopify_api.constants import RETRY_HEADER

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_rest_retry(shopify_client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=re.compile(r".*/shop.json"), status_code=HTTPStatus.BAD_GATEWAY.value)

    response = shopify_client.rest(method="get", path="/admin/shop.json")

    assert 502 in response.status
    assert response.retries == shopify_client.options.max_retries


def test_rest_rate_limit(shopify_client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=re.compile(r".*/shop.json"))

    for _ in range(2):
        shopify_client.options.time_store.append(shopify_client.session, shopify_client.options.deferrer.current_time())

    shopify_client.rest(method="get", path="/admin/api/shop.json")

    assert len(shopify_client.options.time_store.all(shopify_client.session)) == 1


def test_graphql_retry(shopify_client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(r".*/graphql.json"),
        status_code=200,
        json=json.load(open(FIXTURES_DIR / "graphql" / "throttle.json")),
    )

    response = shopify_client.graphql(query="{ shop { name } }")

    assert 502 in response.status
    assert response.retries == shopify_client.options.max_retries


def test_graphql_cost_limit(shopify_client: Client) -> None:
    for _ in range(2):
        shopify_client.options.time_store.append(shopify_client.session, shopify_client.options.deferrer.current_time())

    shopify_client.options.cost_store.append(shopify_client.session, 100)

    shopify_client.graphql("{ shop { name } }")

    assert len(shopify_client.options.time_store.all(shopify_client.session)) == 1
    assert len(shopify_client.options.cost_store.all(shopify_client.session)) == 1


def test_rest_retry_header(shopify_client: Client, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(r".*/shop.json"), status_code=HTTPStatus.BAD_GATEWAY.value, headers={RETRY_HEADER: "1.0"}
    )

    response = shopify_client.rest(method="get", path="/admin/shop.json")

    assert 502 in response.status
    assert response.retries == shopify_client.options.max_retries


@pytest.mark.asyncio
async def test_async_rest_retry(ashopify_client: AsyncClient) -> None:
    response = await ashopify_client.rest(
        method="get",
        path="/admin/shop.json",
        headers={"x-test-status": f"{HTTPStatus.BAD_GATEWAY.value} {HTTPStatus.BAD_GATEWAY.phrase}"},
    )
    assert 502 in response.status
    assert response.retries == ashopify_client.options.max_retries


@pytest.mark.asyncio
async def test_async_rest_rate_limit(ashopify_client: AsyncClient) -> None:
    for _ in range(2):
        ashopify_client.options.time_store.append(
            ashopify_client.session, ashopify_client.options.deferrer.current_time()
        )

    await ashopify_client.rest("get", "/admin/api/shop.json")
    assert len(ashopify_client.options.time_store.all(ashopify_client.session)) == 1


@pytest.mark.asyncio
async def test_async_graphql_cost_limit(ashopify_client: AsyncClient) -> None:
    for _ in range(2):
        ashopify_client.options.time_store.append(
            ashopify_client.session, ashopify_client.options.deferrer.current_time()
        )
    ashopify_client.options.cost_store.append(ashopify_client.session, 100)

    await ashopify_client.graphql("{ shop { name } }")
    assert len(ashopify_client.options.time_store.all(ashopify_client.session)) == 1
    assert len(ashopify_client.options.cost_store.all(ashopify_client.session)) == 1
