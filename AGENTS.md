# AGENTS.md - Receipt Analyzer Development Guide

This file provides guidance for agentic coding agents working in this repository.

## Project Overview

Receipt Analyzer is a web application that:
- Scrapes receipts from Osher/Pairzon using Playwright
- Extracts structured data (date, items, prices) using BeautifulSoup
- Categorizes items using Google Gemini AI
- Updates Google Sheets with two sheets (summary + detailed items)

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Playwright, BeautifulSoup4, Pydantic
- **Frontend**: React 18, Vite, react-i18next, Axios
- **Testing**: pytest (backend), Vitest (frontend)

---

## Commands

### Running the Application

```bash
# Backend only (http://localhost:8000)
cd backend && poetry run uvicorn main:app --reload

# Frontend only (http://localhost:5173)
cd frontend && npm run dev

# Both concurrently (requires concurrently at root)
npm run dev
```

### Testing

```bash
# Backend - all tests
cd backend && poetry run pytest

# Backend - single test file
cd backend && poetry run pytest tests/test_parser.py

# Backend - single test function
cd backend && poetry run pytest tests/test_parser.py::test_parser_extracts_store_name

# Backend - with coverage
cd backend && poetry run pytest --cov=app

# Frontend - all tests
cd frontend && npm test

# Frontend - single test file (watch mode)
cd frontend && npm test src/components/ReceiptForm.jsx

# Frontend - single test (run once, not watch)
cd frontend && npm test src/components/ReceiptForm.jsx -- --run
```

### Linting & Type Checking

```bash
# Backend - format with Black
cd backend && poetry run black app/

# Backend - type checking with MyPy
cd backend && poetry run mypy app/

# Backend - lint with Flake8
cd backend && poetry run flake8 app/

# Frontend - build for production
cd frontend && npm run build

# Frontend - preview production build
cd frontend && npm run preview
```

---

## Code Style Guidelines

### Python (Backend)

**Formatting**
- Line length: 100 characters (Black default)
- Use Black for formatting: `poetry run black app/`
- Target Python 3.11+

**Imports**
- Order: stdlib → third-party → local
- Group by type: async imports, type hints, exceptions
- Example:
  ```python
  import asyncio
  from typing import Optional
  
  from fastapi import APIRouter, HTTPException
  from playwright.async_api import async_playwright
  
  from app.models.receipt import ReceiptRequest
  from app.services.parser import parse_receipt_html
  ```

**Type Hints**
- Always use type hints for function parameters and return types
- Use `Optional[X]` instead of `X | None` for compatibility
- Example:
  ```python
  async def scrape_receipt(self, url: str) -> str:
      items: list[ReceiptItem] = []
      config: Optional[dict] = None
  ```

**Naming Conventions**
- Classes: `PascalCase` (e.g., `ReceiptScraper`)
- Functions/methods: `snake_case` (e.g., `parse_receipt_html`)
- Constants: `UPPER_SNAKE_CASE`
- Private methods: prefix with `_` (e.g., `_extract_items`)
- Custom exceptions: suffix with `Error` (e.g., `ReceiptScraperError`)

**Docstrings**
- Use Google-style docstrings for all public functions/classes
- Include Args, Returns, Raises sections
- Example:
  ```python
  def scrape_receipt(self, url: str) -> str:
      """
      Scrape a receipt URL and return fully rendered HTML.

      Args:
          url: Receipt URL to scrape

      Returns:
          Fully rendered HTML content as string

      Raises:
          ReceiptScraperError: If scraping fails
      """
  ```

**Error Handling**
- Create custom exceptions for each service (suffix with `Error`)
- Use Hebrew error messages for user-facing errors
- Log errors with `logger.exception()` for stack traces
- Example:
  ```python
  class ReceiptScraperError(Exception):
      pass
  
  try:
      await page.goto(url)
  except PlaywrightTimeout as e:
      logger.error(f"Timeout loading receipt: {url}")
      raise ReceiptScraperError(f"Timeout while loading receipt") from e
  ```

**Pydantic Models**
- Use Pydantic v2 for data validation
- Define models in `app/models/`
- Example:
  ```python
  from pydantic import BaseModel, Field
  
  class ReceiptItem(BaseModel):
      name: str
      quantity: float = Field(default=1.0)
      price: float
      category: Optional[str] = None
  ```

---

### JavaScript/React (Frontend)

**General**
- Use functional components with hooks
- Use `const` for all variables (avoid `let` unless reassignment needed)
- Handle loading and error states explicitly

**Component Structure**
```jsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import LoadingSpinner from './LoadingSpinner';
import '../styles/Component.css';

const ComponentName = () => {
  const { t } = useTranslation();
  const [state, setState] = useState(null);

  // Event handlers
  const handleAction = async () => {
    // implementation
  };

  return (
    <div className="container">
      {/* JSX */}
    </div>
  );
};

export default ComponentName;
```

**Imports**
- React hooks first
- Third-party libraries
- Local components
- CSS/styles
- Order each group alphabetically

**i18n (Internationalization)**
- Hebrew is the primary language (RTL support required)
- Use `useTranslation` hook
- All user-facing text must use translation keys
- Keys go in `src/i18n/he.json` and `src/i18n/en.json`

**CSS**
- Use CSS custom properties for theming
- Use logical properties for RTL support:
  - `margin-inline-start` instead of `margin-left`
  - `padding-inline-end` instead of `padding-right`
  - `text-align: start` instead of `text-align: left`
- Keep styles minimal and clean

---

## Project Structure

```
receipt-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Pydantic models
│   │   └── config.py        # Settings
│   ├── tests/               # pytest tests
│   ├── data/                # Category cache, etc.
│   ├── pyproject.toml       # Poetry config
│   └── main.py              # FastAPI app entry
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/       # API clients
│   │   ├── i18n/           # Translation files
│   │   └── styles/         # CSS files
│   └── package.json
└── package.json            # Root scripts
```

---

## Key Design Patterns

### Backend Services
- Each service is a class with focused responsibility
- Use context managers for resource cleanup
- Services: `ReceiptScraper`, `ReceiptParser`, `ItemClassifier`, `SheetsService`

### Error Recovery
- Classification failures are non-blocking (continue without categories)
- Scraping/parsing failures raise specific exceptions
- All errors logged with appropriate level

### Google Sheets
- Two sheets: "Receipt Summary" and "Receipt Items"
- Rows inserted at date-sorted positions
- Duplicate detection by transaction_id

---

## Environment Variables

Create `.env` files (never commit these):

**Backend** (`backend/.env`):
```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
GOOGLE_SHEETS_ID=your-spreadsheet-id
GEMINI_API_KEY=your-api-key
SCRAPING_TIMEOUT=30000
```

**Frontend** (`frontend/.env`):
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## Common Issues & Solutions

1. **Playwright not installed**: Run `poetry run playwright install chromium`
2. **Missing credentials**: Ensure `credentials.json` exists in backend/
3. **Sheets permission error**: Share spreadsheet with service account email
4. **RTL issues**: Use logical CSS properties, test with `dir="rtl"`

---

## Testing Guidelines

- Backend tests go in `backend/tests/`
- Frontend tests colocated with components or in `__tests__/` folders
- Use fixtures in `conftest.py` for pytest
- Mock external services (Google Sheets, Gemini API)
