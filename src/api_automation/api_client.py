"""
APIClient: a reusable, OOP wrapper around `requests`.

This is the kind of "modular, reusable library" mentioned in the CV -
instead of every test writing raw `requests.get(...)` calls, tests use
this client so that retries, timeouts, headers and logging are handled
in ONE place.
"""
from __future__ import annotations
from typing import Any, Optional
import time

import requests

from src.config.settings import settings
from src.core.logger import get_logger


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
        self.timeout = timeout or settings.api.timeout
        self.max_retries = settings.api.max_retries
        self.session = requests.Session()
        self.logger = get_logger(self.__class__.__name__)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs) -> APIResponseWrapper:
        url = self._url(path)
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info("%s %s (attempt %d/%d)", method, url, attempt, self.max_retries)
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                self.logger.info("-> %s in %.0fms", response.status_code, response.elapsed.total_seconds() * 1000)
                return APIResponseWrapper(response)
            except requests.RequestException as exc:
                last_exc = exc
                self.logger.warning("Request failed (attempt %d/%d): %s", attempt, self.max_retries, exc)
                time.sleep(min(2 ** attempt, 5))

        raise RuntimeError(f"All {self.max_retries} attempts failed for {method} {url}") from last_exc

    def get(self, path: str, params: Optional[dict] = None, **kwargs) -> APIResponseWrapper:
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: Optional[dict] = None, **kwargs) -> APIResponseWrapper:
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: Optional[dict] = None, **kwargs) -> APIResponseWrapper:
        return self._request("PUT", path, json=json, **kwargs)

    def patch(self, path: str, json: Optional[dict] = None, **kwargs) -> APIResponseWrapper:
        return self._request("PATCH", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs) -> APIResponseWrapper:
        return self._request("DELETE", path, **kwargs)
