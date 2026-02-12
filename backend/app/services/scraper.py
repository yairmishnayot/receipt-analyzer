"""Receipt scraping service using Playwright for JavaScript-rendered content."""

import asyncio
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ReceiptScraperError(Exception):
    """Custom exception for scraper errors."""
    pass


class ReceiptScraper:
    """Scrapes receipt HTML using Playwright headless browser."""

    def __init__(self, timeout: int = 30000):
        """
        Initialize the receipt scraper.

        Args:
            timeout: Timeout in milliseconds for page load and operations
        """
        self.timeout = timeout
        self._browser: Optional[Browser] = None

    async def __aenter__(self):
        """Context manager entry - initialize browser."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser."""
        await self.close()

    async def close(self):
        """Close the browser if it's open."""
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def scrape_receipt(self, url: str) -> str:
        """
        Scrape a receipt URL and return fully rendered HTML.

        This method:
        1. Launches a headless Chromium browser
        2. Navigates to the receipt URL
        3. Waits for dynamic content to load
        4. Extracts and returns the fully rendered HTML

        Args:
            url: Receipt URL to scrape

        Returns:
            Fully rendered HTML content as string

        Raises:
            ReceiptScraperError: If scraping fails for any reason
        """
        try:
            logger.info(f"Starting to scrape receipt: {url}")

            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                self._browser = browser

                try:
                    # Create new page
                    page: Page = await browser.new_page()

                    # Navigate to URL
                    logger.info(f"Navigating to URL: {url}")
                    await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

                    # Wait for the receipt content to be populated
                    # The receipt uses JavaScript events to populate content
                    # Note: We don't wait for networkidle because the site continues making
                    # background requests indefinitely. Instead, we wait for the actual content.

                    # Wait for specific elements that indicate receipt is loaded
                    try:
                        # Wait for the items table (this indicates receipt data is loaded)
                        await page.wait_for_selector("table#items-table", timeout=15000)
                        logger.info("Receipt items table found")
                    except PlaywrightTimeout:
                        # Fallback: try waiting for any table
                        logger.warning("Items table not found, trying any table...")
                        try:
                            await page.wait_for_selector("table", timeout=5000)
                            logger.info("Generic table found")
                        except PlaywrightTimeout:
                            logger.warning("No table found, continuing anyway")

                    # Give a bit more time for any remaining JavaScript to execute
                    await asyncio.sleep(2)

                    # Extract HTML
                    html_content = await page.content()
                    logger.info(f"Successfully scraped {len(html_content)} characters of HTML")

                    return html_content

                finally:
                    # Cleanup
                    await browser.close()
                    self._browser = None

        except PlaywrightTimeout as e:
            error_msg = f"Timeout while loading receipt: {url}"
            logger.error(error_msg)
            raise ReceiptScraperError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to scrape receipt: {str(e)}"
            logger.error(error_msg)
            raise ReceiptScraperError(error_msg) from e


async def scrape_receipt_url(url: str, timeout: int = 30000) -> str:
    """
    Convenience function to scrape a receipt URL.

    Args:
        url: Receipt URL to scrape
        timeout: Timeout in milliseconds

    Returns:
        Fully rendered HTML content

    Raises:
        ReceiptScraperError: If scraping fails
    """
    async with ReceiptScraper(timeout=timeout) as scraper:
        return await scraper.scrape_receipt(url)
