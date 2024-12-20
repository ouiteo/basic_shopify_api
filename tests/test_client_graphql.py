import pytest
from .utils import generate_opts_and_sess, local_server_session, async_local_server_session
from basic_shopify_api import Client, AsyncClient
from pytest_httpx._httpx_mock import HTTPXMock

@pytest.mark.usefixtures("local_server")
@local_server_session
def test_graphql_return(local_server):
    with Client(*generate_opts_and_sess()) as c:
        response = c.graphql("{ shop { name } }")
        assert isinstance(response.body, dict)
        assert response.body["data"]["shop"]["name"] == "Apple Computers"
        assert response.errors is None


@pytest.mark.asyncio
@pytest.mark.usefixtures("local_server")
@async_local_server_session
async def test_graphql_async_return(local_server):
    async with AsyncClient(*generate_opts_and_sess()) as c:
        response = await c.graphql("{ shop { name } }")
        assert isinstance(response.body, dict)
        assert response.body["data"]["shop"]["name"] == "Apple Computers"
        assert response.errors is None


@pytest.mark.asyncio
@pytest.mark.parametrize("max_limit", [(1), (2)])
@pytest.mark.usefixtures("local_server")
@async_local_server_session
async def test_graphql_pagination_data(local_server, mock_graphql_response, max_limit: int) -> None:
    async with AsyncClient(*generate_opts_and_sess()) as c:
        mock_graphql_response("product.json")
        response = await c.graphql_call_with_pagination("products", "Query", {}, max_limit)
        assert len(response)==max_limit


@pytest.mark.asyncio
@pytest.mark.parametrize("job_status, expected", [("RUNNING", True), ("COMPLETED", False)])
@pytest.mark.usefixtures("local_server")
@async_local_server_session
async def test_is_bulk_job_running(local_server, mock_graphql_response, job_status: str, expected: bool) -> None:
    async with AsyncClient(*generate_opts_and_sess()) as c:
        mock_graphql_response(f"bulk_job_{job_status.lower()}.json")
        response = await c.is_bulk_job_running("QUERY")
        assert response == expected


@pytest.mark.asyncio
@pytest.mark.usefixtures("local_server")
@async_local_server_session
async def test_poll_until_complete(local_server, mock_graphql_response, httpx_mock: HTTPXMock) -> None:
    async with AsyncClient(*generate_opts_and_sess()) as c:
        job_id = "gid://shopify/BulkOperation/1"
        url = "https://download.com"
        mocked_response = "Data Downloaded"
        mock_graphql_response(f"bulk_job_completed.json")
        httpx_mock.add_response(url=url, text=mocked_response)
        response = await c.poll_until_complete(job_id, "QUERY")
        assert response.text == mocked_response
