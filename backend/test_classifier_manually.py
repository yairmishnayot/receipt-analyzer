#!/usr/bin/env python3
"""Quick test to verify the classifier works with Gemini API."""

import asyncio
import sys
sys.path.insert(0, '/Users/yair/projects/receipt-analyzer/backend')

from app.services.classifier import ItemClassifier
from app.models.receipt import ReceiptItem


async def test_classifier():
    print("🧪 Testing Item Classifier with Gemini API\n")
    print("=" * 60)

    # Initialize classifier
    print("1. Initializing classifier...")
    classifier = ItemClassifier()

    if classifier.model is None:
        print("❌ ERROR: Gemini model failed to initialize!")
        print("   Check your GEMINI_API_KEY in .env")
        return False

    print("✅ Gemini model initialized successfully\n")

    # Test items (starting with empty cache)
    test_items = [
        "חלב טרי",
        "לחם שחור",
        "עגבניות שרי",
        "שניצל עוף",
        "קולה זירו",
    ]

    print("2. Testing classification (cache is empty):\n")

    for item_name in test_items:
        print(f"   Classifying: '{item_name}'...")
        category = await classifier.classify_item(item_name)
        print(f"   → Category: '{category}'")

        if category == "אחר" and item_name in ["חלב טרי", "לחם שחור"]:
            print(f"   ⚠️  Warning: Got 'אחר' for a common item")

        print()

    print("=" * 60)
    print("\n3. Cache status:")
    print(f"   Items in cache: {len(classifier.cache)}")

    if len(classifier.cache) > 0:
        print("\n✅ SUCCESS! Gemini API is working and items are being classified!")
        print("\nYou can now process receipts and items will be automatically")
        print("categorized. The cache will grow with each receipt.")
    else:
        print("\n❌ FAILED: No items were added to cache")
        print("   The API might not be responding correctly")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_classifier())
    sys.exit(0 if success else 1)
