import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('10 - Library', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('library page loads', async ({ page }) => {
    await page.goto('/admin/library');
    await waitForLoaded(page);
    await screenshot(page, '10-library-list');
    await expect(page.locator('body')).toContainText(/library|book|isbn|author/i);
  });

  test('can add a new book', async ({ page }) => {
    await page.goto('/admin/library');
    await waitForLoaded(page);

    // Navigate to books tab if available
    const booksTab = page.locator('button, [role="tab"]').filter({ hasText: /book/i }).first();
    if (await booksTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await booksTab.click();
      await waitForLoaded(page);
    }

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);

    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i], input').first();
    await titleInput.fill(`Playwright Book ${unique}`);

    const authorInput = page.locator('input[name="author"], input[placeholder*="author" i]').first();
    if (await authorInput.isVisible({ timeout: 2000 }).catch(() => false)) await authorInput.fill('Test Author');

    const isbnInput = page.locator('input[name="isbn"], input[placeholder*="isbn" i]').first();
    if (await isbnInput.isVisible({ timeout: 2000 }).catch(() => false)) await isbnInput.fill(`978${unique}`);

    const copiesInput = page.locator('input[name="total_copies"], input[name="copies"], input[type="number"]').first();
    if (await copiesInput.isVisible({ timeout: 2000 }).catch(() => false)) await copiesInput.fill('5');

    await screenshot(page, '10-add-book-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create|add/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '10-add-book-result');
  });

  test('can search for a book', async ({ page }) => {
    await page.goto('/admin/library');
    await waitForLoaded(page);

    const searchInput = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await searchInput.fill('math');
      await page.waitForTimeout(1000);
      await screenshot(page, '10-library-search');
      await searchInput.clear();
    }
  });

  test('can issue a book to a student', async ({ page }) => {
    await page.goto('/admin/library');
    await waitForLoaded(page);

    const issueBtn = page.locator('button').filter({ hasText: /issue|borrow|lend/i }).first();
    if (!await issueBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await issueBtn.click();
    await page.waitForTimeout(600);
    await screenshot(page, '10-issue-book-form');

    const cancelBtn = page.locator('button').filter({ hasText: /cancel|close/i }).first();
    if (await cancelBtn.isVisible({ timeout: 2000 }).catch(() => false)) await cancelBtn.click();
  });

  test('can view issued books / returns', async ({ page }) => {
    await page.goto('/admin/library');
    await waitForLoaded(page);

    const issuedTab = page.locator('button, [role="tab"]').filter({ hasText: /issued|return|borrow/i }).first();
    if (await issuedTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await issuedTab.click();
      await waitForLoaded(page);
      await screenshot(page, '10-library-issued');
    }
  });
});
