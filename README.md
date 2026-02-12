# Receipt Analyzer - מנתח קבלות

A web application that automates receipt data extraction and Google Sheets integration. Users paste a receipt URL (from Osher/Pairzon), and the system scrapes the receipt, extracts structured data, and updates a Google Sheets document.

## Features

- 🔍 **Automated Scraping**: Uses Playwright to handle JavaScript-rendered receipts
- 📊 **Google Sheets Integration**: Automatically updates two sheets (summary + detailed items)
- 🏷️ **Smart Categorization**: AI-powered item classification using Google Gemini with intelligent caching
- 🌐 **Bilingual**: Hebrew (primary) and English support with RTL layout
- 🎨 **Clean UI**: Minimalistic, accessible design
- 📱 **Responsive**: Works on desktop and mobile devices
- ⚡ **Fast**: Built with modern async Python and React

## Technology Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Playwright** for headless browser scraping
- **BeautifulSoup4** for HTML parsing
- **Google Sheets API v4** for spreadsheet integration
- **Google Gemini Flash** for AI-powered item categorization
- **RapidFuzz** for fuzzy string matching
- **Pydantic** for data validation

### Frontend
- **React 18** with **Vite**
- **react-i18next** for internationalization
- **Axios** for API communication

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Google Cloud Platform account (for Sheets API)
- Service account credentials JSON
- Google AI Studio API key (for Gemini - free tier available)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd receipt-analyzer
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt

# Install Playwright browsers
poetry run playwright install chromium

# Create .env file from example
cp .env.example .env
# Edit .env and add your configuration
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file from example
cp .env.example .env
```

### 4. Google AI Studio Setup

1. **Get Gemini API Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Click "Get API key" or "Create API key"
   - Create a new project or select existing
   - Copy the API key
   - Add to `backend/.env` as `GEMINI_API_KEY`

**Note**: Google Gemini Flash offers a generous free tier (1,500 requests/day, 1M tokens/day). The categorization system uses intelligent caching to minimize API calls - most items will be classified via fuzzy matching without hitting the API.

### 5. Google Sheets Setup

1. **Create Google Cloud Project**: Visit [Google Cloud Console](https://console.cloud.google.com/)
2. **Enable Google Sheets API**: In API Library, search for "Google Sheets API" and enable it
3. **Create Service Account**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Create new service account with "Editor" role
   - Download credentials JSON
   - Save as `backend/credentials.json`
4. **Share Your Spreadsheet**:
   - Create a new Google Sheet or use existing
   - Click "Share"
   - Add service account email (from credentials JSON)
   - Grant "Editor" permissions
5. **Create Sheets Structure**:
   - Create two sheets in your spreadsheet:
     - **"Receipt Summary"** with headers: Date | Store Name | Total Amount | Transaction ID | Receipt URL
     - **"Receipt Items"** with headers: Receipt Date | Store Name | Item Name | **Category** | Quantity | Unit Price | Total Price | Discount | Transaction ID | Receipt URL
6. **Copy Spreadsheet ID**:
   - From URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
   - Add to `backend/.env` as `GOOGLE_SHEETS_ID`

## Running the Application

### Development Mode

**Option 1: Run separately**

Terminal 1 (Backend):
```bash
cd backend
poetry run uvicorn main:app --reload
# Backend runs on http://localhost:8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

**Option 2: Run together (recommended)**

From the root directory:
```bash
npm run dev
# Requires root package.json with concurrently
```

### Production Build

Backend:
```bash
cd backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm run build
npm run preview
```

## Usage

