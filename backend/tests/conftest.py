"""Pytest configuration and fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient
from app.config import settings


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_receipt_html():
    """Sample receipt HTML for testing parser."""
    return """
    <html>
        <body>
            <h1>אושר עד</h1>
            <div>תאריך: 15/01/2024</div>
            <div>שעה: 10:30</div>
            <div>מספר עסקה: 12345</div>
            <table>
                <tr>
                    <td>חלב 3%</td>
                    <td>1</td>
                    <td>5.90</td>
                    <td>5.90</td>
                </tr>
                <tr>
                    <td>לחם</td>
                    <td>2</td>
                    <td>4.50</td>
                    <td>9.00</td>
                </tr>
            </table>
            <div>סה"כ: 14.90</div>
        </body>
    </html>
    """


@pytest.fixture
def sample_receipt_url():
    """Sample receipt URL for testing."""
    return "https://osher.pairzon.com/test-receipt.html"
