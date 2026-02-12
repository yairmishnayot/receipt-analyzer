"""API routes for receipt processing."""

from fastapi import APIRouter, HTTPException, status
import logging

from app.models.receipt import ReceiptRequest, ReceiptResponse
from app.services.scraper import scrape_receipt_url, ReceiptScraperError
from app.services.parser import parse_receipt_html, ReceiptParserError
from app.services.classifier import ItemClassifier, ItemClassifierError
from app.services.sheets import SheetsService, SheetsServiceError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/receipt", tags=["receipt"])


@router.post("/process", response_model=ReceiptResponse)
async def process_receipt(request: ReceiptRequest):
    """
    Process a receipt URL: scrape, parse, and update Google Sheets.

    Args:
        request: ReceiptRequest containing the receipt URL

    Returns:
        ReceiptResponse with success status and extracted data

    Raises:
        HTTPException: On various error conditions
    """
    url = str(request.url)
    logger.info(f"Processing receipt: {url}")

    try:
        # Step 1: Scrape the receipt
        logger.info("Scraping receipt HTML")
        try:
            html = await scrape_receipt_url(url, timeout=settings.scraping_timeout)
        except ReceiptScraperError as e:
            logger.error(f"Scraping failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"שגיאה בטעינת הקבלה: {str(e)}"
            )

        # Step 2: Parse the receipt
        logger.info("Parsing receipt data")
        try:
            receipt_data = parse_receipt_html(html, url)
        except ReceiptParserError as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"שגיאה בפענוח הקבלה: {str(e)}"
            )

        # Step 3: Classify items into categories
        logger.info("Classifying receipt items")
        try:
            classifier = ItemClassifier()
            receipt_data.items = await classifier.classify_items(receipt_data.items)
        except ItemClassifierError as e:
            logger.error(f"Classification failed: {str(e)}")
            # Non-fatal: continue without categories
            logger.warning("Continuing without item categories")

        # Step 4: Check for duplicates
        logger.info("Checking for duplicate receipt")
        sheets_service = SheetsService()
        duplicate_info = sheets_service.check_duplicate(receipt_data.transaction_id)

        if duplicate_info and not request.force_update:
            # Duplicate found and user hasn't confirmed override
            logger.warning(f"Duplicate receipt found: {receipt_data.transaction_id}")
            return ReceiptResponse(
                success=False,
                message=f"קבלה זו כבר עובדה בעבר (מזהה עסקה: {receipt_data.transaction_id}). האם לעדכן?",
                data=receipt_data,
                is_duplicate=True,
                duplicate_info=duplicate_info
            )

        # Step 5: Update or insert into Google Sheets
        logger.info("Updating Google Sheets")
        try:
            if duplicate_info and request.force_update:
                # Update existing receipt
                logger.info(f"Updating existing receipt: {receipt_data.transaction_id}")
                update_result = await sheets_service.update_existing_receipt(receipt_data)
                message = "הקבלה עודכנה בהצלחה בגיליון"
            else:
                # Insert new receipt
                logger.info(f"Inserting new receipt: {receipt_data.transaction_id}")
                update_result = await sheets_service.update_sheets(receipt_data)
                message = "הקבלה עובדה בהצלחה ונשמרה בגיליון"

            if not update_result.success:
                raise SheetsServiceError(update_result.message)

            logger.info(f"Successfully processed receipt: {receipt_data.transaction_id}")

        except SheetsServiceError as e:
            logger.error(f"Sheets update failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"שגיאה בעדכון הגיליון: {str(e)}"
            )

        # Return success response
        return ReceiptResponse(
            success=True,
            message=message,
            data=receipt_data,
            is_duplicate=bool(duplicate_info and request.force_update)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception(f"Unexpected error processing receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בלתי צפויה: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "receipt-analyzer-backend"
    }