1. **Open the Application**: Navigate to http://localhost:5173
2. **Paste Receipt URL**: Enter an Osher/Pairzon receipt URL (e.g., https://osher.pairzon.com/...)
3. **Submit**: Click "שלח קבלה" (Send Receipt)
4. **Wait**: The system will scrape, parse, classify items, and update your Google Sheet (~5-10 seconds)
5. **Verify**: Check your Google Sheet for the new data with categorized items

## Item Categorization

The application automatically categorizes each receipt item using a smart caching system:

### How It Works
1. **Cache-First**: Checks if the item exists in the local cache (`backend/data/categories.json`)
2. **Fuzzy Matching**: Uses similarity scoring to match variations (e.g., "חלב 3%" matches "חלב")
3. **AI Classification**: If no match found, calls Google Gemini API to classify the item
4. **Auto-Learning**: New classifications are automatically cached for future use

### Available Categories
- **חלבי** (Dairy)
- **מאפים** (Bakery)
- **ירקות** (Vegetables)
- **פירות** (Fruits)
- **בשר ועוף** (Meat & Poultry)
- **דגים** (Fish)
- **קפואים** (Frozen)
- **משקאות** (Beverages)
- **חטיפים** (Snacks)
- **ניקיון** (Cleaning)
- **היגיינה** (Personal Care)
- **אחר** (Other)

### Customization
- Edit `backend/data/categories.json` to add common items and reduce API calls
- Adjust fuzzy matching threshold in `.env` with `CATEGORIES_CACHE_FUZZY_THRESHOLD` (0-100)

### Example Receipt URL

```
https://osher.pairzon.com/dba51f17-81ac-41f8-b76d-64e62fb13df4.html?id=74588a50-4de7-4bd9-b41d-e551452b5b1c&p=1247
```

## API Documentation

Once the backend is running, visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoint

**POST /api/receipt/process**

Request:
```json
{
  "url": "https://osher.pairzon.com/..."
}
```

Response:
```json
{
  "success": true,
  "message": "הקבלה עובדה בהצלחה",
  "data": {
    "date": "2024-01-15T10:30:00",
    "store_name": "אושר עד",
    "items": [...],
    "total_amount": 125.50,
    "transaction_id": "12345",
    "url": "https://..."
  }
}
```

## Project Structure

```
receipt-analyzer/
├── CLAUDE.md                 # Project guidelines for Claude
├── README.md                 # This file
├── .gitignore               # Git ignore rules
├── backend/                 # Python FastAPI backend
│   ├── main.py              # FastAPI app entry point
│   ├── pyproject.toml       # Python dependencies
│   ├── .env                 # Environment variables (create from .env.example)
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # Business logic (scraper, parser, sheets)
│   │   ├── models/          # Pydantic models
│   │   └── config.py        # Configuration
│   └── tests/               # Backend tests
└── frontend/                # React + Vite frontend
    ├── src/
    │   ├── components/      # React components
    │   ├── services/        # API client
    │   ├── i18n/           # Translations (Hebrew, English)
    │   ├── styles/         # CSS files
    │   ├── App.jsx         # Main app component
    │   └── main.jsx        # Entry point
    ├── package.json         # Node dependencies
    └── vite.config.js       # Vite configuration
```

## Testing

### Backend Tests

```bash
cd backend
poetry run pytest
poetry run pytest --cov=app  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
GOOGLE_SHEETS_ID=your-spreadsheet-id-here

# Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# Categorization Configuration (optional)
CATEGORIES_CACHE_PATH=./data/categories.json
CATEGORIES_CACHE_FUZZY_THRESHOLD=80

# Scraping Configuration
SCRAPING_TIMEOUT=30000

# Application Configuration
ENVIRONMENT=development
```

### Frontend Environment Variables

Create `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Troubleshooting

### Common Issues

**1. Playwright Browser Not Found**
```bash
cd backend
poetry run playwright install chromium
```

**2. Google Sheets Permission Denied**
- Verify service account email has "Editor" access to spreadsheet
- Check that credentials.json file exists and is valid
- Confirm GOOGLE_SHEETS_ID in .env matches your spreadsheet

**3. Scraping Timeout**
- Increase SCRAPING_TIMEOUT in backend/.env
- Check receipt URL is accessible
- Verify internet connection

**4. CORS Errors**
- Ensure backend is running on port 8000
- Check CORS_ORIGINS in backend config includes frontend URL
- Verify Vite proxy configuration

**5. Hebrew Text Display Issues**
- Ensure proper UTF-8 encoding
- Check that font supports Hebrew characters
- Verify RTL (dir="rtl") is set correctly

## Development

### Adding Support for New Receipt Formats

Currently, the parser is specific to Osher/Pairzon receipts. To add support for other formats:

1. Create a new parser class in `backend/app/services/parser.py`
2. Implement format detection logic
3. Update the API endpoint to use the appropriate parser

### Adding New Features

See [CLAUDE.md](CLAUDE.md) for:
- Coding standards
- Architecture patterns
- Development workflow
- Testing approach

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Security Notes

- Never commit `credentials.json` or `.env` files
- Keep service account credentials secure
- Validate all user inputs
- Use HTTPS in production
- Regularly update dependencies

## Performance

- Scraping takes ~5-10 seconds per receipt
- Consider implementing rate limiting for production
- Use caching for repeated requests if needed

## Future Enhancements

- [ ] Support for multiple receipt formats
- [ ] Receipt history view in UI
- [ ] Duplicate receipt detection
- [ ] Search and filtering
- [ ] Export to CSV/Excel
- [ ] Mobile app
- [ ] Real-time processing status

## License

[Your License Here]

## Support

For issues and questions:
- Check [CLAUDE.md](CLAUDE.md) for development guidelines
- Review troubleshooting section above
- Open an issue on GitHub

---

Made with ❤️ using Claude Code
