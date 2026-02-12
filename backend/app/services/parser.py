"""Receipt parser service for extracting structured data from HTML."""

from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
import re
import logging

from app.models.receipt import ReceiptData, ReceiptItem

logger = logging.getLogger(__name__)


class ReceiptParserError(Exception):
    """Custom exception for parser errors."""
    pass


class ReceiptParser:
    """
    Parses Osher/Pairzon receipt HTML to extract structured data.

    This parser is specifically designed for the Osher/Pairzon receipt format
    and may not work with other receipt formats.
    """

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse_receipt(self, html: str, url: str) -> ReceiptData:
        """
        Parse receipt HTML and extract structured data.

        Args:
            html: HTML content of the receipt
            url: Original receipt URL

        Returns:
            ReceiptData object with extracted information

        Raises:
            ReceiptParserError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract different components
            date = self._extract_date(soup)
            store_name = self._extract_store_name(soup)
            transaction_id = self._extract_transaction_id(soup)
            items = self._extract_items(soup)
            total_amount = self._extract_total_amount(soup)

            return ReceiptData(
                date=date,
                store_name=store_name,
                items=items,
                total_amount=total_amount,
                transaction_id=transaction_id,
                url=url
            )

        except Exception as e:
            error_msg = f"Failed to parse receipt: {str(e)}"
            logger.error(error_msg)
            raise ReceiptParserError(error_msg) from e

    def _extract_date(self, soup: BeautifulSoup) -> datetime:
        """
        Extract receipt date and time.

        Looks for date/time information in common locations:
        - Meta tags
        - Specific div/span elements with date info
        - Transaction detail sections
        """
        # Try to find date in various formats
        # Look for common date patterns in the HTML

        # Strategy 1: Look for datetime in specific elements
        date_candidates = []

        # Look in all text content for date patterns
        text_content = soup.get_text()

        # Hebrew date patterns: DD/MM/YYYY or DD.MM.YYYY
        date_pattern = r'(\d{1,2})[/.](\d{1,2})[/.](\d{4})'
        date_matches = re.findall(date_pattern, text_content)

        if date_matches:
            # Take the first match
            day, month, year = date_matches[0]
            # Try to find time as well
            time_pattern = r'(\d{1,2}):(\d{2})'
            time_matches = re.findall(time_pattern, text_content)

            if time_matches:
                hour, minute = time_matches[0]
                return datetime(int(year), int(month), int(day), int(hour), int(minute))
            else:
                return datetime(int(year), int(month), int(day))

        # Fallback: use current date
        logger.warning("Could not extract date from receipt, using current date")
        return datetime.now()

    def _extract_store_name(self, soup: BeautifulSoup) -> str:
        """
        Extract store name from receipt header.

        Usually in a header section or prominent text element.
        """
        # Look for store name in header elements
        # Common patterns: h1, h2, or specific class names

        # Try h1 first
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        # Try h2
        h2 = soup.find("h2")
        if h2 and h2.get_text(strip=True):
            return h2.get_text(strip=True)

        # Try to find "אושר" or common store names
        text = soup.get_text()
        if "אושר" in text:
            return "אושר עד"

        # Look for any prominent text at the top
        body_text = soup.find("body")
        if body_text:
            # Get first significant text
            for element in body_text.find_all(["div", "span", "p"]):
                text = element.get_text(strip=True)
                if text and len(text) > 3 and len(text) < 50:
                    return text

        return "חנות לא ידועה"

    def _extract_transaction_id(self, soup: BeautifulSoup) -> str:
        """
        Extract transaction ID from receipt.

        Looks for transaction number, receipt number, or similar identifiers.
        """
        text_content = soup.get_text()

        # Look for common transaction ID patterns
        # Pattern: numbers after "מספר עסקה", "מס' עסקה", "Transaction", etc.
        patterns = [
            r'מספר עסקה[:\s]+(\d+)',
            r'מס[\'׳] עסקה[:\s]+(\d+)',
            r'עסקה[:\s]+(\d+)',
            r'Transaction[:\s]+(\d+)',
            r'מספר קבלה[:\s]+(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_content)
            if match:
                return match.group(1)

        # Fallback: look for any long number sequence
        numbers = re.findall(r'\d{6,}', text_content)
        if numbers:
            return numbers[0]

        # Last resort: generate from URL or timestamp
        return f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _extract_items(self, soup: BeautifulSoup) -> list[ReceiptItem]:
        """
        Extract items from receipt items table.

        Osher/Pairzon receipts have a specific structure:
        - Table with id="items-table"
        - Rows with: item name (class="i-name"), quantity (class="i-quantity"), price (class="i-price")
        """
        items = []

        # Find the items table specifically
        items_table = soup.find("table", id="items-table")

        if not items_table:
            logger.warning("items-table not found, trying fallback")
            return self._extract_items_fallback(soup)

        # Find all rows in the table
        rows = items_table.find_all("tr")

        for row in rows:
            # Skip header rows
            if row.find("th"):
                continue

            # Skip promotion/label rows (they don't have actual item data)
            if row.find(class_="label label-default"):
                continue

            # Extract item name
            name_element = row.find("dt", class_="i-name")
            if not name_element:
                continue

            item_name = name_element.get_text(strip=True)
            if not item_name:
                continue

            # Extract quantity
            quantity_element = row.find(class_="i-quantity")
            quantity = 1.0
            if quantity_element:
                quantity_text = quantity_element.get_text(strip=True)
                # Parse quantity - can be "1" or "0.508  ק"ג  6.90x" (weight items)
                quantity_match = re.search(r'^(\d+\.?\d*)', quantity_text)
                if quantity_match:
                    quantity = float(quantity_match.group(1))

            # Extract price
            price_element = row.find("dt", class_="i-price")
            if not price_element:
                continue

            price_text = price_element.get_text(strip=True)
            # Remove currency symbols and extract number
            # Format is typically "₪ 5.00" or "₪&nbsp;5.00"
            price_match = re.search(r'(\d+\.?\d*)', price_text)
            if not price_match:
                continue

            total_price = float(price_match.group(1))

            # Calculate unit price (total / quantity)
            unit_price = total_price / quantity if quantity > 0 else total_price

            # Create item
            item = ReceiptItem(
                name=item_name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                discount=None
            )
            items.append(item)

        if not items:
            logger.warning("No items found in items-table")

        return items

    def _extract_items_fallback(self, soup: BeautifulSoup) -> list[ReceiptItem]:
        """
        Fallback method to extract items if items-table is not found.
        Uses generic table parsing.
        """
        items = []
        logger.info("Using fallback item extraction method")

        # Find all tables
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                cells = row.find_all(["td", "th"])

                if len(cells) < 2:
                    continue

                # Look for cells with text and prices
                price_cells = []
                text_cells = []

                for cell in cells:
                    cell_text = cell.get_text(strip=True)

                    if re.search(r'\d+\.?\d*', cell_text):
                        price_cells.append(cell_text)
                    elif cell_text:
                        text_cells.append(cell_text)

                if text_cells and price_cells:
                    item_name = max(text_cells, key=len)

                    prices = []
                    for price_text in price_cells:
                        price_match = re.search(r'(\d+\.?\d*)', price_text)
                        if price_match:
                            prices.append(float(price_match.group(1)))

                    if not prices:
                        continue

                    if len(prices) >= 2:
                        quantity = 1.0
                        total_price = prices[-1]
                        unit_price = total_price
                    else:
                        quantity = 1.0
                        unit_price = prices[0]
                        total_price = prices[0]

                    item = ReceiptItem(
                        name=item_name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                        discount=None
                    )
                    items.append(item)

        return items

    def _extract_total_amount(self, soup: BeautifulSoup) -> float:
        """
        Extract total receipt amount.

        Looks for:
        - "סה\"כ" (total in Hebrew)
        - "Total"
        - Large numbers near end of receipt
        """
        text_content = soup.get_text()

        # Look for total patterns
        patterns = [
            r'סה["\']כ[:\s]+(\d+\.?\d*)',
            r'סך הכל[:\s]+(\d+\.?\d*)',
            r'Total[:\s]+(\d+\.?\d*)',
            r'סכום לתשלום[:\s]+(\d+\.?\d*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_content)
            if match:
                return float(match.group(1))

        # Fallback: find all prices and take the largest
        all_numbers = re.findall(r'\d+\.\d{2}', text_content)
        if all_numbers:
            prices = [float(n) for n in all_numbers]
            return max(prices)

        logger.warning("Could not extract total amount, returning 0.0")
        return 0.0


def parse_receipt_html(html: str, url: str) -> ReceiptData:
    """
    Convenience function to parse receipt HTML.

    Args:
        html: HTML content of receipt
        url: Original receipt URL

    Returns:
        ReceiptData object

    Raises:
        ReceiptParserError: If parsing fails
    """
    parser = ReceiptParser()
    return parser.parse_receipt(html, url)
