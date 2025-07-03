const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 500 
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    console.log('Starting authentication test...');
    
    try {
        // Navigate to the application
        console.log('1. Navigating to http://localhost:3001...');
        await page.goto('http://localhost:3001');
        await page.waitForTimeout(2000);
        
        // Check if we're on the login page
        const loginTitle = await page.locator('h2').textContent();
        console.log('2. Page title:', loginTitle);
        
        // Look for the password input
        const passwordInput = await page.locator('input[type="password"]');
        if (await passwordInput.isVisible()) {
            console.log('3. Found password input field');
            
            // Enter the password
            console.log('4. Entering password: MIAMI');
            await passwordInput.fill('MIAMI');
            await page.waitForTimeout(1000);
            
            // Click the login button
            const loginButton = await page.locator('button:has-text("Login")');
            console.log('5. Clicking login button...');
            await loginButton.click();
            
            // Wait for navigation or error
            await page.waitForTimeout(3000);
            
            // Check if we're still on login page (error) or redirected
            const currentUrl = page.url();
            console.log('6. Current URL:', currentUrl);
            
            // Check for error messages
            const errorMessage = await page.locator('.alert-danger').textContent().catch(() => null);
            if (errorMessage) {
                console.log('7. Error message:', errorMessage);
            } else {
                console.log('7. No error message - checking if authenticated');
                
                // Check if we see the main app content
                const mainContent = await page.locator('.container').first().textContent();
                if (mainContent.includes('GymMolly Order Management')) {
                    console.log('8. Successfully authenticated! Main app is visible');
                } else {
                    console.log('8. Page content:', mainContent.substring(0, 100) + '...');
                }
            }
            
            // Check network tab for API calls
            console.log('\n9. Monitoring network requests...');
            page.on('request', request => {
                if (request.url().includes('localhost:')) {
                    console.log('   Request to:', request.url());
                }
            });
            
            // Try to access an API endpoint directly
            console.log('\n10. Testing API endpoint directly...');
            const apiResponse = await page.evaluate(async () => {
                try {
                    const response = await fetch('http://localhost:5001/api/inventory', {
                        credentials: 'include'
                    });
                    return {
                        status: response.status,
                        ok: response.ok,
                        url: response.url
                    };
                } catch (error) {
                    return { error: error.message };
                }
            });
            console.log('    API Response:', apiResponse);
            
        } else {
            console.log('ERROR: Password input not found - page might not have loaded correctly');
        }
        
    } catch (error) {
        console.error('Test error:', error.message);
    }
    
    console.log('\nTest completed. Browser will remain open for inspection.');
    console.log('Press Ctrl+C to exit...');
    
    // Keep browser open
    await page.waitForTimeout(300000);
})();