import pytest
import warnings
from playwright.sync_api import sync_playwright

from src.config.settings import settings
from src.e2e_automation.pages.fuzion_login_page import FuzionLoginPage

VALID_USER = "SLXEnrgy"
VALID_PASS = "test"


@pytest.fixture
def browser_page():
    with sync_playwright() as p:
        browser = getattr(p, settings.e2e.browser).launch(headless=settings.e2e.headless)
        page = browser.new_page()
        page.set_default_timeout(30000)
        yield page
        browser.close()


@pytest.mark.e2e
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
        
        # Fill password
        browser_page.fill(login_page.PASSWORD_INPUT, "secret-text")
        
        # Verify initial state is masked (type="password")
        pwd_input = browser_page.locator(login_page.PASSWORD_INPUT)
        assert pwd_input.get_attribute("type") == "password"

        # Click visibility toggle eye icon
        browser_page.click(login_page.TOGGLE_PASSWORD)
        
        # Verify state is unmasked (type="text")
        assert pwd_input.get_attribute("type") == "text"

        # Click toggle again
        browser_page.click(login_page.TOGGLE_PASSWORD)
        
        # Verify state is masked again
        assert pwd_input.get_attribute("type") == "password"

    def test_forgot_password_modal(self, browser_page):
        """TC-POS-03: 'Forgot Password' link redirection/modal popup"""
        login_page = FuzionLoginPage(browser_page).open()
        
        # Click Forgot Password? link
        browser_page.click(login_page.FORGOT_PASSWORD_LINK)
        
        # Assert modal pops up and header is visible
        modal_header = browser_page.locator(login_page.RESET_PASSWORD_HEADER)
        assert modal_header.is_visible()

        # Click the Close button
        browser_page.click(login_page.CLOSE_MODAL_BUTTON)
        browser_page.wait_for_timeout(1000) # Wait for animation
        
        # Assert modal is closed
        assert not modal_header.is_visible()

    def test_keyboard_navigation(self, browser_page):
        """TC-POS-04: Keyboard navigation (Tab + Enter)"""
        login_page = FuzionLoginPage(browser_page).open()
        
        # Click email field to focus
        browser_page.focus(login_page.USERNAME_INPUT)
        browser_page.keyboard.type(VALID_USER)
        
        # Tab to password field
        browser_page.keyboard.press("Tab")
        browser_page.keyboard.type(VALID_PASS)
        
        # Press Enter directly to submit (standard form submit)
        browser_page.keyboard.press("Enter")
        
        # Verify redirect
        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in()

    def test_password_case_sensitivity(self, browser_page):
        """TC-POS-05: Case sensitivity in password field"""
        login_page = FuzionLoginPage(browser_page).open()
        
        # Attempt login with wrong case
        login_page.login(VALID_USER, VALID_PASS.upper()) # "TEST"
        browser_page.wait_for_timeout(2000)
        
        # Assert login fails (stays on login page)
        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

        # Attempt login with correct case
        login_page.login(VALID_USER, VALID_PASS) # "test"
        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in()

    # ==========================================
    # 2. Negative Test Cases
    # ==========================================

    def test_empty_username_and_password(self, browser_page):
        """TC-NEG-01: Login with empty username and password"""
        login_page = FuzionLoginPage(browser_page).open()
        
        # Clear fields and click login
        browser_page.fill(login_page.USERNAME_INPUT, "")
        browser_page.fill(login_page.PASSWORD_INPUT, "")
        browser_page.click(login_page.SUBMIT_BUTTON)
        
        # Assert form validation state
        email_classes = browser_page.locator(login_page.USERNAME_INPUT).get_attribute("class")
        pwd_classes = browser_page.locator(login_page.PASSWORD_INPUT).get_attribute("class")
        
        assert "ng-invalid" in email_classes
        assert "ng-invalid" in pwd_classes
        assert not login_page.is_logged_in()

    def test_invalid_username_valid_password(self, browser_page):
        """TC-NEG-02: Login with invalid username and valid password format"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login("NonExistentUser123", VALID_PASS)
        
        browser_page.wait_for_timeout(3000)
        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

    def test_valid_username_invalid_password(self, browser_page):
        """TC-NEG-03: Login with valid username and invalid password"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login(VALID_USER, "wrong-password-999")
        
        browser_page.wait_for_timeout(3000)
        assert not login_page.is_logged_in()
        assert "/login" in browser_page.url

    def test_account_lockout_warning(self, browser_page):
        """TC-NEG-04: Verify 2 failed attempts do not lock out user prematurely"""
        warnings.warn("Safety Check: Restricting failed attempts to 2 to protect the shared test account from lockout.")
        login_page = FuzionLoginPage(browser_page).open()
        
        # 1st failed attempt
        login_page.login(VALID_USER, "wrong-password-1")
        browser_page.wait_for_timeout(2000)
        
        # 2nd failed attempt
        login_page.login(VALID_USER, "wrong-password-2")
        browser_page.wait_for_timeout(2000)
        
        # Attempt successful login to confirm account remains active
        login_page.login(VALID_USER, VALID_PASS)
        browser_page.wait_for_url("**/app-preference", timeout=15000)
        assert login_page.is_logged_in(), "Account should not be locked after only 2 failed attempts."

    def test_excessive_long_input(self, browser_page):
        """TC-NEG-05: Special characters and long input validation"""
        login_page = FuzionLoginPage(browser_page).open()
        
        long_username = "A" * 300 + "@special_$%#.com"
        long_password = "B" * 300 + "_!@#$%"
        
        login_page.login(long_username, long_password)
        browser_page.wait_for_timeout(3000)
        
        # Assert page doesn't crash and login fails safely
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
        
        # Simulate logout by clearing all storage and cookies
        browser_page.context.clear_cookies()
        browser_page.evaluate("window.localStorage.clear(); window.sessionStorage.clear();")
        
        # Reload the page
        browser_page.reload()
        browser_page.wait_for_url("**/login", timeout=10000)
        
        # Verify we are on the login page
        assert "/login" in browser_page.url
        
        # Try to navigate back to app-preference
        browser_page.goto("https://uat.fuzionhr.com/app-preference")
        browser_page.wait_for_url("**/login", timeout=10000)
        assert "/login" in browser_page.url, "Should not be able to access app-preference without logging in"

    def test_back_button_after_login(self, browser_page):
        """TC-EDG-02: Browser Back button after Login"""
        login_page = FuzionLoginPage(browser_page).open()
        login_page.login(VALID_USER, VALID_PASS)
        browser_page.wait_for_url("**/app-preference", timeout=15000)
        
        # Press back button
        browser_page.go_back()
        browser_page.wait_for_timeout(2000)
        
        # Verify it stays active or redirects properly without crash
        assert not browser_page.is_closed()

    def test_concurrent_sessions(self, pytestconfig):
        """TC-EDG-03: Concurrent sessions in separate contexts"""
        with sync_playwright() as p:
            browser = getattr(p, settings.e2e.browser).launch(headless=settings.e2e.headless)
            
            # Session 1
            ctx1 = browser.new_context()
            page1 = ctx1.new_page()
            page1.set_default_timeout(30000)
            login_page1 = FuzionLoginPage(page1).open()
            login_page1.login(VALID_USER, VALID_PASS)
            page1.wait_for_url("**/app-preference", timeout=15000)
            assert login_page1.is_logged_in()

            # Session 2
            ctx2 = browser.new_context()
            page2 = ctx2.new_page()
            page2.set_default_timeout(30000)
            login_page2 = FuzionLoginPage(page2).open()
            login_page2.login(VALID_USER, VALID_PASS)
            page2.wait_for_url("**/app-preference", timeout=15000)
            assert login_page2.is_logged_in()

            # Refresh Session 1 to verify it is still valid
            page1.reload()
            page1.wait_for_url("**/app-preference", timeout=15000)
            assert "app-preference" in page1.url, "First session should remain valid"
            
            browser.close()

    def test_password_not_copyable(self, browser_page):
        """TC-EDG-04: Password field type is masked"""
        login_page = FuzionLoginPage(browser_page).open()
        pwd_input = browser_page.locator(login_page.PASSWORD_INPUT)
        
        # Verify it is of type password, which prevents clear-text clipboard copies
        assert pwd_input.get_attribute("type") == "password"

    def test_responsiveness_viewport(self, browser_page):
        """TC-EDG-05: Responsiveness and viewport scaling"""
        login_page = FuzionLoginPage(browser_page).open()
        
        # 1. Mobile Viewport (iPhone X size)
        browser_page.set_viewport_size({"width": 375, "height": 812})
        assert browser_page.locator(login_page.USERNAME_INPUT).is_visible()
        assert browser_page.locator(login_page.PASSWORD_INPUT).is_visible()
        assert browser_page.locator(login_page.SUBMIT_BUTTON).is_visible()

        # 2. Desktop Viewport (1080p)
        browser_page.set_viewport_size({"width": 1920, "height": 1080})
        assert browser_page.locator(login_page.USERNAME_INPUT).is_visible()
        assert browser_page.locator(login_page.PASSWORD_INPUT).is_visible()
        assert browser_page.locator(login_page.SUBMIT_BUTTON).is_visible()
