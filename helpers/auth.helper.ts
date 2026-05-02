import { Page } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

export interface UserCredentials {
  email?: string;
  otp: string;
  role: string;
  name?: string;
}

export class AuthHelper {
  static async loginAs(page: Page, user: UserCredentials) {
    const loginPage = new LoginPage(page);
    const email = user.email || '';
    await loginPage.loginWithOTP(email, user.otp);
  }

  static async logout(page: Page) {
    const btn = page.getByRole('button', { name: /logout|sign out|profile/i });
    try {
      if (await btn.isVisible()) {
        await btn.click();
        await page.waitForLoadState('networkidle');
      }
    } catch (e) {
      console.log('Logout button not found or not visible');
    }
  }

  static async isAuthenticated(page: Page): Promise<boolean> {
    try {
      const btn = page.getByRole('button', { name: /logout|sign out|profile/i });
      return await btn.isVisible();
    } catch {
      return false;
    }
  }
}