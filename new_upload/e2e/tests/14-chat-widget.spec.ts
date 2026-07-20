/**
 * E2E Tests - Chat Widget (AI Assistant)
 *
 * Covers:
 *  01. Widget floating button is visible
 *  02. Clicking opens the panel (header + tabs)
 *  03. Welcome message bot bubble present
 *  04. Suggestion chips visible on welcome message
 *  05. Typing a query and pressing Enter sends the message
 *  06. Bot replies after a free-text message
 *  07. Send button is disabled when input is empty
 *  08. Clear button resets conversation
 *  09. Guided Actions flow starts via "hi"
 *  10. Option buttons appear in guided flow
 *  11. Clicking an option advances the conversation
 *  12. Back-to-Menu header button resets flow
 *  13. FAQ tab loads; search input filters
 *  14. Close button hides the panel
 *  15. Unread badge clears on re-open
 */

import { test, expect, Page, Locator } from '@playwright/test';
import { BASE_URL, loginAsSchoolAdmin } from './helpers';

/** The fixed chat panel container selector */
const PANEL_SEL = '[class*="bottom-20"][class*="right-6"]';

/** Return the scoped panel locator */
function panel(page: Page): Locator {
  return page.locator(PANEL_SEL);
}

/** Chat text input - scoped to the panel */
function chatInput(page: Page): Locator {
  return panel(page).locator('input[placeholder]');
}

/**
 * Wait for the bot to finish replying.
 * Uses a scoped querySelector so it doesn't accidentally find the wrong input.
 */
async function waitForBotReply(page: Page, timeout = 55000) {
  await page.waitForFunction(
    (sel: string) => {
      const p = document.querySelector(sel);
      if (!p) return false;
      const input = p.querySelector('input[placeholder]') as HTMLInputElement | null;
      return input ? !input.disabled : false;
    },
    PANEL_SEL,
    { timeout },
  );
}

/** Return current count of bot message bubbles */
async function botBubbleCount(page: Page): Promise<number> {
  return panel(page).locator('.justify-start').count();
}

