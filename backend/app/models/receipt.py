"""Pydantic models for receipt data structures."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field, field_serializer


class ReceiptItem(BaseModel):
    """Represents a single item on a receipt."""

    name: str = Field(..., description="Product name")
    quantity: float = Field(..., description="Quantity or weight of the item")
    unit_price: float = Field(..., description="Price per unit")
    total_price: float = Field(..., description="Total price for this item")
    discount: Optional[float] = Field(None, description="Discount amount if any")
    category: Optional[str] = Field(None, description="Item category (e.g., Dairy, Produce)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "חלב 3%",
                "quantity": 1.0,
                "unit_price": 5.90,
                "total_price": 5.90,
                "discount": None,
                "category": "חלבי"
            }
        }


class ReceiptData(BaseModel):
    """Represents complete receipt data extracted from a receipt."""

    date: datetime = Field(..., description="Receipt date and time")
    store_name: str = Field(..., description="Store name")
    items: list[ReceiptItem] = Field(..., description="List of items on the receipt")
    total_amount: float = Field(..., description="Total receipt amount")
    transaction_id: str = Field(..., description="Unique transaction identifier")
    url: str = Field(..., description="Original receipt URL")

    @field_serializer('date')
    def serialize_date(self, dt: datetime, _info):
        """Serialize date to dd-mm-YYYY format for API responses."""
        return dt.strftime('%d-%m-%Y')

    class Config:
        json_schema_extra = {
            "example": {
                "date": "15-01-2024",
                "store_name": "אושר עד",
                "items": [
                    {
                        "name": "חלב 3%",
                        "quantity": 1.0,
                        "unit_price": 5.90,
                        "total_price": 5.90,
                        "discount": None
                    }
                ],
                "total_amount": 125.50,
                "transaction_id": "12345",
                "url": "https://osher.pairzon.com/..."
            }
        }


class ReceiptRequest(BaseModel):
    """Request model for receipt processing endpoint."""

    url: HttpUrl = Field(..., description="Receipt URL to process")
    force_update: bool = Field(default=False, description="Force update if duplicate found")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://osher.pairzon.com/dba51f17-81ac-41f8-b76d-64e62fb13df4.html",
                "force_update": False
            }
        }


class ReceiptResponse(BaseModel):
    """Response model for receipt processing endpoint."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message (in Hebrew)")
    data: Optional[ReceiptData] = Field(None, description="Extracted receipt data if successful")
    is_duplicate: bool = Field(default=False, description="Whether this is a duplicate receipt")
    duplicate_info: Optional[dict] = Field(None, description="Information about the duplicate if found")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "הקבלה עובדה בהצלחה",
                "data": {
                    "date": "15-01-2024",
                    "store_name": "אושר עד",
                    "items": [],
                    "total_amount": 125.50,
                    "transaction_id": "12345",
                    "url": "https://osher.pairzon.com/..."
                }
            }
        }


class SheetsUpdateResult(BaseModel):
    """Result of Google Sheets update operation."""

    success: bool = Field(..., description="Whether the update was successful")
    summary_row: Optional[int] = Field(None, description="Row number in summary sheet")
    items_rows: Optional[list[int]] = Field(None, description="Row numbers in items sheet")
    message: str = Field(..., description="Result message")
