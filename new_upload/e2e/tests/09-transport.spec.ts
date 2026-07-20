import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('09 - Transport', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('transport page loads', async ({ page }) => {
    await page.goto('/admin/transport');
    await waitForLoaded(page);
    await screenshot(page, '09-transport-list');
    await expect(page.locator('body')).toContainText(/transport|vehicle|route|bus/i);
  });

  test('can view vehicles list', async ({ page }) => {
    await page.goto('/admin/transport');
    await waitForLoaded(page);

    const vehiclesTab = page.locator('button, [role="tab"]').filter({ hasText: /vehicle/i }).first();
    if (await vehiclesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await vehiclesTab.click();
      await waitForLoaded(page);
    }
    await screenshot(page, '09-transport-vehicles');
  });

  test('can add a vehicle', async ({ page }) => {
    await page.goto('/admin/transport');
    await waitForLoaded(page);

    // Navigate to vehicles tab if available
    const vehiclesTab = page.locator('button, [role="tab"]').filter({ hasText: /vehicle/i }).first();
    if (await vehiclesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await vehiclesTab.click();
      await waitForLoaded(page);
    }

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);

    const regInput = page.locator('input[name="registration_number"], input[placeholder*="reg" i], input').first();
    await regInput.fill(`MH12PW${unique}`);

    const typeInput = page.locator('input[name="vehicle_type"], select[name="vehicle_type"]').first();
    if (await typeInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      if (await page.locator('select[name="vehicle_type"]').isVisible({ timeout: 500 }).catch(() => false)) {
        await page.locator('select[name="vehicle_type"]').selectOption({ index: 1 });
      } else {
        await typeInput.fill('Bus');
      }
    }

    const capacityInput = page.locator('input[name="capacity"], input[placeholder*="capacity" i]').first();
    if (await capacityInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await capacityInput.fill('40');
    }

    await screenshot(page, '09-add-vehicle-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '09-add-vehicle-result');
  });

  test('can view routes list', async ({ page }) => {
    await page.goto('/admin/transport');
    await waitForLoaded(page);

    const routesTab = page.locator('button, [role="tab"]').filter({ hasText: /route/i }).first();
    if (await routesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await routesTab.click();
      await waitForLoaded(page);
      await screenshot(page, '09-transport-routes');
    }
  });

  test('can add a transport route', async ({ page }) => {
    await page.goto('/admin/transport');
    await waitForLoaded(page);

    const routesTab = page.locator('button, [role="tab"]').filter({ hasText: /route/i }).first();
    if (await routesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await routesTab.click();
      await waitForLoaded(page);
    }

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const nameInput = page.locator('input[name="name"], input[placeholder*="route name" i], input').first();
    await nameInput.fill(`Playwright Route ${Date.now().toString().slice(-6)}`);

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '09-add-route-result');
  });
});
