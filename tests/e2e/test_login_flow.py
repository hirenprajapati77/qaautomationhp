"""
E2E automation tests using Playwright + Page Object Model.

Runs against the-internet.herokuapp.com/login - a free, stable public
sandbox built specifically for QA automation practice. Requires:
    playwright install chromium
before first run.

Demonstrates: "End-to-End (E2E) Testing" and "Playwright" from the CV.
"""
from __future__ import annotations

import pytest
from playwright.sync_api import sync_playwright

from src.config.settings import settings
from src.e2e_automation.pages.login_page import LoginPage

VALID_USER = "tomsmith"
VALID_PASS = "SuperSecretPassword!"


@pytest.fixture
def browser_page():
    with sync_playwright() as p:
        browser = getattr(p, settings.e2e.browser).launch(headless=settings.e2e.headless)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(settings.e2e.default_timeout_ms)
        try:
            yield page
        finally:
            context.close()
            browser.close()


@pytest.mark.e2e
@pytest.mark.herokuapp
class TestLoginFlow:

    def test_successful_login(self, browser_page):
        login_page = LoginPage(browser_page).open()
        login_page.login(VALID_USER, VALID_PASS)

        assert login_page.is_logged_in(), "User should land on the /secure page after valid login"
        message = login_page.get_flash_message()
        assert "You logged into a secure area" in message

    def test_invalid_username_shows_error(self, browser_page):
        login_page = LoginPage(browser_page).open()
        login_page.login("not_a_real_user", VALID_PASS)

        message = login_page.get_flash_message()
        assert "Your username is invalid" in message
        assert not login_page.is_logged_in()

    def test_invalid_password_shows_error(self, browser_page):
        login_page = LoginPage(browser_page).open()
        login_page.login(VALID_USER, "wrong-password")

        message = login_page.get_flash_message()
        assert "Your password is invalid" in message
        assert not login_page.is_logged_in()
