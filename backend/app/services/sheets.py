"""Google Sheets integration service for storing receipt data."""

from datetime import datetime
from typing import Optional
import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.receipt import ReceiptData, SheetsUpdateResult
from app.config import settings

logger = logging.getLogger(__name__)


class SheetsServiceError(Exception):
    """Custom exception for Google Sheets service errors."""
    pass


class SheetsService:
    """
    Service for updating Google Sheets with receipt data.

    Manages two sheets:
    1. "Receipt Summary" - One row per receipt
    2. "Receipt Items" - One row per item
    """

    SUMMARY_SHEET_NAME = "סיכום קבלות"  # "Receipt Summary" in Hebrew
    ITEMS_SHEET_NAME = "פרטי קבלות"

    # Hebrew month names mapping
    HEBREW_MONTHS = {
        1: "ינואר",
        2: "פברואר",
        3: "מרץ",
        4: "אפריל",
        5: "מאי",
        6: "יוני",
        7: "יולי",
        8: "אוגוסט",
        9: "ספטמבר",
        10: "אוקטובר",
        11: "נובמבר",
        12: "דצמבר"
    }

    # Column headers (in Hebrew)
    SUMMARY_HEADERS = [
        "תאריך",           # Date
        "חודש",            # Month
        "סכום כולל",       # Total Amount
        "מזהה עסקה",       # Transaction ID (CRITICAL for duplicate detection)
        "עדכון אחרון",     # Last Updated
        "קישור לקבלה"     # Receipt URL
    ]
    ITEMS_HEADERS = [
        "תאריך קבלה",      # Receipt Date
        "חודש",            # Month
        "מזהה עסקה",       # Transaction ID (CRITICAL for linking)
        "שם פריט",         # Item Name
        "קטגוריה",         # Category
        "כמות",            # Quantity
        "מחיר ליחידה",     # Unit Price
        "מחיר כולל",       # Total Price
        "הנחה",            # Discount
        "קישור לקבלה"     # Receipt URL
    ]

    def __init__(self, credentials_path: Optional[str] = None, spreadsheet_id: Optional[str] = None):
        """
        Initialize the Sheets service.

        Args:
            credentials_path: Path to service account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_path = credentials_path or settings.google_sheets_credentials_path
        self.spreadsheet_id = spreadsheet_id or settings.google_sheets_id
        self._service = None

    def _get_service(self):
        """
        Get or create Google Sheets API service instance.

        Returns:
            Google Sheets API service

        Raises:
            SheetsServiceError: If authentication fails
        """
        if self._service:
            return self._service

        try:
            # Load credentials
            creds_path = Path(self.credentials_path)
            if not creds_path.exists():
                raise SheetsServiceError(f"Credentials file not found: {self.credentials_path}")

            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

            # Build service
            self._service = build('sheets', 'v4', credentials=credentials)
            return self._service

        except Exception as e:
            error_msg = f"Failed to authenticate with Google Sheets: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

    async def update_sheets(self, receipt_data: ReceiptData) -> SheetsUpdateResult:
        """
        Update both summary and items sheets with receipt data.

        This method:
        1. Finds the correct date-sorted position
        2. Inserts summary row in "Receipt Summary" sheet
        3. Inserts item rows in "Receipt Items" sheet

        Args:
            receipt_data: Receipt data to insert

        Returns:
            SheetsUpdateResult with row numbers and status

        Raises:
            SheetsServiceError: If update fails
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Ensure sheets exist with headers
            self._ensure_sheets_exist(sheet)

            # Get summary sheet data to find insert position
            summary_position = self._find_insert_position(sheet, receipt_data.date)

            # Insert summary row
            summary_row = self._create_summary_row(receipt_data)
            summary_row_num = self._insert_row(
                sheet,
                self.SUMMARY_SHEET_NAME,
                summary_position,
                summary_row
            )

            # Insert item rows
            items_rows = self._create_items_rows(receipt_data)
            items_row_nums = []

            for item_row in items_rows:
                # Insert all items at the same position (they'll stack)
                row_num = self._insert_row(
                    sheet,
                    self.ITEMS_SHEET_NAME,
                    2,  # Always insert after header (position 2)
                    item_row
                )
                items_row_nums.append(row_num)

            return SheetsUpdateResult(
                success=True,
                summary_row=summary_row_num,
                items_rows=items_row_nums,
                message=f"Successfully updated sheets. Summary row: {summary_row_num}, Items rows: {len(items_row_nums)}"
            )

        except HttpError as e:
            error_msg = f"Google Sheets API error: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to update sheets: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

    def check_duplicate(self, transaction_id: str) -> Optional[dict]:
        """
        Check if a transaction ID already exists in the sheets.

        Args:
            transaction_id: Transaction ID to check

        Returns:
            Dictionary with duplicate info if found, None otherwise.
            Format: {"exists": True, "summary_row": 5, "item_rows": [10, 11, 12]}
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Check summary sheet for transaction ID (column D - index 3: Date, Month, Total, TransactionID)
            range_name = f"{self.SUMMARY_SHEET_NAME}!D:D"
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            # Find row with matching transaction ID
            summary_row = None
            for i, row in enumerate(values[1:], start=2):  # Skip header
                if row and row[0] == transaction_id:
                    summary_row = i
                    break

            if not summary_row:
                return None

            # Find all item rows with this transaction ID (column C - index 2: Date, Month, TransactionID)
            items_range = f"{self.ITEMS_SHEET_NAME}!C:C"
            items_result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=items_range
            ).execute()

            items_values = items_result.get('values', [])
            item_rows = []
            for i, row in enumerate(items_values[1:], start=2):  # Skip header
                if row and row[0] == transaction_id:
                    item_rows.append(i)

            return {
                "exists": True,
                "summary_row": summary_row,
                "item_rows": item_rows,
                "transaction_id": transaction_id
            }

        except Exception as e:
            logger.error(f"Failed to check for duplicates: {str(e)}")
            return None

    async def update_existing_receipt(self, receipt_data: ReceiptData) -> SheetsUpdateResult:
        """
        Update an existing receipt in the sheets.

        This method:
        1. Finds the existing summary row by transaction_id
        2. Updates the summary row
        3. Updates existing item rows in place
        4. Deletes extra item rows if new receipt has fewer items
        5. Inserts new item rows if new receipt has more items

        Args:
            receipt_data: Receipt data to update

        Returns:
            SheetsUpdateResult with updated row numbers

        Raises:
            SheetsServiceError: If update fails
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Check if receipt exists
            duplicate_info = self.check_duplicate(receipt_data.transaction_id)
            if not duplicate_info:
                raise SheetsServiceError(f"Receipt with transaction ID {receipt_data.transaction_id} not found")

            summary_row = duplicate_info["summary_row"]
            old_item_rows = sorted(duplicate_info["item_rows"])  # Sort ascending

            # Update summary row
            summary_row_data = self._create_summary_row(receipt_data)
            summary_range = f"{self.SUMMARY_SHEET_NAME}!A{summary_row}"
            sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=summary_range,
                valueInputOption='RAW',
                body={'values': [summary_row_data]}
            ).execute()

            logger.info(f"Updated summary row {summary_row} for transaction {receipt_data.transaction_id}")

            # Get new item rows
            new_items_rows = self._create_items_rows(receipt_data)
            old_item_count = len(old_item_rows)
            new_item_count = len(new_items_rows)

            updated_item_rows = []

            # Update existing rows in place
            rows_to_update = min(old_item_count, new_item_count)
            for i in range(rows_to_update):
                row_num = old_item_rows[i]
                item_data = new_items_rows[i]
                item_range = f"{self.ITEMS_SHEET_NAME}!A{row_num}"
                sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=item_range,
                    valueInputOption='RAW',
                    body={'values': [item_data]}
                ).execute()
                updated_item_rows.append(row_num)

            logger.info(f"Updated {rows_to_update} item rows in place")

            # Handle difference in item counts
            if new_item_count < old_item_count:
                # Delete extra rows (in reverse order to maintain row numbers)
                rows_to_delete = old_item_rows[new_item_count:]
                for row_num in reversed(rows_to_delete):
                    self._delete_row(sheet, self.ITEMS_SHEET_NAME, row_num)
                logger.info(f"Deleted {len(rows_to_delete)} extra item rows")

            elif new_item_count > old_item_count:
                # Insert additional rows AFTER the last existing item row to keep items together
                additional_items = new_items_rows[old_item_count:]
                insert_position = old_item_rows[-1] + 1  # After last existing row

                for item_row in additional_items:
                    row_num = self._insert_row(
                        sheet,
                        self.ITEMS_SHEET_NAME,
                        insert_position,
                        item_row
                    )
                    updated_item_rows.append(row_num)
                    insert_position += 1  # Next insertion position
                logger.info(f"Inserted {len(additional_items)} additional item rows after row {old_item_rows[-1]}")

            return SheetsUpdateResult(
                success=True,
                summary_row=summary_row,
                items_rows=updated_item_rows,
                message=f"Successfully updated receipt. Summary row: {summary_row}, Updated/Inserted items: {len(updated_item_rows)}"
            )

        except HttpError as e:
            error_msg = f"Google Sheets API error during update: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to update existing receipt: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

    def update_item_category_in_sheets(self, item_name: str, new_category: str) -> int:
        """
        Update the category for all occurrences of an item in the Items sheet.

        Args:
            item_name: Name of the item to update
            new_category: New category to set

        Returns:
            Number of rows updated

        Raises:
            SheetsServiceError: If update fails
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Get all item names from column D (Item Name)
            items_range = f"{self.ITEMS_SHEET_NAME}!D:D"
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=items_range
            ).execute()

            values = result.get('values', [])

            # Find all rows with matching item name
            rows_to_update = []
            for i, row in enumerate(values[1:], start=2):  # Skip header
                if row and row[0] == item_name:
                    rows_to_update.append(i)

            if not rows_to_update:
                logger.warning(f"No rows found with item name '{item_name}'")
                return 0

            # Update category (column E) for all matching rows
            for row_num in rows_to_update:
                category_range = f"{self.ITEMS_SHEET_NAME}!E{row_num}"
                sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=category_range,
                    valueInputOption='RAW',
                    body={'values': [[new_category]]}
                ).execute()

            logger.info(f"Updated category to '{new_category}' for {len(rows_to_update)} rows with item '{item_name}'")
            return len(rows_to_update)

        except HttpError as e:
            error_msg = f"Google Sheets API error while updating item category: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to update item category in sheets: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

    def rename_category_in_sheets(self, old_category: str, new_category: str) -> int:
        """
        Rename category in all rows of Items sheet (column E).

        Args:
            old_category: Current category name to rename
            new_category: New category name

        Returns:
            Number of rows updated

        Raises:
            SheetsServiceError: If update fails
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Get all categories from column E (Category)
            categories_range = f"{self.ITEMS_SHEET_NAME}!E:E"
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=categories_range
            ).execute()

            values = result.get('values', [])

            # Find all rows with matching category
            rows_to_update = []
            for i, row in enumerate(values[1:], start=2):  # Skip header
                if row and row[0] == old_category:
                    rows_to_update.append(i)

            if not rows_to_update:
                logger.info(f"No rows found with category '{old_category}'")
                return 0

            # Batch update all matching rows using batchUpdate API for efficiency
            data = []
            for row_num in rows_to_update:
                data.append({
                    'range': f"{self.ITEMS_SHEET_NAME}!E{row_num}",
                    'values': [[new_category]]
                })

            if data:
                body = {
                    'valueInputOption': 'RAW',
                    'data': data
                }
                sheet.values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()

            logger.info(f"Renamed category from '{old_category}' to '{new_category}' in {len(rows_to_update)} rows")
            return len(rows_to_update)

        except HttpError as e:
            error_msg = f"Google Sheets API error while renaming category: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to rename category in sheets: {str(e)}"
            logger.error(error_msg)
            raise SheetsServiceError(error_msg) from e

    def _delete_row(self, sheet, sheet_name: str, row_number: int):
        """
        Delete a specific row from a sheet.

        Args:
            sheet: Sheets API service
            sheet_name: Name of the sheet
            row_number: Row number to delete (1-indexed)
        """
        try:
            request_body = {
                'requests': [{
                    'deleteDimension': {
                        'range': {
                            'sheetId': self._get_sheet_id(sheet, sheet_name),
                            'dimension': 'ROWS',
                            'startIndex': row_number - 1,  # 0-indexed
                            'endIndex': row_number
                        }
                    }
                }]
            }
            sheet.batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body).execute()
            logger.debug(f"Deleted row {row_number} from {sheet_name}")

        except Exception as e:
            logger.error(f"Failed to delete row {row_number}: {str(e)}")
            raise

    def _ensure_sheets_exist(self, sheet):
        """
        Ensure both sheets exist with proper headers.

        Creates sheets if they don't exist and adds headers.
        Updates headers if sheets already exist.
        """
        try:
            # Get spreadsheet metadata
            spreadsheet = sheet.get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheets = {s['properties']['title'] for s in spreadsheet['sheets']}

            # Create summary sheet if needed
            if self.SUMMARY_SHEET_NAME not in existing_sheets:
                logger.info(f"Creating {self.SUMMARY_SHEET_NAME} sheet")
                self._create_sheet(sheet, self.SUMMARY_SHEET_NAME, self.SUMMARY_HEADERS)
            else:
                # Update headers if sheet already exists
                logger.info(f"Updating headers for {self.SUMMARY_SHEET_NAME} sheet")
                self._update_headers(sheet, self.SUMMARY_SHEET_NAME, self.SUMMARY_HEADERS)

            # Create items sheet if needed
            if self.ITEMS_SHEET_NAME not in existing_sheets:
                logger.info(f"Creating {self.ITEMS_SHEET_NAME} sheet")
                self._create_sheet(sheet, self.ITEMS_SHEET_NAME, self.ITEMS_HEADERS)
            else:
                # Update headers if sheet already exists
                logger.info(f"Updating headers for {self.ITEMS_SHEET_NAME} sheet")
                self._update_headers(sheet, self.ITEMS_SHEET_NAME, self.ITEMS_HEADERS)

        except Exception as e:
            logger.error(f"Failed to ensure sheets exist: {str(e)}")
            raise

    def _create_sheet(self, sheet, sheet_name: str, headers: list[str]):
        """Create a new sheet with headers."""
        try:
            # Add sheet
            request_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            sheet.batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body).execute()

            # Add headers
            self._update_headers(sheet, sheet_name, headers)

        except Exception as e:
            logger.error(f"Failed to create sheet {sheet_name}: {str(e)}")
            raise

    def _update_headers(self, sheet, sheet_name: str, headers: list[str]):
        """Update the header row of an existing sheet."""
        try:
            range_name = f"{sheet_name}!A1"
            value_range_body = {
                'values': [headers]
            }
            sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=value_range_body
            ).execute()
            logger.info(f"Updated headers for {sheet_name}")

        except Exception as e:
            logger.error(f"Failed to update headers for {sheet_name}: {str(e)}")
            raise

    def _find_insert_position(self, sheet, receipt_date: datetime) -> int:
        """
        Find the correct position to insert a receipt based on date.

        Reads existing dates and finds where to insert to maintain chronological order.

        Args:
            sheet: Sheets API service
            receipt_date: Date of the receipt to insert

        Returns:
            Row number where receipt should be inserted (1-indexed)
        """
        try:
            # Read all dates from summary sheet
            range_name = f"{self.SUMMARY_SHEET_NAME}!A:A"
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            # If empty or only header, insert at row 2
            if len(values) <= 1:
                return 2

            # Parse dates (skip header)
            dates_with_rows = []
            for i, row in enumerate(values[1:], start=2):
                if row:
                    try:
                        date_str = row[0]
                        # Try to parse date in dd-mm-YYYY format
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                        dates_with_rows.append((date_obj, i))
                    except (ValueError, IndexError):
                        # Fallback: try old ISO format for backwards compatibility
                        try:
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            dates_with_rows.append((date_obj, i))
                        except (ValueError, IndexError):
                            continue

            # If no valid dates, insert at row 2
            if not dates_with_rows:
                return 2

            # Find insertion point (sorted ascending)
            for date_obj, row_num in dates_with_rows:
                if receipt_date < date_obj:
                    return row_num

            # If newer than all dates, insert at end
            return len(values) + 1

        except Exception as e:
            logger.warning(f"Failed to find insert position, defaulting to end: {str(e)}")
            # Default to appending at end
            return -1  # Will be handled by _insert_row

    def _insert_row(self, sheet, sheet_name: str, position: int, row_data: list) -> int:
        """
        Insert a row at the specified position.

        Args:
            sheet: Sheets API service
            sheet_name: Name of the sheet
            position: Row number to insert at (1-indexed), or -1 to append
            row_data: List of cell values

        Returns:
            Row number where data was inserted
        """
        try:
            if position == -1:
                # Append to end
                range_name = f"{sheet_name}!A:A"
                body = {'values': [row_data]}
                result = sheet.values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                # Extract row number from update
                updated_range = result.get('updates', {}).get('updatedRange', '')
                match = __import__('re').search(r'!A(\d+):', updated_range)
                return int(match.group(1)) if match else -1
            else:
                # Insert at specific position
                # First, insert a blank row
                request_body = {
                    'requests': [{
                        'insertDimension': {
                            'range': {
                                'sheetId': self._get_sheet_id(sheet, sheet_name),
                                'dimension': 'ROWS',
                                'startIndex': position - 1,
                                'endIndex': position
                            }
                        }
                    }]
                }
                sheet.batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body).execute()

                # Then, write data to that row
                range_name = f"{sheet_name}!A{position}"
                body = {'values': [row_data]}
                sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()

                return position

        except Exception as e:
            logger.error(f"Failed to insert row: {str(e)}")
            raise

    def _get_sheet_id(self, sheet, sheet_name: str) -> int:
        """Get the sheet ID for a given sheet name."""
        spreadsheet = sheet.get(spreadsheetId=self.spreadsheet_id).execute()
        for s in spreadsheet['sheets']:
            if s['properties']['title'] == sheet_name:
                return s['properties']['sheetId']
        raise ValueError(f"Sheet not found: {sheet_name}")

    def _create_summary_row(self, receipt_data: ReceiptData) -> list:
        """
        Create a summary row for the Receipt Summary sheet.

        Returns list: [Date, Month, Total Amount, Transaction ID, Last Updated, Receipt URL]
        """
        from datetime import datetime
        return [
            receipt_data.date.strftime('%d-%m-%Y'),
            self.HEBREW_MONTHS[receipt_data.date.month],  # Month in Hebrew (e.g., "ינואר")
            receipt_data.total_amount,
            receipt_data.transaction_id,
            datetime.now().strftime('%d-%m-%Y %H:%M:%S'),  # Last Updated timestamp
            receipt_data.url
        ]

    def _create_items_rows(self, receipt_data: ReceiptData) -> list[list]:
        """
        Create item rows for the Receipt Items sheet.

        Returns list of lists, each containing:
        [Receipt Date, Month, Transaction ID, Item Name, Category, Quantity, Unit Price, Total Price, Discount, Receipt URL]
        """
        rows = []
        for item in receipt_data.items:
            row = [
                receipt_data.date.strftime('%d-%m-%Y'),
                self.HEBREW_MONTHS[receipt_data.date.month],  # Month in Hebrew (e.g., "ינואר")
                receipt_data.transaction_id,
                item.name,
                item.category if item.category else "אחר",
                item.quantity,
                item.unit_price,
                item.total_price,
                item.discount if item.discount else "",
                receipt_data.url
            ]
            rows.append(row)
        return rows
