---
name: codebase-structure
description: This skill provides a comprehensive overview of the Receipt Analyzer project structure, file organization, and architectural layout.
license: MIT
compatibility: opencode
---

# Skill: codebase-structure

This skill provides a comprehensive overview of the Receipt Analyzer project structure, file organization, and architectural layout.

## Project Type

**Monorepo Architecture** - Full-stack web application with separate backend and frontend directories.

## Root Directory Structure

```
receipt-analyzer/
├── backend/              # Python FastAPI backend
├── frontend/             # React + Vite frontend
├── node_modules/         # Root-level Node dependencies (for dev tools)
├── .claude/              # Project-specific Claude Code configuration
├── .git/                 # Git repository
├── .gitignore            # Git ignore rules
├── CLAUDE.md             # Project guidelines and instructions for Claude
├── README.md             # Project documentation
├── package.json          # Root-level package.json (scripts, devDependencies)
└── package-lock.json     # Lock file for root dependencies
```

## Backend Structure (Python/FastAPI)

### Technology Stack
- **Python 3.11+** with **FastAPI** framework
- **Playwright** for browser automation/scraping
- **BeautifulSoup4** for HTML parsing
- **Google Sheets API v4** for spreadsheet integration
- **Poetry** for dependency management
- **pytest** for testing

### Directory Layout

```
backend/
├── app/
│   ├── __init__.py                    # App package initialization
│   ├── config.py                      # Environment configuration and settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── receipt.py             # Receipt processing endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── receipt.py                 # Pydantic data models (Receipt, ReceiptItem)
│   └── services/
│       ├── __init__.py
│       ├── scraper.py                 # ReceiptScraper class (Playwright-based)
│       ├── parser.py                  # ReceiptParser class (BeautifulSoup parsing)
│       └── sheets.py                  # SheetsService class (Google Sheets integration)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # pytest fixtures and configuration
│   ├── test_api.py                    # API endpoint tests
│   └── test_parser.py                 # Parser unit tests
├── main.py                            # FastAPI application entry point
├── test_scrape.py                     # Standalone scraping test script
├── pyproject.toml                     # Poetry dependencies and project config
├── poetry.lock                        # Poetry lock file
├── .env                               # Environment variables (not committed)
├── .env.example                       # Example environment variables template
└── credentials.json                   # Google service account credentials (not committed)
```

### Key Backend Files

| File | Purpose |
|------|---------|
| main.py | FastAPI application initialization, CORS setup, and route mounting |
| app/config.py | Settings class using Pydantic BaseSettings, loads from .env |
| app/api/routes/receipt.py | POST endpoint `/api/receipt/process` for receipt processing |
| app/models/receipt.py | Data models: `ReceiptItem`, `Receipt`, `ProcessReceiptRequest`, `ProcessReceiptResponse` |
| app/services/scraper.py | `ReceiptScraper` class - uses Playwright to load receipt URLs and extract HTML |
| app/services/parser.py | `ReceiptParser` class - parses HTML with BeautifulSoup to extract structured data |
| app/services/sheets.py | `SheetsService` class - interfaces with Google Sheets API to write receipt data |

### Backend Environment Variables (.env)

```bash
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
GOOGLE_SHEETS_ID=your-spreadsheet-id
SCRAPING_TIMEOUT=30000
ENVIRONMENT=development
```

## Frontend Structure (React/Vite)

### Technology Stack
- **React 18** for UI components
- **Vite** for build tooling and dev server
- **react-i18next** for internationalization (Hebrew primary, English secondary)
- **Axios** for HTTP requests
- **Vitest** for testing

### Directory Layout

```
frontend/
├── src/
│   ├── main.jsx                       # React app entry point
│   ├── App.jsx                        # Root component
│   ├── components/
│   │   ├── ReceiptForm.jsx            # Main form component for URL input
│   │   ├── LoadingSpinner.jsx         # Loading state UI component
│   │   └── ErrorDisplay.jsx           # Error message display component
│   ├── services/
│   │   └── api.js                     # Axios-based API client for backend
│   ├── i18n/
│   │   ├── config.js                  # i18next configuration
│   │   ├── he.json                    # Hebrew translations (primary)
│   │   └── en.json                    # English translations (secondary)
│   ├── styles/
│   │   ├── global.css                 # Global styles and RTL support
│   │   ├── ReceiptForm.css            # Form component styles
│   │   ├── LoadingSpinner.css         # Spinner animation styles
│   │   └── ErrorDisplay.css           # Error display styles
│   └── test/
│       └── setup.js                   # Vitest test setup
├── tests/                             # Additional test files (if any)
├── node_modules/                      # Frontend dependencies
├── package.json                       # Frontend dependencies and scripts
├── package-lock.json                  # Lock file
└── vite.config.js                     # Vite configuration (if exists)
```

