import asyncio
from typing import Any
from . import ApiCommon
import logging
from ..options import Options
from ..models import ApiResult, RestResult, Session
from ..constants import REST, GRAPHQL
from httpx import AsyncClient as AsyncHttpxClient
from httpx._types import HeaderTypes, QueryParamTypes
from httpx._models import Response
from pathlib import Path
from httpx import Response as HttpxResponse
import jsonlines
from io import BytesIO
import uuid
import httpx


GQL_DIR = Path(__file__).parent.parent / "gql"

logger = logging.getLogger(__name__)

class AsyncClient(AsyncHttpxClient, ApiCommon):
    """
    Sync client, extends the common client and HTTPX.
    """

    def __init__(
        self,
        session: Session,
        options: Options,
        **kwargs
    ):
        """
        Extend HTTPX's init and setup the client with base URL and auth.
        """

        self.session = session
        self.options = options
        super().__init__(
            base_url=self.session.base_url,
            auth=None if self.options.is_public else (self.session.key, self.session.password),
            **kwargs
        )

    async def _rest_rate_limit(self) -> None:
        """
        Handle rate limiting of REST.
        """

        limiting_required = self._rest_rate_limit_required()
        if limiting_required is not False:
            # Rate limit was determined to be required, sleep for X ms
            await self.options.deferrer.asleep(limiting_required)

    async def _graphql_cost_limit(self) -> None:
        """
        Handle cost limiting for GraphQL.
        """

        limiting_required = self._graphql_cost_limit_required()
        if limiting_required is not False:
            # Cost limit was determined to be required, sleep for X ms
            await self.options.deferrer.asleep(limiting_required)

    async def _rest_pre_actions(self, **kwargs) -> None:
        """
        Actions which fire before REST API call.
        """

        # Determine if rate limiting is required and handle it
        await self._rest_rate_limit()
        # Add to the request times
        self.options.time_store.append(self.session, self.options.deferrer.current_time())
        # Run user-defined actions and pass in the request built
        [await meth(self, **kwargs) for meth in self.options.rest_pre_actions]

    async def _graphql_pre_actions(self, **kwargs) -> None:
        """
        Actions which fire before GraphQL API call.
        """

        # Determine if cost limiting is required and handle it
        await self._graphql_cost_limit()
        # Add to the request times
        self.options.time_store.append(self.session, self.options.deferrer.current_time())
        # Run user-defined actions and pass in the request built
        [await meth(self, **kwargs) for meth in self.options.graphql_pre_actions]

    async def _rest_post_actions(self, response: Response, retries: int) -> RestResult:
        """
        Actions which fire after REST API call.
        """

        # Parse the response from HTTPX
        result = self._parse_response(REST, response, retries)
        # Run user-defined actions and pass in the result object
        [await meth(self, result) for meth in self.options.rest_post_actions]
        return result

    async def _graphql_post_actions(self, response: Response, retries: int) -> ApiResult:
        """
        Actions which fire after GraphQL API call.
        """

        # Parse the response from HTTPX
        result = self._parse_response(GRAPHQL, response, retries)
        # Add to the costs
        self._cost_update(result.body)
        # Run user-defined actions and pass in the result object
        [await meth(self, result) for meth in self.options.graphql_post_actions]
        return result

    def _retry_request(meth: callable) -> callable:
        """
        Determine if retry is required.

        If it is, retry the request.
        If not, return the result.
        """

        async def wrapper(*args, **kwargs) -> ApiResult:
            # Get the instance
            inst: AsyncClient = args[0]
            # Get the number of retries so far
            retries = kwargs.get("_retries", 0)
            # Run the call (rest or graphql)
            result: ApiResult = await meth(*args, **kwargs)
            # Get the response and determine if retry is required
            response = result.response
            retry = inst._retry_required(response, retries)

            if retry is not False:
                # Retry is needed, sleep for X ms
                await inst.options.deferrer.asleep(retry)

                # Re-run the request
                kwargs["_retries"] = retries + 1
                inst_meth = getattr(inst, meth.__name__)
                return await inst_meth(*args[1:], **kwargs)
            return result
        return wrapper

    @_retry_request
    async def rest(
        self,
        method: str,
        path: str,
        params: QueryParamTypes = None,
        headers: HeaderTypes = {},
        _retries: int = 0
    ) -> RestResult:
        """
        Fire a REST API call.
        """

        # Dynamically map to HTTPX's method for get/post/put/etc
        meth = getattr(self, method)
        # Build the request based on the method and inputs
        kwargs = self._build_request(method, path, params, headers)
        # Run the pre-actions
        await self._rest_pre_actions(**kwargs)

        # Run the call and post-actions, and return the result
        response = await meth(**kwargs)
        result = await self._rest_post_actions(response, _retries)
        return result

    @_retry_request
    async def graphql(
        self,
        query: str,
        variables: dict = None,
        headers: HeaderTypes = {},
        _retries: int = 0,
    ) -> ApiResult:
        """
        Fire a GraphQL call.
        """

        # Build the request
        kwargs = self._build_request(
            "post",
            "/admin/api/graphql.json",
            {"query": query, "variables": variables},
            headers,
        )
        # Run the pre-actions
        await self._graphql_pre_actions(**kwargs)

        # Run the call and post-actions, and return the result
        response = await self.post(**kwargs)
        result = await self._graphql_post_actions(response, _retries)
        return result

    async def graphql_call_with_pagination(
        self, entity: str, query: str, variables: dict[str, Any] = {}, max_limit: int | None = None
    ) -> list[dict[str, Any]] | None:
        """
        Make a graphql query with pagination

        :param entity: The entity to fetch, e.g "products", "orders"
        :param query: The query to run
        :param variables: The variables to pass to the query

        :return: A list of entity data
        """
        has_next_page = True
        end_cursor: str | None = None
        data = []

        query = self.parse_query(query)
        
        while has_next_page:
            variables["cursor"] = end_cursor

            response = await self.graphql(query, variables)
            if not response.body:
                return None

            entity_path = entity.split(".")
            entity_data = response.body.get("data", {})

            for key in entity_path:
                entity_data = entity_data.get(key, {})
                if not entity_data:
                    return None

            page_info = entity_data.get("pageInfo", {})

            has_next_page = page_info.get("hasNextPage", False)
            end_cursor = page_info.get("endCursor", None)
            entity_data.pop("pageInfo", None)

            for edge in entity_data.get("edges", []):
                data.append(edge.get("node", {}))

            if max_limit and len(data) >= max_limit:
                return data[:max_limit]

        return data
    
    async def is_bulk_job_running(self, job_type: str) -> bool:
        """
        Check if a bulk operation is running
        job_type: "QUERY" or "MUTATION"
        """
        query = open(GQL_DIR / "current_bulkoperation.gql").read() % {"job_type": job_type}
        query = self.parse_query(query)
        response = await self.graphql(query)
        if response.errors:
            raise ValueError(response.errors)
        current_bulk_operation = response.body["data"]["currentBulkOperation"]
        if current_bulk_operation is not None and current_bulk_operation["status"] in ["CREATED", "RUNNING"]:
            return True

        return False

    async def poll_until_complete(self, job_id: str, job_type: str) -> HttpxResponse:
        """
        Poll the bulk operation until it is complete, then return the dataframe
        """
        query = open(GQL_DIR / "current_bulkoperation.gql").read() % {"job_type": job_type}
        query = self.parse_query(query)
        bulk_check_response = await self.graphql(query)

        current_bulk_operation = bulk_check_response.body["data"]["currentBulkOperation"]
        if current_bulk_operation is None or current_bulk_operation["id"] != job_id:
            raise ValueError(f"Job {job_id} not found")

        status = current_bulk_operation["status"]
        objectCount = current_bulk_operation["objectCount"]

        if status in ["CREATED", "RUNNING"]:
            logger.debug(f"Job {job_id} {job_type} is {status}, objectCount:{objectCount}, waiting 1 second")
            await asyncio.sleep(1)
            return await self.poll_until_complete(job_id, job_type)

        elif status == "COMPLETED":
            data_url = current_bulk_operation["url"]
            if data_url:
                async with AsyncHttpxClient() as client:
                    download_response = await client.get(data_url)

                download_response.raise_for_status()
                return download_response

            else:  # data url was None, it means job returned no data
                return HttpxResponse(status_code=204, content=b"")

        raise ValueError(f"Job failed with status {status} [{bulk_check_response.body}]")

    async def run_bulk_operation_query(
        self, sub_query: str, variables: dict[str, Any] = {}, wait: bool = True
    ) -> str | jsonlines.Reader:
        # check if any bulk query job in progress currently
        is_job_running = await self.is_bulk_job_running(job_type="QUERY")
        if is_job_running:
            raise ValueError("Bulk query job already running")

        query = open(GQL_DIR / "query_bulkoperation.gql").read() % {"sub_query": sub_query}

        query = self.parse_query(query)
        response = await self.graphql(query, variables)

        user_errors = (response.body and response.body["data"]["bulkOperationRunQuery"]["userErrors"]) or (
            response.errors
        )
        if user_errors:
            raise ValueError(user_errors)

        job_id: str = response.body["data"]["bulkOperationRunQuery"]["bulkOperation"]["id"]
        if wait:
            response = await self.poll_until_complete(job_id, "QUERY")
            reader = jsonlines.Reader(BytesIO(response.content))
            return reader

        return job_id

    async def run_bulk_operation_mutation(
        self, query: str, rows: list[dict[str, Any]], key: str | None = "input", wait: bool = True
    ) -> str | jsonlines.Reader:
        """
        Run a GQL mutation in bulk

        Supported operations: https://shopify.dev/docs/api/usage/bulk-operations/imports#limitations
        dataframe is expected to have ONLY the fields that you wish to change.
        """
        filename = f"{uuid.uuid4()}.jsonl"
        stage_mutation_query = open(GQL_DIR / "mutation_upload_bulkoperation.gql").read() % {"filename": filename}

        ###################
        # Stage Mutations #
        ###################
        # Get the upload parameters for our mutation file
        stage_mutation_query = self.parse_query(stage_mutation_query)
        stage_mutations_response = await self.graphql(stage_mutation_query)
        if not stage_mutations_response.body:
            raise ValueError(stage_mutations_response.errors)

        stage_mutations_data = stage_mutations_response.body["data"]["stagedUploadsCreate"]["stagedTargets"][0]
        mutations_upload_url = stage_mutations_data["url"]
        mutations_upload_params = stage_mutations_data["parameters"]

        ####################
        # Upload Mutations #
        ####################
        if key is not None:
            rows = [{key: row} for row in rows]
        fp = BytesIO()
        writer = jsonlines.Writer(fp)
        writer.write_all(rows)
        fp.seek(0)

        files = {"file": (filename, fp, "application/octet-stream")}
        data = {param["name"]: (param["value"],) for param in mutations_upload_params}
        staged_upload_path = data["key"][0]

        async with httpx.AsyncClient() as client:
            mutations_upload_response = await client.post(mutations_upload_url, data=data, files=files)

        mutations_upload_response.raise_for_status()

        ######################
        # Run Bulk Operation #
        ######################
        bulk_mutation_query = open(GQL_DIR / "mutation_bulkoperation.gql").read() % {
            "mutation_query": query,
            "staged_upload_path": staged_upload_path,
        }

        # Perform the bulk mutation, and wait for its response
        bulk_mutation_query = self.parse_query(bulk_mutation_query)
        response = await self.graphql(bulk_mutation_query)
        if not response.body:
            raise ValueError(response.errors)

        user_errors = response.body["data"]["bulkOperationRunMutation"]["userErrors"]
        if user_errors:
            raise ValueError(user_errors)

        job_id: str = response.body["data"]["bulkOperationRunMutation"]["bulkOperation"]["id"]

        if not wait:
            return job_id

        response = await self.poll_until_complete(job_id, "MUTATION")
        reader = jsonlines.Reader(BytesIO(response.content))
        return reader

