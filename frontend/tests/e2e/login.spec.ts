import { test, expect } from '@playwright/test'

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should display login form', async ({ page }) => {
    await expect(page.locator('text=Войти')).toBeVisible()
    await expect(page.locator('input[name="login"]')).toBeVisible()
    await expect(page.locator('input[name="password"]')).toBeVisible()
  })

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.click('button[type="submit"]')
    
    await expect(page.locator('text=Логин обязателен')).toBeVisible()
    await expect(page.locator('text=Пароль обязателен')).toBeVisible()
  })

  test('should navigate to dashboard on successful login', async ({ page }) => {
    // Mock successful login response
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'test-token',
          user: { id: 1, name: 'Test User', role: 'admin' }
        })
      })
    })

    await page.fill('input[name="login"]', 'testuser')
    await page.fill('input[name="password"]', 'testpassword')
    await page.click('button[type="submit"]')

    // Should redirect to dashboard
    await expect(page).toHaveURL('/')
  })

  test('should display error on failed login', async ({ page }) => {
    // Mock failed login response
    await page.route('**/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Неверные учетные данные'
        })
      })
    })

    await page.fill('input[name="login"]', 'wronguser')
    await page.fill('input[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    await expect(page.locator('text=Неверные учетные данные')).toBeVisible()
  })
}) 