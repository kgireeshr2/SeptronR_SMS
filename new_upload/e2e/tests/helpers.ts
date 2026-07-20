import { Page, expect } from '@playwright/test';

export const BASE_URL = 'http://localhost:5173';
export const API_URL = 'http://localhost:8000/api/v1';

export const SUPER_ADMIN = {
  username: 'superadmin@sms.com',
  password: 'SuperAdmin@123',
};

export const SCHOOL_ADMIN = {
  username: 'admin@sunrise.edu',
  password: 'Sunrise@123',
  schoolName: 'Sunrise Public School',
};

export const SCHOOL_NAME = 'Demo High School';

/** Login as super admin and navigate to dashboard */
export async function loginAsSuperAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('#username', SUPER_ADMIN.username);
  await page.fill('#password', SUPER_ADMIN.password);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/super-admin/dashboard', { timeout: 15000 });
}

/** Login as Sunrise Public School admin */
export async function loginAsSchoolAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('#username', SCHOOL_ADMIN.username);
  await page.fill('#password', SCHOOL_ADMIN.password);
  await page.click('button[type="submit"]');
  // Redirect to school dashboard
  await page.waitForURL(/dashboard|admin/, { timeout: 15000 });
  await waitForLoaded(page);
}

/** Wait for toast message to appear */
export async function expectToast(page: Page, text: string) {
  const toast = page.locator('[data-sonner-toast]').filter({ hasText: text });
  await expect(toast).toBeVisible({ timeout: 8000 });
}

/** Wait for a page heading to be visible */
export async function expectHeading(page: Page, text: string) {
  await expect(page.locator('h1, h2').filter({ hasText: text }).first()).toBeVisible({ timeout: 10000 });
}

/** Click sidebar nav item */
export async function clickNav(page: Page, label: string) {
  await page.locator(`a, button`).filter({ hasText: label }).first().click();
  await page.waitForLoadState('networkidle');
}

/** Fill a form field by label text */
export async function fillByLabel(page: Page, label: string, value: string) {
  const input = page.locator(`label`).filter({ hasText: label }).locator('..').locator('input, textarea, select').first();
  await input.fill(value);
}

/** Select option in dropdown by label */
export async function selectByLabel(page: Page, label: string, value: string) {
  const sel = page.locator(`label`).filter({ hasText: label }).locator('..').locator('select').first();
  await sel.selectOption(value);
}

/** Find and click a button by text */
export async function clickButton(page: Page, text: string) {
  await page.locator('button').filter({ hasText: text }).first().click();
}

/** Wait for loading spinners to disappear */
export async function waitForLoaded(page: Page) {
  await page.waitForLoadState('networkidle');
  // Wait for any spinner/skeleton to disappear
  try {
    await page.locator('.animate-spin, [data-loading="true"]').waitFor({ state: 'hidden', timeout: 5000 });
  } catch {
    // If no spinner found, that's fine
  }
}

/** Take a labeled screenshot */
export async function screenshot(page: Page, name: string) {
  await page.screenshot({ path: `screenshots/${name}.png`, fullPage: false });
}
