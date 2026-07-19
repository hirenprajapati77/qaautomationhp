"""
BasePage: the Page Object Model (POM) parent class for Playwright E2E tests.

Every concrete page (LoginPage, DashboardPage, ...) inherits from this and
only adds its own locators + business actions. Common waits/clicks/typing
logic lives here exactly once.
"""
from __future__ import annotations
from playwright.sync_api import Page

from src.config.settings import settings
from src.core.logger import get_logger


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = settings.e2e.base_url
        self.logger = get_logger(self.__class__.__name__)

    def goto(self, path: str = "") -> None:
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        self.logger.info("Navigating to %s", url)
        self.page.goto(url, timeout=settings.e2e.default_timeout_ms)

    def click(self, selector: str) -> None:
        self.logger.info("Click: %s", selector)
        self.page.locator(selector).click(timeout=settings.e2e.default_timeout_ms)

    def fill(self, selector: str, value: str) -> None:
        self.logger.info("Fill: %s", selector)
        self.page.locator(selector).fill(value, timeout=settings.e2e.default_timeout_ms)

    def text_of(self, selector: str) -> str:
        return self.page.locator(selector).inner_text(timeout=settings.e2e.default_timeout_ms)

    def is_visible(self, selector: str, timeout_ms: int | None = None) -> bool:
        """Return True if the locator becomes visible within the timeout."""
        timeout = settings.e2e.default_timeout_ms if timeout_ms is None else timeout_ms
        try:
            self.page.locator(selector).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for(self, selector: str, state: str = "visible") -> None:
        self.page.locator(selector).wait_for(state=state, timeout=settings.e2e.default_timeout_ms)

    def wait_for_hidden(self, selector: str) -> None:
        self.page.locator(selector).wait_for(state="hidden", timeout=settings.e2e.default_timeout_ms)
