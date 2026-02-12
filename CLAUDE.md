# Receipt Analyzer - Project Guidelines

## Project Overview

This is a web application that automates receipt data extraction and Google Sheets integration. Users paste a receipt URL (specifically from Osher/Pairzon), and the system scrapes the receipt, extracts structured data (date, items, prices), and updates a Google Sheets document with two sheets: a summary sheet and a detailed items sheet.

## Technology Stack

### Backend
- **Python 3.11+** with **FastAPI** - Modern async web framework
- **Playwright** - Headless browser for scraping JavaScript-rendered receipts
- **BeautifulSoup4** - HTML parsing
- **Pydantic** - Data validation and serialization
- **Google Sheets API v4** - Spreadsheet integration
- **Google Gemini Flash** - AI-powered item categorization
- **RapidFuzz** - Fuzzy string matching for cache optimization
- **Poetry** - Dependency management
- **pytest** - Testing framework

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **react-i18next** - Internationalization (Hebrew primary, English secondary)
- **Axios** - HTTP client
- **Vitest** - Testing framework

## Architecture

### Monorepo Structure
```
receipt-analyzer/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Pydantic models
│   │   └── config.py       # Configuration
│   ├── tests/              # Backend tests
│   └── pyproject.toml      # Python dependencies
└── frontend/         # React + Vite frontend
    ├── src/
    │   ├── components/     # React components
    │   ├── services/       # API clients
    │   ├── i18n/          # Translations
    │   └── styles/        # CSS styles
    └── package.json        # Node dependencies
```

## Key Design Decisions

### Why Playwright?
The Osher/Pairzon receipt format uses JavaScript event dispatching to dynamically populate content. Simple HTML scraping won't capture this data. Playwright allows us to:
- Load the page in a real browser environment
- Wait for JavaScript to execute and populate content
- Capture the fully rendered HTML

### Hebrew as Primary Language
- UI defaults to Hebrew with RTL (right-to-left) layout
- English available as secondary language
- All user-facing text internationalized via `react-i18next`
- Error messages in Hebrew by default

### Two-Sheet Google Sheets Structure
**Sheet 1: "Receipt Summary"**
- One row per receipt
- Columns: Date (dd-mm-YYYY) | Month (Hebrew name, e.g., "ינואר") | Total Amount | Transaction ID | Last Updated | Receipt URL
- Sorted by date

**Sheet 2: "Receipt Items"**
- One row per item (multiple rows per receipt)
- Columns: Receipt Date (dd-mm-YYYY) | Month (Hebrew name, e.g., "ינואר") | Transaction ID | Item Name | **Category** | Quantity | Unit Price | Total Price | Discount | Receipt URL
- Linked to summary via Transaction ID
- Items are automatically categorized using AI

**Insert Logic**: Rows are inserted at date-sorted positions to maintain chronological order.

### Item Categorization System
The application includes an intelligent categorization system that automatically classifies receipt items:

**Why This Approach:**
- **Cache-First Strategy**: Minimizes API calls by checking local cache first (stored in `data/categories.json`)
- **Fuzzy Matching**: Uses RapidFuzz to handle item name variations (e.g., "חלב 3%" matches "חלב")
- **Google Gemini Flash**: Uses free-tier AI (1,500 requests/day) for unknown items
- **Auto-Learning**: New classifications are automatically cached for future receipts
- **Non-Blocking**: Classification failures don't break the receipt processing flow

**Categories:**
- חלבי (Dairy), מאפים (Bakery), ירקות (Vegetables), פירות (Fruits)
- בשר ועוף (Meat & Poultry), דגים (Fish), קפואים (Frozen)
- משקאות (Beverages), חטיפים (Snacks)
- ניקיון (Cleaning), היגיינה (Personal Care), אחר (Other)

**Cache File**: `backend/data/categories.json` contains pre-populated common items and grows automatically as new items are classified.

### MVP Scope
- **Currently supports**: Osher/Pairzon receipt format only
- **Future expansion**: Extensible to other receipt formats (not implemented yet)
- Parser is specific to the current format - don't over-engineer for future formats

## File Organization Conventions

### Backend
- **`app/services/`**: Business logic classes (ReceiptScraper, ReceiptParser, ItemClassifier, SheetsService)
- **`app/models/`**: Pydantic models for data validation
- **`app/api/routes/`**: FastAPI route handlers
- **`app/config.py`**: Environment configuration
- **`data/`**: Category cache and data files
- **`tests/`**: Unit and integration tests

### Frontend
- **`components/`**: Reusable React components (ReceiptForm, LoadingSpinner, ErrorDisplay)
- **`services/`**: Backend API client
- **`i18n/`**: Translation files (he.json, en.json)
- **`styles/`**: Global CSS with RTL support

## Development Workflow

### Initial Setup

**Backend:**
```bash
cd backend
poetry install
poetry run playwright install chromium
```

**Frontend:**
```bash
cd frontend
npm install
```

### Running the Application

**Backend (FastAPI):**
```bash
cd backend
poetry run uvicorn main:app --reload
# Runs on http://localhost:8000
```

**Frontend (Vite):**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
# Proxies API requests to backend
```

**Both (from root):**
```bash
npm run dev
# Requires concurrently package at root level
```

### Testing

**Backend:**
```bash
cd backend
poetry run pytest
poetry run pytest --cov=app  # With coverage
```

**Frontend:**
```bash
cd frontend
npm test
```

## Environment Variables

### Backend `.env`
Required environment variables:
```bash
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json  # Path to service account JSON
GOOGLE_SHEETS_ID=your-spreadsheet-id               # Target Google Sheet ID

