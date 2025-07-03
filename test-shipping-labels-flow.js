const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('1. Navigating to application...');
    await page.goto('http://localhost:3000');
    
    // Check if we need to login
    if (await page.locator('input[type="password"]').isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('2. Login required, entering password...');
      await page.fill('input[type="password"]', 'MIAMI');
      await page.click('button[type="submit"]');
      await page.waitForLoadState('networkidle');
    }

    console.log('3. On main order form page...');
    
    // Fill in PO number
    await page.fill('#po', 'TEST-PO-' + Date.now());
    
    // Select an address (first one in dropdown)
    await page.selectOption('#address', { index: 1 });
    await page.waitForTimeout(500);
    
    // Add some products to the order
    console.log('4. Adding products to order...');
    const casesInputs = await page.locator('input[type="number"]').all();
    if (casesInputs.length > 0) {
      // Add 2 cases of the first product
      await casesInputs[0].fill('2');
      
      // Add 1 case of the second product if available
      if (casesInputs.length > 1) {
        await casesInputs[1].fill('1');
      }
    }
    
    // Click Next button to go to shipping labels page
    console.log('5. Clicking Next to go to shipping labels page...');
    await page.click('button:has-text("Next")');
    
    // Wait for navigation to shipping labels page
    await page.waitForURL('**/shipping-labels');
    console.log('6. Successfully navigated to shipping labels page!');
    
    // Take a screenshot of the shipping labels page
    await page.screenshot({ path: 'shipping-labels-page.png', fullPage: true });
    
    // Verify the page content
    console.log('7. Verifying shipping labels page content...');
    
    // Check if the ordered items are displayed
    const orderedItemsText = await page.locator('h5:has-text("Please upload labels for the following items:")').isVisible();
    console.log('   - Ordered items section visible:', orderedItemsText);
    
    // Check if the total labels needed message is shown
    const totalLabelsAlert = await page.locator('.alert-info').textContent();
    console.log('   - Total labels needed:', totalLabelsAlert);
    
    // Check if shipping method dropdown is present
    const shippingMethodVisible = await page.locator('#shippingMethod').isVisible();
    console.log('   - Shipping method dropdown visible:', shippingMethodVisible);
    
    // Check if drag & drop area is present
    const dragDropVisible = await page.locator('div[style*="dashed"]').isVisible();
    console.log('   - Drag & drop area visible:', dragDropVisible);
    
    // Check if Continue button is disabled (since no files uploaded)
    const continueButton = page.locator('button:has-text("Continue to Order Review")');
    const isDisabled = await continueButton.isDisabled();
    console.log('   - Continue button properly disabled:', isDisabled);
    
    console.log('\n✅ Test completed successfully!');
    console.log('Screenshot saved as: shipping-labels-page.png');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    await page.screenshot({ path: 'error-state.png' });
  } finally {
    await browser.close();
  }
})();