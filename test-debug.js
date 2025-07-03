const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Capture console messages
  page.on('console', msg => {
    console.log(`CONSOLE [${msg.type()}]:`, msg.text());
  });

  // Capture page errors
  page.on('pageerror', error => {
    console.log('PAGE ERROR:', error.message);
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    console.log('REQUEST FAILED:', request.url(), request.failure().errorText);
  });

  try {
    console.log('Opening http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'domcontentloaded' });
    
    console.log('Page loaded, waiting 3 seconds to see what happens...');
    await page.waitForTimeout(3000);
    
    // Check what's on the page
    const bodyText = await page.locator('body').textContent();
    console.log('Page content:', bodyText.substring(0, 200));
    
    // Take screenshot
    await page.screenshot({ path: 'debug-screenshot.png' });
    console.log('Screenshot saved: debug-screenshot.png');
    
    // Check network activity
    console.log('\nChecking API calls...');
    
    // Make a direct API call to test
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('http://localhost:5001/api/check-auth', {
          credentials: 'include'
        });
        return {
          status: res.status,
          statusText: res.statusText,
          data: await res.text()
        };
      } catch (error) {
        return { error: error.message };
      }
    });
    
    console.log('Direct API call result:', response);
    
  } catch (error) {
    console.error('Test error:', error);
  } finally {
    console.log('\nKeeping browser open for inspection...');
    await page.waitForTimeout(10000);
    await browser.close();
  }
})();