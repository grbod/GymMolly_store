const { chromium } = require('playwright');

async function testLogin() {
  console.log('Starting login test...');
  
  // Launch browser
  const browser = await chromium.launch({ 
    headless: false, // Set to true for headless mode
    slowMo: 500 // Slow down actions to see what's happening
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Log console messages
  page.on('console', msg => console.log('Browser console:', msg.text()));
  page.on('pageerror', error => console.log('Browser error:', error.message));
  
  try {
    // Test 1: Navigate to login page
    console.log('1. Navigating to login page...');
    await page.goto('http://localhost:3001');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of login page
    await page.screenshot({ path: 'login-page.png' });
    console.log('   ✓ Login page loaded');
    
    // Test 2: Try incorrect password
    console.log('2. Testing incorrect password...');
    await page.fill('input[type="password"]', 'WRONG');
    await page.click('button[type="submit"]');
    
    // Wait for any error message
    await page.waitForTimeout(2000); // Give time for response
    const errorVisible = await page.locator('.alert-danger, .error-message, [class*="error"]').isVisible().catch(() => false);
    if (errorVisible) {
      console.log('   ✓ Invalid password error shown');
    } else {
      console.log('   ⚠ No visible error message, checking console...');
    }
    
    // Test 3: Try correct password
    console.log('3. Testing correct password...');
    await page.fill('input[type="password"]', 'MIAMI');
    await page.click('button[type="submit"]');
    
    // Wait for redirect to main app
    await page.waitForURL('**/order-form', { timeout: 10000 });
    console.log('   ✓ Successfully logged in and redirected');
    
    // Take screenshot of main app
    await page.screenshot({ path: 'main-app.png' });
    
    // Test 4: Verify we can see the order form
    await page.waitForSelector('text=Create Order', { timeout: 5000 });
    console.log('   ✓ Order form is visible');
    
    // Test 5: Test logout
    console.log('4. Testing logout...');
    await page.click('button:has-text("Logout")');
    await page.waitForURL('**/login', { timeout: 5000 });
    console.log('   ✓ Successfully logged out');
    
    // Test 6: Test rate limiting
    console.log('5. Testing rate limiting...');
    for (let i = 1; i <= 3; i++) {
      await page.fill('input[type="password"]', 'WRONG' + i);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(1000);
    }
    
    // Check for rate limit message
    await page.waitForSelector('text=/Too many failed attempts/i', { timeout: 5000 });
    console.log('   ✓ Rate limiting activated after 3 attempts');
    
    // Take screenshot of rate limit
    await page.screenshot({ path: 'rate-limit.png' });
    
    console.log('\n✅ All tests passed!');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    await page.screenshot({ path: 'error-screenshot.png' });
  } finally {
    await browser.close();
  }
}

// Run the test
testLogin().catch(console.error);