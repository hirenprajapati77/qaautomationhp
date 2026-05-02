import { BasePage } from './BasePage';
import { Page } from '@playwright/test';

export class UserManagementPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async goto() {
    await this.navigate('/User/Index');
  }

  // Grid locators
  async getGridRows() {
    return this.page.locator('[data-testid="user-grid"] tbody tr, table tbody tr');
  }

  async getColumnHeader(columnName: string) {
    return this.page.locator(`th:has-text("${columnName}"), [data-column="${columnName}"]`);
  }

  async clickColumnHeader(columnName: string) {
    const header = await this.getColumnHeader(columnName);
    await header.click();
  }

  async applyFilter(columnName: string, value: string) {
    const filterIcon = this.page.locator(`[data-column="${columnName}"] [data-testid="filter-icon"], th:has-text("${columnName}") button`).first();
    await filterIcon.click();
    const filterInput = this.page.locator(`[placeholder*="filter"], [placeholder*="Filter"]`).first();
    await filterInput.fill(value);
    const applyBtn = this.page.getByRole('button', { name: /apply|ok/i }).first();
    await applyBtn.click();
  }

  async searchInGrid(searchTerm: string) {
    const searchBox = this.page.locator('[placeholder*="search"], [placeholder*="Search"]').first();
    await searchBox.fill(searchTerm);
    await this.page.keyboard.press('Enter');
  }

  async clickExcelExport() {
    const exportBtn = this.page.getByRole('button', { name: /export|excel/i }).first();
    await exportBtn.click();
  }

  async clickResetLayout() {
    const resetBtn = this.page.getByRole('button', { name: /reset/i }).first();
    await resetBtn.click();
  }

  async clickClearFilters() {
    const clearBtn = this.page.getByRole('button', { name: /clear|reset/i });
    const buttons = await clearBtn.all();
    for (const btn of buttons) {
      const text = await btn.textContent();
      if (text?.includes('Clear')) {
        await btn.click();
        break;
      }
    }
  }

  async clickChooseColumns() {
    const chooseBtn = this.page.getByRole('button', { name: /column|choose/i }).first();
    await chooseBtn.click();
  }

  async toggleColumn(columnName: string) {
    const checkbox = this.page.locator(`input[type="checkbox"][value="${columnName}"], label:has-text("${columnName}") input`);
    await checkbox.click();
  }

  async saveSortFilterChoices() {
    const okBtn = this.page.getByRole('button', { name: /ok|apply/i }).first();
    await okBtn.click();
  }

  // View functionality
  async clickViewButton() {
    const viewBtn = this.page.getByRole('button', { name: /view/i }).first();
    await viewBtn.click();
  }

  async clickSaveView() {
    const saveViewBtn = this.page.getByRole('button', { name: /save.*view/i });
    await saveViewBtn.click();
  }

  async clickManageViews() {
    const manageBtn = this.page.getByRole('button', { name: /manage.*view/i });
    await manageBtn.click();
  }

  async toggleUpdateExistingView(toggle: boolean) {
    const checkbox = this.page.locator('input[type="checkbox"]').filter({ hasText: /update.*existing/i }).first();
    const isChecked = await checkbox.isChecked();
    if (isChecked !== toggle) {
      await checkbox.click();
    }
  }

  async enterViewName(name: string) {
    const input = this.page.locator('input[placeholder*="View Name"], input[name*="viewName"]').first();
    await input.fill(name);
  }

  async enterViewDescription(description: string) {
    const input = this.page.locator('textarea[placeholder*="Description"], input[name*="description"]').first();
    await input.fill(description);
  }

  async selectViewFromDropdown(viewName: string) {
    const dropdown = this.page.locator('select, [role="combobox"]').first();
    await dropdown.click();
    const option = this.page.getByRole('option', { name: viewName });
    await option.click();
  }

  // Select actions
  async selectUser(userName: string) {
    const checkbox = this.page.locator(`input[type="checkbox"][value="${userName}"], tr:has-text("${userName}") input[type="checkbox"]`).first();
    await checkbox.click();
  }

  async selectMultipleUsers(userNames: string[]) {
    for (const userName of userNames) {
      await this.selectUser(userName);
    }
  }

  async clickSelectAction() {
    const actionBtn = this.page.getByRole('button', { name: /select action|action/i }).first();
    await actionBtn.click();
  }

  async selectActionOption(actionName: string) {
    const option = this.page.getByRole('option', { name: new RegExp(actionName, 'i') });
    await option.click();
  }

  async confirmDeletion() {
    const confirmBtn = this.page.getByRole('button', { name: /confirm|yes|delete/i });
    await confirmBtn.click();
  }

  // Import functionality
  async clickCreateButton() {
    const createBtn = this.page.getByRole('button', { name: /\+|create|add/i }).first();
    await createBtn.click();
  }

  async clickImport() {
    const importBtn = this.page.getByRole('button', { name: /import/i });
    await importBtn.click();
  }

  async browseFile(filePath: string) {
    const input = this.page.locator('input[type="file"]');
    await input.setInputFiles(filePath);
  }

  async clickDownloadSample() {
    const downloadBtn = this.page.getByRole('button', { name: /sample|template/i });
    await downloadBtn.click();
  }

  async clickImportConfirm() {
    const importBtn = this.page.getByRole('button', { name: /import/i }).last();
    await importBtn.click();
  }

  // Create user form
  async clickCreateUser() {
    const createBtn = this.page.getByRole('button', { name: /create/i });
    await createBtn.click();
  }

  async fillFirstName(value: string) {
    const input = this.page.locator('input[name*="firstName"], input[placeholder*="First"]').first();
    await input.fill(value);
  }

  async fillLastName(value: string) {
    const input = this.page.locator('input[name*="lastName"], input[placeholder*="Last"]').first();
    await input.fill(value);
  }

  async fillEmail(value: string) {
    const input = this.page.locator('input[type="email"], input[name*="email"]').first();
    await input.fill(value);
  }

  async fillMobileNumber(value: string) {
    const input = this.page.locator('input[name*="mobile"], input[placeholder*="Mobile"]').first();
    await input.fill(value);
  }

  async fillEmployeeId(value: string) {
    const input = this.page.locator('input[name*="employeeId"], input[placeholder*="Employee"]').first();
    await input.fill(value);
  }

  async selectDesignation(value: string) {
    const dropdown = this.page.locator('select[name*="designation"], [data-testid="designation"]').first();
    await dropdown.click();
    const option = this.page.getByRole('option', { name: new RegExp(value, 'i') });
    await option.click();
  }

  async selectDepartment(value: string) {
    const dropdown = this.page.locator('select[name*="department"], [data-testid="department"]').first();
    await dropdown.click();
    const option = this.page.getByRole('option', { name: new RegExp(value, 'i') });
    await option.click();
  }

  async selectReportingManager(value: string) {
    const dropdown = this.page.locator('select[name*="reportingManager"], [data-testid="manager"]').first();
    await dropdown.click();
    const option = this.page.getByRole('option', { name: new RegExp(value, 'i') });
    await option.click();
  }

  async selectRoles(roles: string[]) {
    const dropdown = this.page.locator('select[name*="role"], [data-testid="roles"]').first();
    await dropdown.click();
    for (const role of roles) {
      const option = this.page.getByRole('option', { name: new RegExp(role, 'i') });
      await option.click();
    }
  }

  async toggleDisable(toggle: boolean) {
    const checkbox = this.page.locator('input[type="checkbox"][name*="disable"]').first();
    const isChecked = await checkbox.isChecked();
    if (isChecked !== toggle) {
      await checkbox.click();
    }
  }

  async toggleAllowEmail(toggle: boolean) {
    const checkbox = this.page.locator('input[type="checkbox"][name*="email"], input[type="checkbox"][name*="allow"]').last();
    const isChecked = await checkbox.isChecked();
    if (isChecked !== toggle) {
      await checkbox.click();
    }
  }

  async clickSaveUser() {
    const saveBtn = this.page.getByRole('button', { name: /save|create/i }).first();
    await saveBtn.click();
  }

  async clickCancelForm() {
    const cancelBtn = this.page.getByRole('button', { name: /cancel|close/i });
    await cancelBtn.click();
  }

  async getValidationError(fieldName: string) {
    const error = this.page.locator(`[data-field="${fieldName}"] .error, .error:near(label:has-text("${fieldName}"))`).first();
    return error.textContent();
  }

  async getAllValidationErrors() {
    const errors = await this.page.locator('.error, [role="alert"]').all();
    const errorTexts = [];
    for (const error of errors) {
      const text = await error.textContent();
      if (text) errorTexts.push(text);
    }
    return errorTexts;
  }
}
