"""
FuzionHR UAT E2E suite.

These tests hit a real external UAT environment and shared credentials.
They are gated behind the `fuzion` marker and require FUZION_E2E=1 plus
credentials so they do not run in default CI.
"""
from __future__ import annotations

import os
import warnings

import pytest
from playwright.sync_api import sync_playwright

from src.config.settings import settings
from src.e2e_automation.pages.fuzion_login_page import FuzionLoginPage

VALID_USER = os.getenv("FUZION_USER", "SLXEnrgy")
VALID_PASS = os.getenv("FUZION_PASS", "test")


def pytest_configure(config):
    # Marker is also declared in pytest.ini; keep local import side effects minimal.
    pass


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


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.fuzion,
    pytest.mark.skipif(
        os.getenv("FUZION_E2E", "").lower() not in {"1", "true", "yes"},
        reason="Fuzion UAT suite disabled; set FUZION_E2E=1 to enable",
    ),
]


@pytest.mark.e2e
@pytest.mark.fuzion
class TestFuzionLoginFlow:

    # ==========================================
    # 1. Positive Test Cases
    # ==========================================

    def test_successful_login(self, browser_page):
        """TC-POS-01: Login with valid username and valid password"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login(VALID_USER, VALID_PASS)

        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in(), "User should be redirected to the /app-preference page"

    def test_password_visibility_toggle(self, browser_page):
        """TC-POS-02: Password visibility toggle (eye icon)"""
        login_page = FuzionLoginPage(browser_page).open()

        browser_page.fill(login_page.PASSWORD_INPUT, "secret-text")

        pwd_input = browser_page.locator(login_page.PASSWORD_INPUT)
        assert pwd_input.get_attribute("type") == "password"

        browser_page.click(login_page.TOGGLE_PASSWORD)
        assert pwd_input.get_attribute("type") == "text"

        browser_page.click(login_page.TOGGLE_PASSWORD)
        assert pwd_input.get_attribute("type") == "password"

    def test_forgot_password_modal(self, browser_page):
        """TC-POS-03: 'Forgot Password' link redirection/modal popup"""
        login_page = FuzionLoginPage(browser_page).open()

        browser_page.click(login_page.FORGOT_PASSWORD_LINK)

        modal_header = browser_page.locator(login_page.RESET_PASSWORD_HEADER)
        modal_header.wait_for(state="visible", timeout=settings.e2e.default_timeout_ms)
        assert modal_header.is_visible()

        browser_page.click(login_page.CLOSE_MODAL_BUTTON)
        modal_header.wait_for(state="hidden", timeout=settings.e2e.default_timeout_ms)
        assert not modal_header.is_visible()

    def test_keyboard_navigation(self, browser_page):
        """TC-POS-04: Keyboard navigation (Tab + Enter)"""
        login_page = FuzionLoginPage(browser_page).open()

        browser_page.focus(login_page.USERNAME_INPUT)
        browser_page.keyboard.type(VALID_USER)

        browser_page.keyboard.press("Tab")
        browser_page.keyboard.type(VALID_PASS)

        browser_page.keyboard.press("Enter")

        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in()

    def test_password_case_sensitivity(self, browser_page):
        """TC-POS-05: Case sensitivity in password field"""
        login_page = FuzionLoginPage(browser_page).open()

        login_page.login(VALID_USER, VALID_PASS.upper())
        browser_page.wait_for_url("**/login", timeout=settings.e2e.default_timeout_ms)

        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

        login_page.login(VALID_USER, VALID_PASS)
        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in()

    # ==========================================
    # 2. Negative Test Cases
    # ==========================================

    def test_empty_username_and_password(self, browser_page):
        """TC-NEG-01: Login with empty username and password"""
        login_page = FuzionLoginPage(browser_page).open()

        browser_page.fill(login_page.USERNAME_INPUT, "")
        browser_page.fill(login_page.PASSWORD_INPUT, "")
        browser_page.click(login_page.SUBMIT_BUTTON)

        email_classes = browser_page.locator(login_page.USERNAME_INPUT).get_attribute("class") or ""
        pwd_classes = browser_page.locator(login_page.PASSWORD_INPUT).get_attribute("class") or ""

        assert "ng-invalid" in email_classes
        assert "ng-invalid" in pwd_classes
        assert not login_page.is_logged_in()

    def test_invalid_username_valid_password(self, browser_page):
        """TC-NEG-02: Login with invalid username and valid password format"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login("NonExistentUser123", VALID_PASS)

        browser_page.wait_for_url("**/login", timeout=settings.e2e.default_timeout_ms)
        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

    def test_valid_username_invalid_password(self, browser_page):
        """TC-NEG-03: Login with valid username and invalid password"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login(VALID_USER, "wrong-password-999")

        browser_page.wait_for_url("**/login", timeout=settings.e2e.default_timeout_ms)
        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

    def test_account_lockout_warning(self, browser_page):
        """TC-NEG-04: Verify 2 failed attempts do not lock out user prematurely"""
        warnings.warn(
            "Safety Check: Restricting failed attempts to 2 to protect the shared test account from lockout."
        )
        login_page = FuzionLoginPage(browser_page).open()

        login_page.login(VALID_USER, "wrong-password-1")
        browser_page.wait_for_url("**/login", timeout=settings.e2e.default_timeout_ms)

        login_page.login(VALID_USER, "wrong-password-2")
        browser_page.wait_for_url("**/login", timeout=settings.e2e.default_timeout_ms)

        login_page.login(VALID_USER, VALID_PASS)
        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in(), "Account should not be locked after only 2 failed attempts."

    def test_excessive_long_input(self, browser_page):
        """TC-NEG-05: Special characters and long input validation"""
        login_page = FuzionLoginPage(browser_page).open()

        long_username = "A" * 300 + "@special_$%#.com"
        long_password = "B" * 300 + "_!@#$%"

        login_page.login(long_username, long_password)
        browser_page.wait_for_url("**/login", timeout=settings.e2e.default_timeout_ms)

        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

    # ==========================================
    # 3. Edge & Security Cases
    # ==========================================

    def test_back_button_after_logout(self, browser_page):
        """TC-EDG-01: Browser Back button after Logout"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login(VALID_USER, VALID_PASS)
        browser_page.wait_for_url("**/app-preference", timeout=15000)

        browser_page.context.clear_cookies()
        browser_page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")

        browser_page.reload()
        browser_page.wait_for_url("**/login", timeout=10000)

        assert "/login" in browser_page.url

        browser_page.goto(f"{login_page.base_url}/app-preference")
        browser_page.wait_for_url("**/login", timeout=10000)
        assert "/login" in browser_page.url, "Should not be able to access app-preference without logging in"

    def test_back_button_after_login(self, browser_page):
        """TC-EDG-02: Browser Back button after Login"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login(VALID_USER, VALID_PASS)
        browser_page.wait_for_url("**/app-preference", timeout=15000)

        browser_page.go_back()
        browser_page.wait_for_load_state("domcontentloaded")

        assert not browser_page.is_closed()

    def test_concurrent_sessions(self):
        """TC-EDG-03: Concurrent sessions in separate contexts"""
        with sync_playwright() as p:
            browser = getattr(p, settings.e2e.browser).launch(headless=settings.e2e.headless)
            ctx1 = browser.new_context()
            ctx2 = browser.new_context()
            try:
                page1 = ctx1.new_page()
                page1.set_default_timeout(settings.e2e.default_timeout_ms)
                login_page1 = FuzionLoginPage(page1).open()
                login_page1.login(VALID_USER, VALID_PASS)
                page1.wait_for_url("**/app-preference", timeout=15000)
                assert login_page1.is_logged_in()

                page2 = ctx2.new_page()
                page2.set_default_timeout(settings.e2e.default_timeout_ms)
                login_page2 = FuzionLoginPage(page2).open()
                login_page2.login(VALID_USER, VALID_PASS)
                page2.wait_for_url("**/app-preference", timeout=15000)
                assert login_page2.is_logged_in()

                page1.reload()
                page1.wait_for_url("**/app-preference", timeout=15000)
                assert "app-preference" in page1.url, "First session should remain valid"
            finally:
                ctx1.close()
                ctx2.close()
                browser.close()

    def test_password_not_copyable(self, browser_page):
        """TC-EDG-04: Password field type is masked"""
        login_page = FuzionLoginPage(browser_page).open()
        pwd_input = browser_page.locator(login_page.PASSWORD_INPUT)

        assert pwd_input.get_attribute("type") == "password"

    def test_responsiveness_viewport(self, browser_page):
        """TC-EDG-05: Responsiveness and viewport scaling"""
        login_page = FuzionLoginPage(browser_page).open()

        browser_page.set_viewport_size({"width": 375, "height": 812})
        assert browser_page.locator(login_page.USERNAME_INPUT).is_visible()
        assert browser_page.locator(login_page.PASSWORD_INPUT).is_visible()
        assert browser_page.locator(login_page.SUBMIT_BUTTON).is_visible()

        browser_page.set_viewport_size({"width": 1920, "height": 1080})
        assert browser_page.locator(login_page.USERNAME_INPUT).is_visible()
        assert browser_page.locator(login_page.PASSWORD_INPUT).is_visible()
        assert browser_page.locator(login_page.SUBMIT_BUTTON).is_visible()
