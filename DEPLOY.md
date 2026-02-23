# Deployment to Render

This guide covers deploying the Receipt Analyzer to Render.

## Architecture

- **Backend**: Python FastAPI (Web Service)
- **Frontend**: React/Vite (Static Site)

## Prerequisites

1. Push your code to a GitHub repository
2. Create a Render account

---

## Backend Deployment

### 1. Create a Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---------|-------|
| Name | `receipt-analyzer-api` |
| Region | Choose closest to you |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### 2. Environment Variables

Add these environment variables in the Render dashboard:

| Key | Value |
|-----|-------|
| `GOOGLE_SHEETS_ID` | Your spreadsheet ID |
| `GEMINI_API_KEY` | Your Gemini API key |
| `SCRAPING_TIMEOUT` | `30000` |
| `FRONTEND_URL` | `https://your-frontend.onrender.com` |

#### Option A: credentials.json file (legacy)

| Key | Value |
|-----|-------|
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | `./credentials.json` |

Then upload `credentials.json` as a **Secret File** in Render:
1. Go to your Web Service settings
2. Under **Secret Files**, click **Add Secret File**
3. Name: `credentials.json`
4. Contents: Paste the full JSON content

#### Option B: Environment variable (recommended)

| Key | Value |
|-----|-------|
| `GOOGLE_SHEETS_CREDENTIALS_B64` | Base64-encoded JSON credentials |

To encode your credentials.json:
```bash
base64 -w0 credentials.json
```

### 3. Install Playwright Browsers

Add a post-install script in your build command:

```bash
pip install -r requirements.txt && playwright install chromium
```

Or add a `build.sh` script:

```bash
#!/bin/bash
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Frontend Deployment

### 1. Create a Static Site

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Static Site**
3. Connect your GitHub repository
4. Configure the service:

| Setting | Value |
|---------|-------|
| Name | `receipt-analyzer` |
| Region | Choose closest to you |
| Branch | `main` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |

### 2. Environment Variables

Add this environment variable:

| Key | Value |
|-----|-------|
| `VITE_API_BASE_URL` | `https://your-api-service.onrender.com` |

### 3. Configure Redirects/Rewrites

In your Static Site settings on Render, go to **Redirects/Rewrites** and add:

| Source Path | Destination | Action |
|-------------|-------------|--------|
| `/*` | `/index.html` | Rewrite |

This enables client-side routing.

---

## Health Check

The backend includes a `/health` endpoint. Configure this as your health check path in Render:

- Health Check Path: `/health`

---

## Troubleshooting

### Playwright installation fails
Render's free tier has limited resources. You may need to use a paid plan or install a lighter browser.

### CORS issues
Update `cors_origins` in `backend/app/config.py` to include your frontend's Render URL.

### Environment variables not loading
Make sure `.env` file is not used in production - all secrets should be set in Render dashboard.
