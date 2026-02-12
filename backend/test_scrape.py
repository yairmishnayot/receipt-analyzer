"""Test script to diagnose scraping issues."""

import asyncio
from playwright.async_api import async_playwright

async def test_scrape():
    url = "https://osher.pairzon.com/dba51f17-81ac-41f8-b76d-64e62fb13df4.html?id=74588a50-4de7-4bd9-b41d-e551452b5b1c&p=1247"

    print(f"Testing scrape of: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navigate to URL
            print("1. Navigating to URL...")
            response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            print(f"   Response status: {response.status}")

            # Try waiting for networkidle
            print("2. Waiting for networkidle (60s timeout)...")
            try:
                await page.wait_for_load_state("networkidle", timeout=60000)
                print("   ✓ Networkidle reached")
            except Exception as e:
                print(f"   ✗ Networkidle timeout: {str(e)[:100]}")

            # Check for table
            print("3. Looking for table element...")
            try:
                await page.wait_for_selector("table", timeout=5000)
                print("   ✓ Table found")
            except:
                print("   ✗ No table found")

            # Check page title and some content
            print("4. Checking page content...")
            title = await page.title()
            print(f"   Title: {title}")

            # Get HTML content
            html = await page.content()
            print(f"   HTML length: {len(html)} characters")

            # Save HTML for inspection
            with open("/tmp/receipt_test.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("   Saved HTML to /tmp/receipt_test.html")

            # Look for specific elements
            print("5. Looking for receipt-specific elements...")
            try:
                # Try to find any div or table that might contain receipt data
                elements = await page.query_selector_all("table")
                print(f"   Found {len(elements)} table elements")

                divs = await page.query_selector_all("div")
                print(f"   Found {len(divs)} div elements")
            except Exception as e:
                print(f"   Error: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrape())