### Key Frontend Files

| File | Purpose |
|------|---------|
| src/main.jsx | React app initialization, i18n setup, renders root component |
| src/App.jsx | Root component, contains ReceiptForm and handles language switching |
| src/components/ReceiptForm.jsx | Main UI component for receipt URL submission |
| src/services/api.js | Axios instance configured to call backend API at `/api/receipt/process` |
| src/i18n/config.js | i18next initialization with Hebrew as default language |
| src/i18n/he.json | Hebrew UI text translations |
| src/i18n/en.json | English UI text translations |

## Data Flow Architecture

```
User (Browser)
    ↓
Frontend (React) - ReceiptForm.jsx
    ↓ (HTTP POST)
Backend API - /api/receipt/process
    ↓
ReceiptScraper (Playwright)
    ↓ (loads URL, extracts HTML)
ReceiptParser (BeautifulSoup)
    ↓ (parses HTML → structured data)
SheetsService (Google Sheets API)
    ↓ (writes to 2 sheets)
Google Sheets
    ↓
Response → Frontend → User
```

## File Naming Conventions

### Backend (Python)
- **Snake case** for file names: `receipt_parser.py`, `test_api.py`
- **PascalCase** for class names: `ReceiptScraper`, `SheetsService`
- **Snake case** for functions/variables: `parse_receipt()`, `total_amount`

### Frontend (JavaScript/React)
- **PascalCase** for component files: `ReceiptForm.jsx`, `ErrorDisplay.jsx`
- **camelCase** for utility files: `api.js`, `config.js`
- **kebab-case** for CSS files: `loading-spinner.css`, `receipt-form.css`
- **Lowercase** for translation files: `he.json`, `en.json`

## Testing Structure

### Backend Tests (`backend/tests/`)
- **conftest.py** - pytest fixtures (mock scraper, parser, sheets service)
- **test_api.py** - API endpoint integration tests
- **test_parser.py** - Parser unit tests with sample HTML fixtures

### Frontend Tests
- **src/test/setup.js** - Vitest configuration
- Component tests (to be created) would go in `tests/` or co-located with components

## Configuration Files

### Backend
| File | Purpose |
|------|---------|
| pyproject.toml | Poetry dependencies, Python version, project metadata |
| poetry.lock | Locked dependency versions |
| .env | Environment-specific configuration (gitignored) |
| .env.example | Template for environment variables |
| credentials.json | Google service account credentials (gitignored) |

### Frontend
| File | Purpose |
|------|---------|
| package.json | npm dependencies, build scripts |
| package-lock.json | Locked npm dependency tree |
| vite.config.js | Vite bundler configuration (if exists) |

### Root
| File | Purpose |
|------|---------|
| package.json | Monorepo scripts (e.g., `npm run dev` to start both frontend and backend) |
| CLAUDE.md | Comprehensive project guidelines for AI assistance |
| README.md | User-facing project documentation |
| .gitignore | Excludes: `node_modules/`, `.env`, `credentials.json`, `__pycache__/`, etc. |

## Google Sheets Integration

The application writes to two sheets in a single Google Spreadsheet:

**Sheet 1: "Receipt Summary"**
- Columns: Date | Store Name | Total Amount | Transaction ID | Receipt URL
- One row per receipt
- Rows inserted in date-sorted order

**Sheet 2: "Receipt Items"**
- Columns: Receipt Date | Store Name | Item Name | Quantity | Unit Price | Total Price | Discount | Transaction ID | Receipt URL
- One row per item (multiple rows per receipt)
- Linked to summary via Transaction ID

## Development Commands

### Backend
```bash
cd backend
poetry install                    # Install dependencies
poetry run playwright install     # Install browser binaries
poetry run uvicorn main:app --reload   # Start dev server (port 8000)
poetry run pytest                 # Run tests
poetry run pytest --cov=app       # Run tests with coverage
```

