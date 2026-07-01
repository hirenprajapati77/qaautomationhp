"""
LoginPage: concrete Page Object for the-internet.herokuapp.com/login
(a well-known, free, stable sandbox site used widely for QA automation
practice - no credentials required, valid creds are publicly documented
by the site itself: tomsmith / SuperSecretPassword!).
"""
from __future__ import annotations
from src.e2e_automation.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    SUBMIT_BUTTON = "button[type='submit']"
    FLASH_MESSAGE = "#flash"
    SECURE_AREA_HEADER = ".secure-area h2, h2"

    def open(self) -> "LoginPage":
        self.goto("/login")
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)
        return self

    def get_flash_message(self) -> str:
        self.wait_for(self.FLASH_MESSAGE)
        return self.text_of(self.FLASH_MESSAGE).strip()

    def is_logged_in(self) -> bool:
        return "secure" in self.page.url
