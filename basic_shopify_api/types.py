from typing import Union

from httpx._types import QueryParamTypes, RequestData

# Joins HTTPX's query or post data
UnionRequestData = Union[QueryParamTypes, RequestData]

# Value for cost/time storage
StoreValue = Union[int, float]

# Container dict setup for cost/time storage
StoreContainer = dict[str, list[StoreValue]]

# Parsed JSON body from response
ParsedBody = dict | None

# Parsed error body from response
ParsedError = Union[dict, Exception] | None

# Time to sleep for deferrer
SleepTime = Union[float, int]
