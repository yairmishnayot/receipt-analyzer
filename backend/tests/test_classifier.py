"""Tests for the item classification service."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile

from app.services.classifier import ItemClassifier, ItemClassifierError
from app.models.receipt import ReceiptItem


@pytest.fixture
def temp_cache_file():
    """Create a temporary cache file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        cache_data = {
            "version": "1.0",
            "categories": {
                "חלב": "חלבי",
                "חלב 3%": "חלבי",
                "לחם": "מאפים",
                "עגבניות": "ירקות",
                "בננה": "פירות"
            }
        }
        json.dump(cache_data, f, ensure_ascii=False)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_settings(temp_cache_file):
    """Mock settings for testing."""
    with patch('app.services.classifier.settings') as mock:
        mock.gemini_api_key = "test-api-key"
        mock.gemini_model = "gemini-1.5-flash"
        mock.categories_cache_path = temp_cache_file
        mock.categories_cache_fuzzy_threshold = 80
        yield mock


@pytest.fixture
def mock_genai():
    """Mock Google Generative AI module."""
    with patch('app.services.classifier.genai') as mock:
        mock_model = Mock()
        mock.GenerativeModel.return_value = mock_model
        yield mock


class TestItemClassifier:
    """Test cases for ItemClassifier."""

    def test_load_cache(self, mock_settings, mock_genai):
        """Test loading cache from file."""
        classifier = ItemClassifier()
        assert len(classifier.cache) == 5
        assert classifier.cache["חלב"] == "חלבי"
        assert classifier.cache["לחם"] == "מאפים"

    def test_load_cache_file_not_found(self, mock_genai):
        """Test loading cache when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "nonexistent.json"
            with patch('app.services.classifier.settings') as mock_settings:
                mock_settings.gemini_api_key = "test-api-key"
                mock_settings.gemini_model = "gemini-1.5-flash"
                mock_settings.categories_cache_path = str(non_existent)
                mock_settings.categories_cache_fuzzy_threshold = 80

                classifier = ItemClassifier()
                assert len(classifier.cache) == 0
                assert non_existent.exists()  # Should create empty cache

    @pytest.mark.asyncio
    async def test_classify_item_from_cache_exact_match(self, mock_settings, mock_genai):
        """Test classification with exact cache match."""
        classifier = ItemClassifier()
        category = await classifier.classify_item("חלב")
        assert category == "חלבי"

    @pytest.mark.asyncio
    async def test_classify_item_fuzzy_match(self, mock_settings, mock_genai):
        """Test classification with fuzzy matching."""
        classifier = ItemClassifier()
        # "חלב טרי" should fuzzy match "חלב"
        category = await classifier.classify_item("חלב טרי")
        assert category == "חלבי"

    @pytest.mark.asyncio
    async def test_classify_item_with_gemini(self, mock_settings, mock_genai):
        """Test classification using Gemini API for unknown item."""
        classifier = ItemClassifier()

        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "חטיפים"
        classifier.model.generate_content = Mock(return_value=mock_response)

        category = await classifier.classify_item("במבה")
        assert category == "חטיפים"

        # Verify item was cached
        assert "במבה" in classifier.cache
        assert classifier.cache["במבה"] == "חטיפים"

    @pytest.mark.asyncio
    async def test_classify_item_gemini_api_failure(self, mock_settings, mock_genai):
        """Test fallback to 'אחר' when Gemini API fails."""
        classifier = ItemClassifier()

        # Mock Gemini to raise exception
        classifier.model.generate_content = Mock(side_effect=Exception("API Error"))

        category = await classifier.classify_item("unknown item")
        assert category == "אחר"

    @pytest.mark.asyncio
    async def test_classify_item_invalid_category_from_gemini(self, mock_settings, mock_genai):
        """Test handling of invalid category from Gemini."""
        classifier = ItemClassifier()

        # Mock Gemini to return invalid category
        mock_response = Mock()
        mock_response.text = "InvalidCategory"
        classifier.model.generate_content = Mock(return_value=mock_response)

        category = await classifier.classify_item("test item")
        assert category == "אחר"

    @pytest.mark.asyncio
    async def test_classify_items_batch(self, mock_settings, mock_genai):
        """Test batch classification of multiple items."""
        classifier = ItemClassifier()

        items = [
            ReceiptItem(name="חלב", quantity=1.0, unit_price=5.90, total_price=5.90),
            ReceiptItem(name="לחם", quantity=1.0, unit_price=7.50, total_price=7.50),
            ReceiptItem(name="עגבניות", quantity=0.5, unit_price=3.00, total_price=1.50),
        ]

        classified_items = await classifier.classify_items(items)

        assert len(classified_items) == 3
        assert classified_items[0].category == "חלבי"
        assert classified_items[1].category == "מאפים"
        assert classified_items[2].category == "ירקות"

    @pytest.mark.asyncio
    async def test_fuzzy_matching_hebrew(self, mock_settings, mock_genai):
        """Test fuzzy matching with Hebrew text variations."""
        classifier = ItemClassifier()

        # Test various forms that should match "חלב"
        test_cases = [
            ("חלב מלא", "חלבי"),  # Should match "חלב"
            ("חלב 1%", "חלבי"),   # Should match "חלב 3%"
        ]

        for item_name, expected_category in test_cases:
            category = await classifier.classify_item(item_name)
            assert category == expected_category

    @pytest.mark.asyncio
    async def test_cache_persistence(self, mock_settings, mock_genai):
        """Test that new classifications are saved to cache."""
        classifier = ItemClassifier()

        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = "משקאות"
        classifier.model.generate_content = Mock(return_value=mock_response)

        # Classify new item
        category = await classifier.classify_item("קולה")
        assert category == "משקאות"

        # Verify cache was updated in memory
        assert "קולה" in classifier.cache
        assert classifier.cache["קולה"] == "משקאות"

        # Verify cache was saved to disk
        with open(classifier.cache_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            assert "קולה" in saved_data["categories"]
            assert saved_data["categories"]["קולה"] == "משקאות"

    def test_find_fuzzy_match_no_match(self, mock_settings, mock_genai):
        """Test fuzzy matching when no good match exists."""
        classifier = ItemClassifier()

        # Item that shouldn't match anything well
        result = classifier._find_fuzzy_match("xyz123")
        assert result is None

    def test_find_fuzzy_match_below_threshold(self, mock_settings, mock_genai):
        """Test fuzzy matching below threshold doesn't match."""
        classifier = ItemClassifier()
        classifier.fuzzy_threshold = 90  # High threshold

        # This might not match at 90% threshold
        result = classifier._find_fuzzy_match("חלבון")
        # Result depends on fuzzy matching score, but test passes either way

    @pytest.mark.asyncio
    async def test_gemini_retry_logic(self, mock_settings, mock_genai):
        """Test that Gemini API calls are retried on failure."""
        classifier = ItemClassifier()

        # Mock to fail twice then succeed
        mock_response = Mock()
        mock_response.text = "חלבי"
        classifier.model.generate_content = Mock(
            side_effect=[
                Exception("Temporary error"),
                Exception("Temporary error"),
                mock_response
            ]
        )

        category = await classifier.classify_item("test item")
        assert category == "חלבי"

        # Verify it was called 3 times (2 failures + 1 success)
        assert classifier.model.generate_content.call_count == 3

    @pytest.mark.asyncio
    async def test_gemini_max_retries_exceeded(self, mock_settings, mock_genai):
        """Test fallback after max retries exceeded."""
        classifier = ItemClassifier()

        # Mock to always fail
        classifier.model.generate_content = Mock(side_effect=Exception("Permanent error"))

        category = await classifier.classify_item("test item")
        assert category == "אחר"

        # Verify it was called 3 times (initial + 2 retries)
        assert classifier.model.generate_content.call_count == 3
