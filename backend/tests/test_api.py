"""Tests for API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from app.models.receipt import ReceiptData, ReceiptItem
from datetime import datetime


def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Receipt Analyzer API" in response.json()["message"]


def test_receipt_process_invalid_url(test_client):
    """Test receipt processing with invalid URL."""
    response = test_client.post(
        "/api/receipt/process",
        json={"url": "not-a-url"}
    )
    assert response.status_code == 422  # Validation error


@patch('app.api.routes.receipt.scrape_receipt_url')
@patch('app.api.routes.receipt.parse_receipt_html')
@patch('app.api.routes.receipt.SheetsService')
def test_receipt_process_success(mock_sheets, mock_parser, mock_scraper, test_client):
    """Test successful receipt processing."""
    # Mock scraper
    mock_scraper.return_value = "<html>test</html>"

    # Mock parser
    mock_receipt_data = ReceiptData(
        date=datetime(2024, 1, 15, 10, 30),
        store_name="Test Store",
        items=[
            ReceiptItem(
                name="Test Item",
                quantity=1.0,
                unit_price=10.0,
                total_price=10.0,
                discount=None
            )
        ],
        total_amount=10.0,
        transaction_id="12345",
        url="https://test.com"
    )
    mock_parser.return_value = mock_receipt_data

    # Mock sheets service
    mock_sheets_instance = AsyncMock()
    mock_sheets_instance.update_sheets.return_value = AsyncMock(success=True, message="Success")
    mock_sheets.return_value = mock_sheets_instance

    # Test
    response = test_client.post(
        "/api/receipt/process",
        json={"url": "https://test.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
