const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

test.describe('Accessibility', () => {
  const routes = ['/', '/payments', '/transactions', '/flows'];

  for (const route of routes) {
    test(`${route} page should have no axe violations`, async ({ page }) => {
      await page.goto(route);

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});