# Google Gemini AI Configuration
GEMINI_API_KEY=your-api-key-here                   # Google AI Studio API key
GEMINI_MODEL=gemini-1.5-flash                      # Gemini model (optional, defaults to flash)

# Item Categorization (optional - has defaults)
CATEGORIES_CACHE_PATH=./data/categories.json       # Path to category cache file
CATEGORIES_CACHE_FUZZY_THRESHOLD=80                # Fuzzy match threshold (0-100)

# Scraping Configuration
SCRAPING_TIMEOUT=30000                             # Playwright timeout in ms

# Application Configuration
ENVIRONMENT=development                             # Environment name
```

### Frontend `.env`
```bash
VITE_API_BASE_URL=http://localhost:8000  # Backend API URL
```

## Google Sheets Setup

### Prerequisites
1. **Create Google Cloud Project**: https://console.cloud.google.com/
2. **Enable Google Sheets API**: In API Library, search for "Google Sheets API" and enable
3. **Create Service Account**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Create new service account
   - Download credentials JSON
   - Save as `backend/credentials.json`
4. **Share Spreadsheet**:
   - Open target Google Sheet
   - Click "Share"
   - Add service account email (from credentials JSON)
   - Grant "Editor" permissions
5. **Copy Spreadsheet ID**:
   - From URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
   - Add to `.env` as `GOOGLE_SHEETS_ID`

### Sheet Structure
Create two sheets in your spreadsheet:
1. **"Receipt Summary"** - Headers: Date | Month | Total Amount | Transaction ID | Last Updated | Receipt URL
   - Date format: dd-mm-YYYY (e.g., "15-01-2024")
   - Month: Hebrew name (e.g., "ינואר" for January)
2. **"Receipt Items"** - Headers: Receipt Date | Month | Transaction ID | Item Name | Category | Quantity | Unit Price | Total Price | Discount | Receipt URL
   - Date format: dd-mm-YYYY (e.g., "15-01-2024")
   - Month: Hebrew name (e.g., "ינואר" for January)

## API Endpoints

### `POST /api/receipt/process`
Process a receipt URL and update Google Sheets.

**Request:**
```json
{
  "url": "https://osher.pairzon.com/..."
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "הקבלה עובדה בהצלחה",
  "data": {
    "date": "15-01-2024",
    "store_name": "אושר עד",
    "items": [...],
    "total_amount": 125.50,
    "transaction_id": "12345",
    "url": "https://..."
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "שגיאה: לא ניתן לטעון את הקבלה",
  "data": null
}
```

## Testing Approach

### Backend Testing
- **Unit Tests**: Test individual services (scraper, parser, sheets) with mocked dependencies
- **Integration Tests**: Test API endpoints with mocked external services
- **Fixtures**: Save sample receipt HTML for consistent parser testing

### Frontend Testing
- **Component Tests**: Test each component in isolation
- **RTL Tests**: Verify Hebrew/English switching and RTL layout
- **Integration Tests**: Test form submission with mocked API

### Manual Testing
Use the example receipt URL for end-to-end testing:
```
https://osher.pairzon.com/dba51f17-81ac-41f8-b76d-64e62fb13df4.html?id=74588a50-4de7-4bd9-b41d-e551452b5b1c&p=1247
```

## Common Commands

```bash
# Install all dependencies (from root)
cd backend && poetry install && cd ../frontend && npm install

# Run development servers
npm run dev  # Both frontend and backend (from root)

# Run tests
cd backend && poetry run pytest
cd frontend && npm test

# Install Playwright browsers (one-time)
cd backend && poetry run playwright install chromium

# Format code (if using formatters)
cd backend && poetry run black app/
cd frontend && npm run format
```

## Coding Standards

### Python (Backend)
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Follow PEP 8 style guide
- Use async/await for I/O operations
- Handle errors with meaningful messages in Hebrew

### JavaScript/React (Frontend)
- Use functional components with hooks
- Keep components small and focused
- Use `const` for all variables (unless reassignment needed)
- Handle loading and error states explicitly
- Internationalize all user-facing text

### CSS
- Use logical properties for RTL support (e.g., `margin-inline-start` instead of `margin-left`)
- Keep styles minimalistic and clean
- Ensure good contrast for accessibility
- Test in both RTL and LTR modes

## Debugging Tips

### Backend Debugging
- **Scraper issues**: Check Playwright browser logs
- **Parser issues**: Save failed HTML to `tests/fixtures/` and examine structure
- **Sheets issues**: Verify service account email has editor access to spreadsheet

### Frontend Debugging
- **API errors**: Check browser Network tab
- **RTL issues**: Test with both `dir="rtl"` and `dir="ltr"`
- **i18n issues**: Verify translation keys exist in both `he.json` and `en.json`

## Future Considerations

### Planned Enhancements (Not in MVP)
- Support for additional receipt formats (other stores)
- Receipt history view in UI
- Duplicate receipt detection
- Receipt search and filtering
- Export to other formats (CSV, Excel)
- Mobile app version

### Extensibility Notes
- Parser service can be extended with strategy pattern for multiple receipt formats
- Google Sheets service can support multiple spreadsheets
- Frontend can add receipt management features

## Important Notes

- **Security**: Never commit `credentials.json` or `.env` files to git
- **Performance**: Playwright scraping takes ~5-10 seconds per receipt
- **Rate Limiting**: Consider implementing rate limiting if scaling to many users
- **Error Handling**: Always return Hebrew error messages to users
- **Testing**: Always test with the example receipt URL before deploying changes
