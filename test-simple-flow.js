const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 // Slow down actions to see what's happening
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Opening http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Take initial screenshot
    await page.screenshot({ path: 'initial-page.png' });
    console.log('Screenshot saved: initial-page.png');
    
    // Wait a bit to see what loads
    await page.waitForTimeout(2000);
    
    // Check current URL
    console.log('Current URL:', page.url());
    
    // Check if we're on login page or main page
    const hasPasswordField = await page.locator('input[type="password"]').count();
    console.log('Password field found:', hasPasswordField > 0);
    
    if (hasPasswordField > 0) {
      console.log('Entering password...');
      await page.fill('input[type="password"]', 'MIAMI');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'after-login.png' });
      console.log('Screenshot saved: after-login.png');
    }
    
    // Check if we're on the order form
    const hasPOField = await page.locator('#po').count();
    console.log('PO field found:', hasPOField > 0);
    
    if (hasPOField > 0) {
      console.log('We are on the order form!');
      
      // Fill basic order info
      await page.fill('#po', 'TEST-123');
      
      // Try to select first address
      const addressOptions = await page.locator('#address option').count();
      console.log('Number of addresses available:', addressOptions - 1); // Minus the default option
      
      if (addressOptions > 1) {
        await page.selectOption('#address', { index: 1 });
        console.log('Selected first address');
      }
      
      // Add cases to first product
      const firstCasesInput = page.locator('input[type="number"]').first();
      if (await firstCasesInput.isVisible()) {
        await firstCasesInput.fill('2');
        console.log('Added 2 cases to first product');
      }
      
      // Look for Next button
      const nextButton = page.locator('button:has-text("Next")');
      if (await nextButton.isVisible()) {
        console.log('Found Next button, clicking...');
        await nextButton.click();
        
        // Wait for navigation
        await page.waitForTimeout(2000);
        console.log('Current URL after clicking Next:', page.url());
        
        // Take screenshot of new page
        await page.screenshot({ path: 'shipping-labels-page.png', fullPage: true });
        console.log('Screenshot saved: shipping-labels-page.png');
      }
    }
    
  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: 'error-screenshot.png' });
  } finally {
    console.log('Closing browser in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
  }
})();