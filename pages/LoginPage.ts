import { BasePage } from './BasePage';
import { Page } from '@playwright/test';

export class LoginPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await this.navigate('');
  }

  async loginWithOTP(email: string, otp: string) {
    await this.goto();
    
    // Wait for login form to load
    await this.page.waitForTimeout(2000);
    
    // Step 1: Enter email/mobile
    const emailInput = this.page.locator('input[type="text"], input[type="email"]').first();
    await emailInput.fill(email);
    console.log(`Entered email: ${email}`);
    
    // Step 2: Send OTP
    const sendOtpBtn = this.page.getByRole('button', { name: /send|request|get otp|verify/i }).first();
    if (await sendOtpBtn.isVisible()) {
      await sendOtpBtn.click();
      console.log('OTP sent');
      await this.page.waitForTimeout(2000);
    }
    
    // Step 3: Enter OTP
    const otpInput = this.page.locator('input[placeholder*="OTP"], input[placeholder*="otp"], input[maxlength="6"]').first();
    await otpInput.fill(otp);
    console.log(`Entered OTP: ${otp}`);
    
    // Step 4: Submit
    const submitBtn = this.page.getByRole('button', { name: /login|submit|sign in/i }).last();
    await submitBtn.click();
    await this.waitForLoad();
  }

  async getErrorMessage(): Promise<string> {
    try {
      const errorMsg = this.page.getByRole('alert');
      await errorMsg.waitFor({ state: 'visible', timeout: 5000 });
      return errorMsg.textContent() ?? '';
    } catch {
      return '';
    }
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      const logoutBtn = this.page.getByRole('button', { name: /logout|sign out|profile/i });
      return await logoutBtn.isVisible();
    } catch {
      return false;
    }
  }
}