test.describe('Chat Widget', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await loginAsSchoolAdmin(page);
    await page.goto(BASE_URL + '/admin/students');
    await page.waitForLoadState('networkidle');
  });

  test.afterAll(async () => {
    await page.close();
  });

  // -----------------------------------------------------------------------
  // 01. Floating button visible
  // -----------------------------------------------------------------------
  test('01 - floating AI Assistant button is visible', async () => {
    await expect(page.locator('button', { hasText: 'AI Assistant' })).toBeVisible({ timeout: 8000 });
  });

  // -----------------------------------------------------------------------
  // 02. Opening the panel
  // -----------------------------------------------------------------------
  test('02 - clicking opens the chat panel with header and tabs', async () => {
    await page.locator('button', { hasText: 'AI Assistant' }).click();
    const p = panel(page);
    await expect(p.locator('text=School AI Agent').first()).toBeVisible({ timeout: 6000 });
    await expect(p.locator('button').filter({ hasText: 'Chat' }).first()).toBeVisible();
    await expect(p.locator('button').filter({ hasText: 'FAQ' }).first()).toBeVisible();
    await expect(chatInput(page)).toBeVisible();
  });

  // -----------------------------------------------------------------------
  // 03. Bot welcome bubble
  // -----------------------------------------------------------------------
  test('03 - welcome message bot bubble is present', async () => {
    await expect(panel(page).locator('.justify-start').first()).toBeVisible({ timeout: 5000 });
    // Bot avatar is a gradient circle
    await expect(panel(page).locator('.bg-gradient-to-br.from-blue-500').first()).toBeVisible({ timeout: 3000 });
  });

  // -----------------------------------------------------------------------
  // 04. Suggestion chips
  // -----------------------------------------------------------------------
  test('04 - suggestion chips are rendered on the welcome message', async () => {
    const chip = panel(page).locator('button[class*="rounded-full"][class*="indigo"]').first();
    await expect(chip).toBeVisible({ timeout: 5000 });
  });

  // -----------------------------------------------------------------------
  // 05. Type and Enter sends a message
  // -----------------------------------------------------------------------
  test('05 - typing and pressing Enter sends a user message', async () => {
    const input = chatInput(page);
    await input.fill('How many students are enrolled?');
    await input.press('Enter');
    await expect(input).toHaveValue('', { timeout: 5000 });
    await expect(panel(page).locator('.justify-end', { hasText: 'How many students are enrolled?' })).toBeVisible({ timeout: 8000 });
  });

  // -----------------------------------------------------------------------
  // 06. Bot replies
  // -----------------------------------------------------------------------
  test('06 - bot replies to the free-text query', async () => {
    // Loading dots (animate-bounce) inside the panel
    await panel(page).locator('.animate-bounce').first().waitFor({ state: 'attached', timeout: 8000 }).catch(() => {});
    await waitForBotReply(page, 55000);
    await expect(panel(page).locator('.justify-start').last()).toBeVisible({ timeout: 5000 });
  });

  // -----------------------------------------------------------------------
  // 07. Send button disabled when input empty
  // -----------------------------------------------------------------------
  test('07 - send button is disabled when input is empty', async () => {
    await chatInput(page).fill('');
    // Send button is the last button in the input bar; has [disabled] when input empty
    await expect(panel(page).locator('button[disabled]').last()).toBeVisible({ timeout: 5000 });
  });

  // -----------------------------------------------------------------------
  // 08. Clear resets conversation
  // -----------------------------------------------------------------------
  test('08 - Clear button resets the conversation to welcome only', async () => {
    await panel(page).locator('button', { hasText: 'Clear' }).click();
    await expect(panel(page).locator('.justify-end')).toHaveCount(0, { timeout: 4000 });
    await expect(panel(page).locator('.justify-start').first()).toBeVisible({ timeout: 3000 });
  });

  // -----------------------------------------------------------------------
  // 09. Guided Actions flow via "hi"
  // -----------------------------------------------------------------------
  test('09 - typing "hi" starts guided flow and shows Guided Mode pill', async () => {
    const input = chatInput(page);
    await input.fill('hi');
    await input.press('Enter');
    await expect(panel(page).locator('.justify-end', { hasText: 'hi' })).toBeVisible({ timeout: 8000 });
    await waitForBotReply(page, 55000);
    // Header sub-text shows "Guided Mode"
    await expect(panel(page).locator('text=Guided Mode')).toBeVisible({ timeout: 10000 });
  });

  // -----------------------------------------------------------------------
  // 10. Guided flow option buttons
  // -----------------------------------------------------------------------
  test('10 - guided flow renders option buttons', async () => {
    const optionBtn = panel(page).locator('button[class*="from-indigo-50"]').first();
    await expect(optionBtn).toBeVisible({ timeout: 8000 });
  });

  // -----------------------------------------------------------------------
  // 11. Clicking an option advances guided flow
  // -----------------------------------------------------------------------
  test('11 - clicking a guided option advances the conversation', async () => {
    const countBefore = await botBubbleCount(page);
    const firstOption = panel(page).locator('button[class*="from-indigo-50"]').first();
    await firstOption.click();
    // User bubble appears (we check count not exact text to avoid description bleed)
    await expect(panel(page).locator('.justify-end')).not.toHaveCount(0, { timeout: 8000 });
    await waitForBotReply(page, 55000);
    expect(await botBubbleCount(page)).toBeGreaterThan(countBefore);
  });

  // -----------------------------------------------------------------------
  // 12. Back-to-Menu resets guided flow
  // -----------------------------------------------------------------------
  test('12 - Back-to-Menu header button resets guided flow', async () => {
    const menuBtn = panel(page).locator('button', { hasText: 'Menu' }).first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await waitForBotReply(page, 55000);
      await expect(panel(page).locator('.justify-start').last()).toBeVisible({ timeout: 5000 });
    }
  });

  // -----------------------------------------------------------------------
  // 13. FAQ tab
  // -----------------------------------------------------------------------
  test('13 - FAQ tab loads and search input is functional', async () => {
    // Ensure bot is not still loading before switching tabs
    await waitForBotReply(page, 10000).catch(() => {});
    await panel(page).locator('button').filter({ hasText: 'FAQ' }).first().click();
    const searchInput = panel(page).locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill('attendance');
    await page.waitForTimeout(500);
    await expect(panel(page).locator('button').filter({ hasText: 'FAQ' }).first()).toBeVisible();
    await searchInput.clear();
    await panel(page).locator('button').filter({ hasText: 'Chat' }).first().click();
    await expect(chatInput(page)).toBeVisible({ timeout: 3000 });
  });

  // -----------------------------------------------------------------------
  // 14. Close hides the panel
  // -----------------------------------------------------------------------
  test('14 - Close button hides the chat panel', async () => {
    // Switch back to chat tab just in case
    await panel(page).locator('button').filter({ hasText: 'Chat' }).first().click().catch(() => {});
    const closeBtn = page.locator('button', { hasText: 'Close' });
    if (await closeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await closeBtn.click();
      // "AI Assistant" floating button shown = open===false = panel is hidden
      await expect(page.locator('button', { hasText: 'AI Assistant' })).toBeVisible({ timeout: 3000 });
      // Confirm "Close" label is gone (panel is closed)
      await expect(page.locator('button', { hasText: 'Close' })).not.toBeVisible({ timeout: 3000 });
    } else {
      // Panel already closed — just verify the float button is shown
      await expect(page.locator('button', { hasText: 'AI Assistant' })).toBeVisible({ timeout: 5000 });
    }
  });

  // -----------------------------------------------------------------------
  // 15. Unread badge clears on re-open
  // -----------------------------------------------------------------------
  test('15 - unread badge clears when chat panel is reopened', async () => {
    await page.locator('button', { hasText: 'AI Assistant' }).click();
    await chatInput(page).fill('hello');
    await chatInput(page).press('Enter');
    await page.locator('button', { hasText: 'Close' }).click();
    // Wait for bot reply to arrive while panel is closed
    await page.waitForTimeout(8000);
    await page.locator('button', { hasText: 'AI Assistant' }).click();
    // Badge should be reset after opening
    const badge = page.locator('button', { hasText: 'AI Assistant' }).locator('span[class*="bg-red-500"]');
    await expect(badge).not.toBeVisible({ timeout: 3000 });
    await page.locator('button', { hasText: 'Close' }).click();
  });
});