"""
APIClient: a reusable, OOP wrapper around `requests`.

This is the kind of "modular, reusable library" mentioned in the CV -
instead of every test writing raw `requests.get(...)` calls, tests use
this client so that retries, timeouts, headers and logging are handled
in ONE place.
"""
from __future__ import annotations

import time
from typing import Any, Optional

import requests

from src.config.settings import settings
from src.core.logger import get_logger

# Methods that are safe to retry by default (idempotent or conventionally retried).
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class APIClientError(RuntimeError):
    """Raised when the API client exhausts retries or encounters a fatal error."""


class APIResponseWrapper:
    """Small value object so tests assert on a stable, typed interface
    instead of poking at `requests.Response` directly everywhere."""

    def __init__(self, response: requests.Response):
        self.status_code = response.status_code
        self.headers = response.headers
        self.raw = response
        try:
            self.json: Any = response.json()
        except ValueError:
            self.json = None
        self.text = response.text
        self.elapsed_ms = response.elapsed.total_seconds() * 1000


class APIClient:
    """Generic REST client with retry-on-failure and structured logging."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = (base_url or settings.api.base_url).rstrip("/")
        self.timeout = settings.api.timeout if timeout is None else timeout
        self.max_retries = settings.api.max_retries
        self.session = requests.Session()
        self.logger = get_logger(self.__class__.__name__)

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _should_retry(self, method: str, *, idempotent: bool) -> bool:
        return idempotent or method.upper() in _IDEMPOTENT_METHODS

    def _retry_delay_seconds(self, attempt: int, response: requests.Response | None) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), 30.0)
                except ValueError:
                    pass
        return min(2 ** attempt, 5)

    def _request(
        self,
        method: str,
        path: str,
        *,
        idempotent: bool = False,
        **kwargs,
    ) -> APIResponseWrapper:
        url = self._url(path)
        method = method.upper()
        last_exc: Exception | None = None
        can_retry = self._should_retry(method, idempotent=idempotent)

        attempts = self.max_retries if can_retry else 1
        for attempt in range(1, attempts + 1):
            try:
                self.logger.info("%s %s (attempt %d/%d)", method, url, attempt, attempts)
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                elapsed_ms = response.elapsed.total_seconds() * 1000
                self.logger.info("-> %s in %.0fms", response.status_code, elapsed_ms)

                if (
                    can_retry
                    and response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < attempts
                ):
                    delay = self._retry_delay_seconds(attempt, response)
                    self.logger.warning(
                        "Retryable status %s for %s %s; sleeping %.1fs before retry",
                        response.status_code,
                        method,
                        url,
                        delay,
                    )
                    time.sleep(delay)
                    continue

                return APIResponseWrapper(response)
            except requests.RequestException as exc:
                last_exc = exc
                self.logger.warning(
                    "Request failed (attempt %d/%d): %s", attempt, attempts, exc
                )
                if not can_retry or attempt >= attempts:
                    break
                time.sleep(self._retry_delay_seconds(attempt, None))

        raise APIClientError(
            f"All {attempts} attempts failed for {method} {url}"
        ) from last_exc

    def get(self, path: str, params: Optional[dict] = None, **kwargs) -> APIResponseWrapper:
        return self._request("GET", path, params=params, **kwargs)

    def post(
        self,
        path: str,
        json: Optional[dict] = None,
        *,
        idempotent: bool = False,
        **kwargs,
    ) -> APIResponseWrapper:
        return self._request("POST", path, json=json, idempotent=idempotent, **kwargs)

    def put(self, path: str, json: Optional[dict] = None, **kwargs) -> APIResponseWrapper:
        return self._request("PUT", path, json=json, **kwargs)

    def patch(
        self,
        path: str,
        json: Optional[dict] = None,
        *,
        idempotent: bool = False,
        **kwargs,
    ) -> APIResponseWrapper:
        return self._request("PATCH", path, json=json, idempotent=idempotent, **kwargs)

    def delete(self, path: str, **kwargs) -> APIResponseWrapper:
        return self._request("DELETE", path, **kwargs)
