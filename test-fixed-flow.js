const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 300
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('1. Opening application...');
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Check if we're on login page
    const passwordField = page.locator('input[type="password"]');
    if (await passwordField.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('2. Login page detected, entering password...');
      await passwordField.fill('MIAMI');
      await page.click('button[type="submit"]');
      
      // Wait for login to process
      await page.waitForTimeout(1000);
    }
    
    // Wait for order form to load
    console.log('3. Waiting for order form...');
    await page.waitForSelector('#po', { timeout: 10000 });
    console.log('   ✓ Order form loaded!');
    
    // Fill in the order form
    console.log('4. Filling order form...');
    await page.fill('#po', 'TEST-' + Date.now());
    
    // Select first available address
    const addressDropdown = page.locator('#address');
    const options = await addressDropdown.locator('option').count();
    if (options > 1) {
      await addressDropdown.selectOption({ index: 1 });
      console.log('   ✓ Selected address');
    }
    
    // Add products
    const casesInputs = await page.locator('input[type="number"]').all();
    if (casesInputs.length > 0) {
      await casesInputs[0].fill('2');
      console.log('   ✓ Added 2 cases of first product');
      
      if (casesInputs.length > 1) {
        await casesInputs[1].fill('1');
        console.log('   ✓ Added 1 case of second product');
      }
    }
    
    // Click Next
    console.log('5. Clicking Next button...');
    await page.click('button:has-text("Next")');
    
    // Wait for shipping labels page
    await page.waitForURL('**/shipping-labels', { timeout: 5000 });
    console.log('   ✓ Successfully navigated to shipping labels page!');
    
    // Verify shipping labels page content
    console.log('6. Verifying shipping labels page...');
    await page.waitForSelector('h1:has-text("Upload Shipping Labels")');
    
    // Take screenshot
    await page.screenshot({ path: 'shipping-labels-success.png', fullPage: true });
    console.log('   ✓ Screenshot saved: shipping-labels-success.png');
    
    // Check page elements
    const hasOrderedItems = await page.locator('text="Please upload labels for the following items:"').isVisible();
    const hasUploadArea = await page.locator('div[style*="dashed"]').isVisible();
    const hasShippingMethod = await page.locator('#shippingMethod').isVisible();
    
    console.log('\n✅ Test Results:');
    console.log('   - Ordered items displayed:', hasOrderedItems);
    console.log('   - Upload area visible:', hasUploadArea);
    console.log('   - Shipping method dropdown:', hasShippingMethod);
    
    // Check the total labels message
    const alertText = await page.locator('.alert-info').textContent();
    console.log('   - Alert message:', alertText);
    
    console.log('\n✨ Test completed successfully!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await page.screenshot({ path: 'error-state.png' });
  } finally {
    console.log('\nClosing browser in 3 seconds...');
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();