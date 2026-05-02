import { test as base, Page } from '@playwright/test';
import { AuthHelper } from '../helpers/auth.helper';
import usersData from './users.json';

const USERS = usersData.users as Record<string, any>;

type UserFixtures = {
  adminUser: Page;
  regularUser: Page;
  guestUser: Page;
};

export const test = base.extend<UserFixtures>({
  adminUser: async ({ page }, use) => {
    await AuthHelper.loginAs(page, USERS['adminUser']);
    await use(page);
    await AuthHelper.logout(page);
  },
  regularUser: async ({ page }, use) => {
    await AuthHelper.loginAs(page, USERS['regularUser']);
    await use(page);
    await AuthHelper.logout(page);
  },
  guestUser: async ({ page }, use) => {
    await AuthHelper.loginAs(page, USERS['guestUser']);
    await use(page);
    await AuthHelper.logout(page);
  },
});

export { expect } from '@playwright/test';
export { USERS };