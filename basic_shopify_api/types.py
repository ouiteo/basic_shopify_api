from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Union

from httpx._types import QueryParamTypes, RequestData

if TYPE_CHECKING:
    from .clients.async_client import AsyncClient
    from .clients.client import Client
    from .models import ApiResult, RestResult

# Joins HTTPX's query or post data
UnionRequestData = Union[QueryParamTypes, RequestData]

# Value for cost/time storage
StoreValue = Union[int, float]

# Container dict setup for cost/time storage
StoreContainer = dict[str, list[StoreValue]]

# Parsed JSON body from response
ParsedBody = dict[str, Any] | None

# Parsed error body from response
ParsedError = Union[dict, Exception] | None

# Time to sleep for deferrer
SleepTime = Union[float, int]

# Callbacks for rest or graphql calls
PreCallback = Union[
    Callable[["Client", Optional[Any]], None],
    Callable[["AsyncClient", Optional[Any]], Awaitable[None]],
]

PostCallback = Union[
    Callable[["Client", "ApiResult | RestResult", Optional[Any]], None],
    Callable[["AsyncClient", "ApiResult | RestResult", Optional[Any]], Awaitable[None]],
]
