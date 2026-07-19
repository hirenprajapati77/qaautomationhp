from __future__ import annotations

from src.config.settings import settings
from src.e2e_automation.base_page import BasePage


class FuzionLoginPage(BasePage):
    # Selectors
    USERNAME_INPUT = "#email"
    PASSWORD_INPUT = "#password"
    SUBMIT_BUTTON = "button[type='submit']"
    TOGGLE_PASSWORD = "span.toggle-password"
    FORGOT_PASSWORD_LINK = "a:has-text('Forgot Password?')"
    RESET_PASSWORD_HEADER = "h5.modal-title"
    CLOSE_MODAL_BUTTON = "button.close"

    def __init__(self, page):
        super().__init__(page)
        self.base_url = settings.e2e.fuzion_base_url

    def open(self) -> FuzionLoginPage:
        self.goto("/login")
        return self

    def login(self, username: str, password: str) -> FuzionLoginPage:
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        return self

    def is_logged_in(self) -> bool:
        # Successful login redirects to app-preference page
        return "app-preference" in self.page.url
