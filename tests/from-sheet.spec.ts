import { test, expect } from '../fixtures/test.fixtures';
import { LoginPage } from '../pages/LoginPage';
import { DataHelper } from '../helpers/data.helper';

// ── POSITIVE CASES ────────────────────────────────────────────────────────────
test.describe('✓ POSITIVE CASES', () => {
  test('App loads successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).not.toHaveURL(/error|404|500/);
    await expect(page).toHaveTitle(/.+/);
  });

  test('Login page is accessible', async ({ page }) => {
    await page.goto('/login');
    await expect(page).not.toHaveURL(/error|404/);
  });
});

// ── NEGATIVE CASES ────────────────────────────────────────────────────────────
test.describe('✗ NEGATIVE CASES', () => {
  test('Login fails with wrong OTP', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginWithOTP('hiren@innovuratech.com', '000000');
    const isLoggedIn = await loginPage.isLoggedIn();
    expect(isLoggedIn).toBe(false);
  });

  test('Login fails with empty email', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    const submitBtn = page.getByRole('button', { name: /login|submit/i }).last();
    if (await submitBtn.isVisible()) await submitBtn.click();
    const isLoggedIn = await loginPage.isLoggedIn();
    expect(isLoggedIn).toBe(false);
  });
});

// ── EDGE CASES ────────────────────────────────────────────────────────────────
test.describe('◈ EDGE CASES', () => {
  test('SQL injection in email does not crash app', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginWithOTP(DataHelper.boundaries.sqlInjection, '123456');
    await expect(page).not.toHaveURL(/error|500/);
  });

  test('XSS payload in email is handled safely', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.loginWithOTP(DataHelper.boundaries.xssPayload, '123456');
    await expect(page).not.toHaveURL(/error|500/);
  });

  test('Max length email handled gracefully', async ({ page }) => {
    await page.goto('');
    const emailInput = page.locator('input[type=\"text\"], input[type=\"email\"]').first();
    if (await emailInput.isVisible()) {
      await emailInput.fill(DataHelper.boundaries.maxLength255);
    }
    await expect(page).not.toHaveURL(/error|500/);
  });
});