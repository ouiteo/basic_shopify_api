import json
from pathlib import Path
from typing import Any, Callable, Generator, Optional
from uuid import uuid4

import httpx
import pytest
from pytest_httpx import HTTPXMock

from basic_shopify_api.clients.async_client import AsyncClient
from basic_shopify_api.clients.client import Client
from basic_shopify_api.constants import DEFAULT_MODE
from basic_shopify_api.models import Session
from basic_shopify_api.options import Options

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return False


@pytest.fixture
def error_factory() -> Callable[..., dict]:
    def factory(code: str = "THROTTLED") -> dict:
        return {
            "errors": [{
                "message": "Bad stuff happened",
                "extensions": {"code": code, "requestId": str(uuid4())}
            }]
        }

    return factory


@pytest.fixture
def mocked_graphql(httpx_mock: HTTPXMock) -> Callable[[str], None]:

    def factory(fixture: Optional[str] = None, data: Optional[dict[str, Any]] = None) -> None:
        if fixture:
            data = json.load(open(FIXTURES_DIR / "graphql" / fixture))

        httpx_mock.add_response(
            url="https://example.myshopify.com/admin/api/2020-04/graphql.json",
            method="POST",
            status_code=200,
            json=data
        )

    return factory


@pytest.fixture
def mock_shopify(httpx_mock: HTTPXMock) -> None:
    rest_responses = {
        "shop.json": "get_shop.json",
    }

    graph_responses = {
        b'{"query": "{ shop { name } }", "variables": null}': "post_graphql.json",
    }

    def mock_response(request: httpx.Request):
        return httpx.Response(status_code=200, json={})

        if request.url.path.endswith("graphql.json"):
            key = request.content
            fixture = graph_responses.get(request.content, "")
            path = FIXTURES_DIR / "graphql" / fixture
        else:
            key = request.url.path.split("/")[-1]
            fixture = rest_responses.get(key, "")
            path = FIXTURES_DIR / "rest" / fixture

        if not fixture:
            raise ValueError(f"Unmocked request for {key}")

        with open(path) as fp:
            data = json.load(fp)

        return httpx.Response(status_code=200, json=data)

    # rest: https://example.myshopify.com/admin/api/2020-04/shop.json
    # graphql: https://example.myshopify.com/admin/api/2020-04/graphql.json

    httpx_mock.add_callback(mock_response, url=r"https://example.myshopify.com/.*")


@pytest.fixture
def shopify_client() -> Generator[Client, None, None]:
    opts = Options()
    opts.mode = DEFAULT_MODE
    sess = Session("example.myshopify.com", "abc", "123")

    with Client(sess, opts) as client:
        yield client


@pytest.fixture
def ashopify_client() -> Generator[AsyncClient, None, None]:
    opts = Options()
    opts.mode = DEFAULT_MODE
    sess = Session("example.myshopify.com", "abc", "123")

    yield AsyncClient(sess, opts)
