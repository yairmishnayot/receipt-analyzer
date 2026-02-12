"""Tests for receipt parser service."""

import pytest
from app.services.parser import ReceiptParser, parse_receipt_html, ReceiptParserError


def test_parser_extracts_store_name(sample_receipt_html, sample_receipt_url):
    """Test that parser extracts store name."""
    receipt_data = parse_receipt_html(sample_receipt_html, sample_receipt_url)
    assert receipt_data.store_name == "אושר עד"


def test_parser_extracts_items(sample_receipt_html, sample_receipt_url):
    """Test that parser extracts items."""
    receipt_data = parse_receipt_html(sample_receipt_html, sample_receipt_url)
    assert len(receipt_data.items) > 0


def test_parser_extracts_total(sample_receipt_html, sample_receipt_url):
    """Test that parser extracts total amount."""
    receipt_data = parse_receipt_html(sample_receipt_html, sample_receipt_url)
    assert receipt_data.total_amount == 14.90


def test_parser_extracts_transaction_id(sample_receipt_html, sample_receipt_url):
    """Test that parser extracts transaction ID."""
    receipt_data = parse_receipt_html(sample_receipt_html, sample_receipt_url)
    assert receipt_data.transaction_id == "12345"


def test_parser_handles_invalid_html(sample_receipt_url):
    """Test that parser handles invalid HTML gracefully."""
    invalid_html = "<html><body></body></html>"
    # Should not raise, but may have default values
    receipt_data = parse_receipt_html(invalid_html, sample_receipt_url)
    assert receipt_data.url == sample_receipt_url
