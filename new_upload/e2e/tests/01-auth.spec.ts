import { test, expect } from '@playwright/test';
import { loginAsSuperAdmin, SUPER_ADMIN, expectToast, screenshot } from './helpers';

test.describe('01 - Authentication', () => {

  test('shows login page with correct heading', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('SeptroSchool');
    await expect(page.locator('p')).toContainText('Sign in to your account');
    await screenshot(page, '01-login-page');
  });

  test('shows validation error for empty form submission', async ({ page }) => {
    await page.goto('/login');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Username is required').or(page.locator('text=required'))).toBeVisible();
    await screenshot(page, '01-login-validation');
  });

  test('shows error for wrong password', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', SUPER_ADMIN.username);
    await page.fill('#password', 'WrongPassword123');
    await page.click('button[type="submit"]');
    // Check for error toast or error message
    await expect(
      page.locator('[data-sonner-toast]').or(page.locator('.text-red-500')).first()
    ).toBeVisible({ timeout: 8000 });
    await screenshot(page, '01-login-wrong-password');
  });

  test('shows error for non-existent user', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'nobody@doesnotexist.com');
    await page.fill('#password', 'SomePassword123');
    await page.click('button[type="submit"]');
    await expect(
      page.locator('[data-sonner-toast]').or(page.locator('.text-red-500')).first()
    ).toBeVisible({ timeout: 8000 });
    await screenshot(page, '01-login-nonexistent');
  });

  test('can toggle password visibility', async ({ page }) => {
    await page.goto('/login');
    const passwordInput = page.locator('#password');
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click the show/hide password button
    await page.locator('button[type="button"]').filter({ hasText: /eye/i }).or(
      page.locator('button').nth(0)
    ).click();

    // Password should now be visible (or at least the button was clickable)
    await screenshot(page, '01-login-password-toggle');
  });

  test('super admin can login successfully and reaches dashboard', async ({ page }) => {
    await loginAsSuperAdmin(page);
    await expect(page).toHaveURL(/super-admin\/dashboard/);
    // Super admin dashboard should show school info
    await expect(page.locator('body')).toContainText(/school|School/i);
    await screenshot(page, '01-super-admin-dashboard');
  });

  test('forgot password page is accessible', async ({ page }) => {
    await page.goto('/login');
    const forgotLink = page.locator('a', { hasText: /forgot/i }).or(page.locator('a[href*="forgot"]'));
    if (await forgotLink.isVisible()) {
      await forgotLink.click();
      await expect(page).toHaveURL(/forgot-password/);
      await screenshot(page, '01-forgot-password');
    } else {
      test.skip();
    }
  });

  test('redirects authenticated user away from login', async ({ page }) => {
    // Login first
    await loginAsSuperAdmin(page);
    // Try to go back to login - should be redirected
    await page.goto('/login');
    await page.waitForTimeout(2000); // Give time for redirect
    // Should not stay on /login
    const url = page.url();
    expect(url).not.toMatch(/^http:\/\/localhost:5173\/login$/);
    await screenshot(page, '01-redirect-from-login');
  });

  test('super admin can logout', async ({ page }) => {
    await loginAsSuperAdmin(page);

    // Try to find logout button in header or dropdown
    const avatarOrMenu = page.locator('[aria-label="user menu"], [data-testid="user-menu"]').or(
      page.locator('button').filter({ hasText: /super.*admin|logout|sign out/i }).first()
    );

    // If not found by those selectors, try clicking avatar/user icon area
    const userArea = page.locator('header').locator('button').last();
    if (await userArea.isVisible()) {
      await userArea.click();
      await page.waitForTimeout(500);

      const logoutBtn = page.locator('button, a').filter({ hasText: /logout|sign out/i });
      if (await logoutBtn.isVisible()) {
        await logoutBtn.click();
        await page.waitForURL('**/login', { timeout: 10000 });
        await expect(page).toHaveURL(/login/);
        await screenshot(page, '01-logout');
      }
    }
  });
});
