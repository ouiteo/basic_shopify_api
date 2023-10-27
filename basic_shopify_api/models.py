from http import HTTPStatus
from typing import Optional

from httpx._models import Response

from .types import ParsedBody, ParsedError


class Session:
    domain: str
    key: str
    password: str
    secret: str

    def __init__(
        self,
        domain: Optional[str] = None,
        key: Optional[str] = None,
        password: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> None:
        self.domain = domain
        self.key = key
        self.password = password
        self.secret = secret

    @property
    def base_url(self) -> str:
        return f"https://{self.domain}"


class RestLink:
    next: Optional[str]
    prev: Optional[str]

    def __init__(self, next: Optional[str], prev: Optional[str]) -> None:
        self.next = next
        self.prev = prev


class ApiResult:
    response: Response
    status: tuple[HTTPStatus]
    body: ParsedBody
    errors: ParsedError
    retries: int

    def __init__(
        self, response: Response, status: HTTPStatus, body: ParsedBody, errors: ParsedError, retries: int = 0
    ) -> None:
        self.response = response
        self.status = (status,)
        self.body = body
        self.errors = errors
        self.retries = retries


class RestResult(ApiResult):
    link: RestLink

    def __init__(self, link: RestLink, **kwargs) -> None:
        super().__init__(**kwargs)
        self.link = link
