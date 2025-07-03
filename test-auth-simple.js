const { chromium } = require('playwright');

async function testAuth() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    console.log('Testing authentication system...\n');
    
    // Test 1: Check if login page loads
    console.log('1. Loading login page...');
    await page.goto('http://localhost:3001');
    const title = await page.title();
    console.log(`   ✓ Page title: ${title}`);
    
    // Test 2: Test backend API directly
    console.log('\n2. Testing backend API...');
    const apiResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:5001/api/check-auth');
        return await response.json();
      } catch (e) {
        return { error: e.message };
      }
    });
    console.log('   API Response:', apiResponse);
    
    // Test 3: Try login with correct password
    console.log('\n3. Testing login with correct password...');
    await page.fill('input[type="password"]', 'MIAMI');
    
    // Intercept the login request to see what happens
    const [loginResponse] = await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/login'), { timeout: 5000 }).catch(() => null),
      page.click('button[type="submit"]')
    ]);
    
    if (loginResponse) {
      console.log(`   Login response status: ${loginResponse.status()}`);
      const responseBody = await loginResponse.json().catch(() => ({}));
      console.log('   Login response:', responseBody);
    } else {
      console.log('   ⚠ No login response detected - checking if redirected...');
      await page.waitForTimeout(2000);
      const currentUrl = page.url();
      console.log(`   Current URL: ${currentUrl}`);
      if (currentUrl.includes('order-form')) {
        console.log('   ✓ Successfully redirected to order form!');
      }
    }
    
    // Take a screenshot
    await page.screenshot({ path: 'auth-test-result.png' });
    console.log('\n✓ Screenshot saved as auth-test-result.png');
    
  } catch (error) {
    console.error('\n✗ Error:', error.message);
  } finally {
    await browser.close();
  }
}

testAuth();