### Frontend
```bash
cd frontend
npm install                       # Install dependencies
npm run dev                       # Start dev server (port 5173)
npm test                          # Run tests
npm run build                     # Build for production
```

### Both (from root)
```bash
npm run dev                       # Start both servers concurrently
```

## Key Dependencies

### Backend (Python)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `playwright` - Browser automation
- `beautifulsoup4` - HTML parsing
- `google-auth` + `google-api-python-client` - Google Sheets integration
- `pydantic` - Data validation
- `python-dotenv` - Environment variable loading
- `pytest` + `pytest-asyncio` - Testing

### Frontend (JavaScript)
- `react` + `react-dom` - UI framework
- `vite` - Build tool
- `axios` - HTTP client
- `react-i18next` + `i18next` - Internationalization
- `vitest` - Testing framework

## Receipt Format Support

**Currently Supported:**
- Osher/Pairzon receipt format only
- Example URL: `https://osher.pairzon.com/dba51f17-81ac-41f8-b76d-64e62fb13df4.html?id=74588a50-4de7-4bd9-b41d-e551452b5b1c&p=1247`

**Implementation Details:**
- Receipt content is JavaScript-rendered (requires browser automation)
- Parser in `app/services/parser.py` is specific to this format
- Uses specific HTML selectors for data extraction

## Language and Localization

- **Primary Language:** Hebrew (עברית)
- **Secondary Language:** English
- **RTL Support:** CSS uses logical properties for RTL layout
- **Error Messages:** Hebrew by default
- **Translation Files:** `frontend/src/i18n/he.json` and `en.json`

## When to Modify Each Component

| Scenario | Edit this file |
|----------|----------------|
| Scraping logic changes | `backend/app/services/scraper.py` |
| Receipt HTML format changes | `backend/app/services/parser.py` |
| Google Sheets structure changes | `backend/app/services/sheets.py` |
| API contract changes | `backend/app/models/receipt.py` (Pydantic models) + `backend/app/api/routes/receipt.py` (endpoints) + `frontend/src/services/api.js` (API client) |
| UI changes | `frontend/src/components/*.jsx` + `frontend/src/styles/*.css` |
| Add translations | `frontend/src/i18n/he.json` and `en.json` |

## Quick File Reference

| Need to... | Edit this file |
|-----------|----------------|
| Change API endpoint logic | `backend/app/api/routes/receipt.py` |
| Modify scraping behavior | `backend/app/services/scraper.py` |
| Update HTML parsing | `backend/app/services/parser.py` |
| Change Sheets integration | `backend/app/services/sheets.py` |
| Add/modify data models | `backend/app/models/receipt.py` |
| Update environment config | `backend/.env` and `backend/app/config.py` |
| Change UI components | `frontend/src/components/*.jsx` |
| Update API client | `frontend/src/services/api.js` |
| Add translations | `frontend/src/i18n/he.json`, `en.json` |
| Modify styles | `frontend/src/styles/*.css` |
| Update tests | `backend/tests/*` or `frontend/tests/*` |

## Architecture Patterns

### Backend Patterns
- **Service Layer Architecture** - Business logic separated into service classes
- **Dependency Injection** - Services instantiated and passed to routes
- **Async/Await** - All I/O operations are async
- **Pydantic Models** - Request/response validation and serialization

### Frontend Patterns
- **Component-Based Architecture** - Reusable React functional components
- **Centralized API Client** - Single Axios instance in `services/api.js`
- **Internationalization** - All text externalized to translation files
- **CSS Modules** - Component-specific stylesheets

## Security Notes

- **Never commit:** `.env`, `credentials.json`, `node_modules/`, `__pycache__/`
- **Google Sheets Access:** Requires service account with Editor permissions
- **CORS:** Backend configured to allow frontend origin (localhost:5173 in dev)

## MVP Scope

**Currently Implemented:**
- Single receipt URL processing
- Osher/Pairzon format only
- Google Sheets integration (2 sheets)
- Hebrew/English UI

**Not Yet Implemented (Future):**
- Support for other receipt formats
- Receipt history/management
- Duplicate detection
- Search/filtering
- Batch processing
