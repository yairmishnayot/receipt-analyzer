"""Item classification service using Google Gemini AI with caching."""

import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from rapidfuzz import fuzz, process

from app.models.receipt import ReceiptItem
from app.config import settings

# Lazy import to avoid protobuf compatibility issues during module import
if TYPE_CHECKING:
    import google.generativeai as genai

logger = logging.getLogger(__name__)


class ItemClassifierError(Exception):
    """Custom exception for item classification errors."""
    pass


class ItemClassifier:
    """
    Service for classifying receipt items into categories.

    Uses a cache-first approach with fuzzy matching to minimize API calls.
    Falls back to Google Gemini API for unknown items.
    """

    # Category classification prompt template
    CLASSIFICATION_PROMPT = """אתה עוזר לסווג פריטי מכולת לקטגוריות.

בהינתן שם פריט מסופרמרקט, החזר את הקטגוריה המתאימה ביותר בעברית.
הקטגוריה צריכה להיות כללית ותמציתית (1-3 מילים).

דוגמאות:
- חלב → חלבי
- לחם → מאפים
- עגבניה → ירקות
- תפוח → פירות
- שוקולד → ממתקים
- סבון → ניקיון
- שמפו → היגיינה

החזר **רק** את שם הקטגוריה בעברית, ללא הסבר או פירוט נוסף.

פריט: {item_name}
קטגוריה:"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the item classifier.

        Args:
            api_key: Google Gemini API key (defaults to settings)
            model: Gemini model name (defaults to settings)
        """
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model or settings.gemini_model
        self.cache_path = Path(settings.categories_cache_path)
        self.fuzzy_threshold = settings.categories_cache_fuzzy_threshold

        # Lazy import and configure Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini model: {str(e)}")
            self.model = None

        # Load cache
        self.cache = self._load_cache()
        logger.info(f"Loaded {len(self.cache)} items from category cache")

    def _load_cache(self) -> dict[str, str]:
        """
        Load category cache from JSON file.

        Returns:
            Dictionary mapping item names to categories
        """
        try:
            if not self.cache_path.exists():
                logger.warning(f"Cache file not found: {self.cache_path}, creating empty cache")
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                self._save_cache_to_disk({"version": "1.0", "categories": {}})
                return {}

            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("categories", {})

        except Exception as e:
            logger.error(f"Failed to load cache: {str(e)}")
            return {}

    def _save_cache(self, item_name: str, category: str):
        """
        Add item to cache and save to disk.

        Args:
            item_name: Name of the item
            category: Category to assign
        """
        try:
            # Add to in-memory cache
            self.cache[item_name] = category

            # Save to disk
            self._save_cache_to_disk({"version": "1.0", "categories": self.cache})
            logger.info(f"Cached classification: '{item_name}' -> '{category}'")

        except Exception as e:
            logger.error(f"Failed to save cache: {str(e)}")
            # Non-fatal - continue without caching

    def _save_cache_to_disk(self, data: dict):
        """
        Atomically save cache to disk using temp file + rename.

        Args:
            data: Full cache data structure to save
        """
        # Write to temp file first
        temp_path = self.cache_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Atomic rename
        temp_path.replace(self.cache_path)

    def _find_fuzzy_match(self, item_name: str) -> Optional[str]:
        """
        Find fuzzy match in cache using similarity scoring.

        Args:
            item_name: Item name to match

        Returns:
            Matched category if found, None otherwise
        """
        if not self.cache:
            return None

        try:
            # Use rapidfuzz to find best match
            result = process.extractOne(
                item_name,
                self.cache.keys(),
                scorer=fuzz.ratio,
                score_cutoff=self.fuzzy_threshold
            )

            if result:
                matched_item, score, _ = result
                category = self.cache[matched_item]
                logger.info(f"Fuzzy match: '{item_name}' -> '{matched_item}' (score: {score:.1f}) -> '{category}'")
                return category

            return None

        except Exception as e:
            logger.error(f"Fuzzy matching failed: {str(e)}")
            return None

    async def _classify_with_gemini(self, item_name: str, retry_count: int = 0) -> str:
        """
        Classify item using Google Gemini API.

        Args:
            item_name: Item name to classify
            retry_count: Current retry attempt number

        Returns:
            Category name

        Raises:
            ItemClassifierError: If classification fails after retries
        """
        max_retries = 2

        # Check if Gemini model is available
        if self.model is None:
            logger.error("Gemini model not initialized, returning fallback category")
            return "אחר"

        try:
            # Format prompt
            prompt = self.CLASSIFICATION_PROMPT.format(item_name=item_name)

            # Call Gemini API in thread pool (SDK is synchronous)
            logger.info(f"Calling Gemini API to classify: '{item_name}'")
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )

            # Extract category from response
            # Handle both simple and complex responses
            try:
                category = response.text.strip()
            except (ValueError, AttributeError):
                # Fallback to extracting from parts if text accessor fails
                if response.candidates and response.candidates[0].content.parts:
                    category = response.candidates[0].content.parts[0].text.strip()
                else:
                    category = "אחר"

            # Basic validation: ensure it's not empty and is reasonably short
            if not category or len(category) > 50:
                logger.warning(f"Gemini returned invalid category '{category}', using 'אחר'")
                category = "אחר"

            logger.info(f"Gemini classified '{item_name}' as '{category}'")
            return category

        except Exception as e:
            logger.error(f"Gemini API error (attempt {retry_count + 1}/{max_retries + 1}): {str(e)}")

            # Retry on transient errors
            if retry_count < max_retries:
                await asyncio.sleep(1)  # Brief delay before retry
                return await self._classify_with_gemini(item_name, retry_count + 1)

            # After all retries failed, return fallback
            logger.error(f"Failed to classify '{item_name}' after {max_retries + 1} attempts, using 'אחר'")
            return "אחר"

    async def classify_item(self, item_name: str) -> str:
        """
        Classify a single item into a category.

        Uses cache-first approach with fuzzy matching, falls back to Gemini API.

        Args:
            item_name: Name of the item to classify

        Returns:
            Category name
        """
        try:
            # Step 1: Check exact match in cache
            if item_name in self.cache:
                category = self.cache[item_name]
                logger.debug(f"Cache hit (exact): '{item_name}' -> '{category}'")
                return category

            # Step 2: Try fuzzy matching
            fuzzy_category = self._find_fuzzy_match(item_name)
            if fuzzy_category:
                # Cache this exact name for future lookups
                self._save_cache(item_name, fuzzy_category)
                return fuzzy_category

            # Step 3: Call Gemini API for new item
            category = await self._classify_with_gemini(item_name)

            # Step 4: Cache the result (including "אחר")
            self._save_cache(item_name, category)

            return category

        except Exception as e:
            logger.error(f"Classification failed for '{item_name}': {str(e)}")
            # Return fallback category on any error
            return "אחר"

    async def classify_items(self, items: list[ReceiptItem]) -> list[ReceiptItem]:
        """
        Classify all items in a receipt.

        Args:
            items: List of receipt items to classify

        Returns:
            List of items with updated category field
        """
        logger.info(f"Classifying {len(items)} items")

        # Classify all items concurrently
        tasks = [self.classify_item(item.name) for item in items]
        categories = await asyncio.gather(*tasks)

        # Update item categories
        for item, category in zip(items, categories):
            item.category = category

        logger.info(f"Successfully classified {len(items)} items")
        return items

    def get_all_categories(self) -> dict[str, str]:
        """
        Get all cached item classifications.

        Returns:
            Dictionary mapping item names to categories
        """
        return self.cache.copy()

    def update_category(self, item_name: str, new_category: str) -> bool:
        """
        Update the category for a specific item in the cache.

        Args:
            item_name: Name of the item to update
            new_category: New category to assign

        Returns:
            True if successful, False otherwise
        """
        try:
            if item_name not in self.cache:
                logger.warning(f"Item '{item_name}' not found in cache")
                return False

            old_category = self.cache[item_name]
            self._save_cache(item_name, new_category)
            logger.info(f"Updated classification: '{item_name}' from '{old_category}' to '{new_category}'")
            return True

        except Exception as e:
            logger.error(f"Failed to update category for '{item_name}': {str(e)}")
            return False

    def rename_category(self, old_category: str, new_category: str) -> dict:
        """
        Rename a category across all items in cache.

        Args:
            old_category: Current category name to rename
            new_category: New category name

        Returns:
            Dictionary with:
                - success: bool
                - items_updated: int (count of items updated)
                - old_category: str
                - new_category: str
        """
        try:
            # Validate inputs
            if not old_category or not old_category.strip():
                logger.error("Old category name cannot be empty")
                return {
                    "success": False,
                    "items_updated": 0,
                    "old_category": old_category,
                    "new_category": new_category
                }

            if not new_category or not new_category.strip():
                logger.error("New category name cannot be empty")
                return {
                    "success": False,
                    "items_updated": 0,
                    "old_category": old_category,
                    "new_category": new_category
                }

            if old_category == new_category:
                logger.info("Old and new category names are identical, no update needed")
                return {
                    "success": True,
                    "items_updated": 0,
                    "old_category": old_category,
                    "new_category": new_category
                }

            # Find all items with the old category
            items_to_update = [
                item_name for item_name, category in self.cache.items()
                if category == old_category
            ]

            # Update each item to the new category
            for item_name in items_to_update:
                self.cache[item_name] = new_category

            # Save cache atomically
            if items_to_update:
                self._save_cache_to_disk({"version": "1.0", "categories": self.cache})
                logger.info(f"Renamed category '{old_category}' to '{new_category}' for {len(items_to_update)} items")

            return {
                "success": True,
                "items_updated": len(items_to_update),
                "old_category": old_category,
                "new_category": new_category
            }

        except Exception as e:
            logger.error(f"Failed to rename category '{old_category}' to '{new_category}': {str(e)}")
            return {
                "success": False,
                "items_updated": 0,
                "old_category": old_category,
                "new_category": new_category
            }
