"""API routes for category management."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import logging

from app.services.classifier import ItemClassifier
from app.services.sheets import SheetsService, SheetsServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryItem(BaseModel):
    """Model for a cached category item."""
    item_name: str = Field(..., description="Name of the item")
    category: str = Field(..., description="Assigned category")


class CategoryUpdate(BaseModel):
    """Model for updating a category."""
    item_name: str = Field(..., description="Name of the item to update")
    new_category: str = Field(..., description="New category to assign")


class CategoriesResponse(BaseModel):
    """Response model for getting all categories."""
    success: bool = Field(..., description="Whether the operation was successful")
    count: int = Field(..., description="Number of cached items")
    items: list[CategoryItem] = Field(..., description="List of cached items with categories")


class CategoryUpdateResponse(BaseModel):
    """Response model for updating a category."""
    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Result message in Hebrew")
    item: CategoryItem = Field(None, description="Updated item")
    sheets_updated: int = Field(default=0, description="Number of rows updated in Google Sheets")


class CategoryRename(BaseModel):
    """Model for renaming a category."""
    old_name: str = Field(..., min_length=1, description="Current category name")
    new_name: str = Field(..., min_length=1, description="New category name")


class CategoryRenameResponse(BaseModel):
    """Response model for renaming a category."""
    success: bool = Field(..., description="Whether the rename was successful")
    message: str = Field(..., description="Result message in Hebrew")
    cache_items_updated: int = Field(..., description="Number of items updated in cache")
    sheets_rows_updated: int = Field(..., description="Number of rows updated in Google Sheets")
    old_name: str = Field(..., description="Original category name")
    new_name: str = Field(..., description="New category name")


@router.get("/", response_model=CategoriesResponse)
async def get_all_categories():
    """
    Get all cached item classifications.

    Returns:
        CategoriesResponse with all cached items and their categories
    """
    try:
        classifier = ItemClassifier()
        cache = classifier.get_all_categories()

        items = [
            CategoryItem(item_name=name, category=cat)
            for name, cat in cache.items()
        ]

        # Sort by category, then by item name
        items.sort(key=lambda x: (x.category, x.item_name))

        return CategoriesResponse(
            success=True,
            count=len(items),
            items=items
        )

    except Exception as e:
        logger.exception(f"Failed to get categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בטעינת הקטגוריות: {str(e)}"
        )


@router.put("/", response_model=CategoryUpdateResponse)
async def update_category(update: CategoryUpdate):
    """
    Update the category for a specific item.

    This will:
    1. Update the category in the cache
    2. Update ALL occurrences of this item in Google Sheets

    Args:
        update: CategoryUpdate with item name and new category

    Returns:
        CategoryUpdateResponse with success status, updated item, and number of sheets rows updated
    """
    try:
        # Update cache
        classifier = ItemClassifier()
        cache_success = classifier.update_category(update.item_name, update.new_category)

        if not cache_success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"פריט '{update.item_name}' לא נמצא במטמון"
            )

        # Update Google Sheets (find all occurrences and update)
        sheets_updated = 0
        try:
            sheets_service = SheetsService()
            sheets_updated = sheets_service.update_item_category_in_sheets(
                update.item_name,
                update.new_category
            )
            logger.info(f"Updated {sheets_updated} rows in Google Sheets for item '{update.item_name}'")
        except SheetsServiceError as e:
            logger.error(f"Failed to update sheets (cache was updated): {str(e)}")
            # Don't fail the whole request if sheets update fails
            # Cache is updated, which is the primary goal

        return CategoryUpdateResponse(
            success=True,
            message=f"הקטגוריה עודכנה בהצלחה במטמון ו-{sheets_updated} שורות בגיליון",
            item=CategoryItem(
                item_name=update.item_name,
                category=update.new_category
            ),
            sheets_updated=sheets_updated
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Failed to update category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בעדכון הקטגוריה: {str(e)}"
        )


@router.put("/rename", response_model=CategoryRenameResponse)
async def rename_category(rename: CategoryRename):
    """
    Rename a category globally across cache and Google Sheets.

    This will:
    1. Rename the category for all items in the cache
    2. Update ALL occurrences of this category in Google Sheets (Items sheet)

    Args:
        rename: CategoryRename with old and new category names

    Returns:
        CategoryRenameResponse with counts of updated items and rows
    """
    try:
        # Validate inputs
        if not rename.old_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="שם הקטגוריה הישנה לא יכול להיות ריק"
            )

        if not rename.new_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="שם הקטגוריה החדשה לא יכול להיות ריק"
            )

        if rename.old_name == rename.new_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="הקטגוריה החדשה זהה לקיימת"
            )

        # Update cache
        classifier = ItemClassifier()
        cache_result = classifier.rename_category(rename.old_name, rename.new_name)

        if not cache_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="שגיאה בעדכון המטמון"
            )

        cache_items_updated = cache_result["items_updated"]

        # Update Google Sheets (non-blocking - log errors but don't fail)
        sheets_rows_updated = 0
        try:
            sheets_service = SheetsService()
            sheets_rows_updated = sheets_service.rename_category_in_sheets(
                rename.old_name,
                rename.new_name
            )
            logger.info(f"Updated {sheets_rows_updated} rows in Google Sheets for category rename")
        except SheetsServiceError as e:
            logger.error(f"Failed to update sheets (cache was updated): {str(e)}")
            # Don't fail the whole request if sheets update fails
            # Cache is updated, which is the primary goal

        return CategoryRenameResponse(
            success=True,
            message=f"הקטגוריה '{rename.old_name}' שונתה ל-'{rename.new_name}' - {cache_items_updated} פריטים במטמון, {sheets_rows_updated} שורות בגיליון",
            cache_items_updated=cache_items_updated,
            sheets_rows_updated=sheets_rows_updated,
            old_name=rename.old_name,
            new_name=rename.new_name
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Failed to rename category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"שגיאה בשינוי שם הקטגוריה: {str(e)}"
        )
