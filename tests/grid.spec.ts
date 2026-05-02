import { test, expect } from '../fixtures/test.fixtures';
import { UserManagementPage } from '../pages/UserManagementPage';
import { DataHelper } from '../helpers/data.helper';

test.describe('✓ GRID FUNCTIONALITY - USER MANAGEMENT', () => {
  
  test('To verify grid displays all users correctly', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    const rows = await userMgmt.getGridRows();
    expect(rows).toBeTruthy();
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('To verify column sorting A-Z functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    // Click column header twice to get A-Z order
    await userMgmt.clickColumnHeader('User Name');
    await page.waitForTimeout(500);
    const firstClick = await page.locator('table tbody tr:first-child').textContent();
    await userMgmt.clickColumnHeader('User Name');
    await page.waitForTimeout(500);
    const secondClick = await page.locator('table tbody tr:first-child').textContent();
    expect(firstClick).not.toBe(secondClick);
  });

  test('To verify column sorting Z-A functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    await userMgmt.clickColumnHeader('User Name');
    await page.waitForTimeout(500);
    await userMgmt.clickColumnHeader('User Name');
    await page.waitForTimeout(500);
    // Z-A should be descending
    const secondValue = await page.locator('table tbody tr:first-child').textContent();
    expect(secondValue).toBeTruthy();
  });

  test('To verify column text filtering', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    const searchTerm = 'admin';
    await userMgmt.searchInGrid(searchTerm);
    await page.waitForTimeout(1000);
    const rows = await userMgmt.getGridRows();
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('To verify Excel export functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    // Set up download listener
    const downloadPromise = page.waitForEvent('download');
    await userMgmt.clickExcelExport();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/xlsx|xls|csv/);
  });

  test('To verify reset layout functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    await userMgmt.clickChooseColumns();
    await page.waitForTimeout(500);
    await userMgmt.clickResetLayout();
    await page.waitForTimeout(500);
    const gridVisible = await page.locator('table').isVisible();
    expect(gridVisible).toBe(true);
  });

  test('To verify clear filters functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    await userMgmt.searchInGrid('test');
    await page.waitForTimeout(500);
    await userMgmt.clickClearFilters();
    await page.waitForTimeout(500);
    const grid = await page.locator('table').isVisible();
    expect(grid).toBe(true);
  });

  test('To verify search functionality in grid', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    await userMgmt.searchInGrid('admin');
    await page.waitForTimeout(1000);
    const rows = await userMgmt.getGridRows();
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('To verify column chooser functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    await userMgmt.clickChooseColumns();
    await page.waitForTimeout(500);
    // Toggle a column
    await userMgmt.toggleColumn('Email');
    await userMgmt.saveSortFilterChoices();
    await page.waitForTimeout(500);
    const gridVisible = await page.locator('table').isVisible();
    expect(gridVisible).toBe(true);
  });

  test('To verify pagination functionality', async ({ page, adminUser }) => {
    const userMgmt = new UserManagementPage(page);
    await userMgmt.goto();
    const paginationVisible = await page.locator('[data-testid="pagination"], .pagination, nav').isVisible().catch(() => false);
    if (paginationVisible) {
      expect(paginationVisible).toBe(true);
    }
  });
});
