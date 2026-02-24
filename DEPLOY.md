# Deployment to Render

Simple step-by-step guide to deploy Receipt Analyzer.

## What You Need

| Item | Where to Find |
|------|---------------|
| GitHub repo | Push your code first |
| Render account | [render.com](https://dashboard.render.com) |
| `GOOGLE_SHEETS_ID` | Open your Google Sheet → URL between `/d/` and `/edit` |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `credentials.json` | Download from Google Cloud Console → Service Account → Keys |

---

## Step 1: Deploy Backend

1. Go to [Render Dashboard](https://dashboard.render.com)
2. **New +** → **Web Service**
3. Connect your GitHub repo
4. Configure:

   | Setting | Value |
   |---------|-------|
   | Name | `receipt-analyzer-api` |
   | Region | Closest to you |
   | Branch | `main` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt && python -m playwright install chromium` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

5. Add Environment Variable:

   | Key | Value |
   |-----|-------|
   | `GOOGLE_SHEETS_ID` | Your spreadsheet ID |
   | `GEMINI_API_KEY` | Your Gemini API key |
   | `SCRAPING_TIMEOUT` | `30000` |
   | `FRONTEND_URL` | You'll add this later |

6. Add Secret File (not environment variable):
   - Name: `credentials.json`
   - Contents: Paste full JSON from Google Cloud

7. Set **Health Check**: `/health`

8. Click **Create Web Service**

---

## Step 2: Deploy Frontend

1. **New +** → **Static Site**
2. Connect the same GitHub repo
3. Configure:

   | Setting | Value |
   |---------|-------|
   | Name | `receipt-analyzer` |
   | Branch | `main` |
   | Build Command | `npm install && npm run build` |
   | Publish Directory | `dist` |

4. Add Environment Variable:

   | Key | Value |
   |-----|-------|
   | `VITE_API_BASE_URL` | `https://receipt-analyzer-api.onrender.com` |

5. Add **Redirect/Rewrite** (for React client-side routing):
   - In Render dashboard: go to your static site → **Redirects/Rewrites** → **Add Rewrite**
   - Source: `/*`
   - Destination: `/index.html`
   - Action: **Rewrite**

6. Click **Create Static Site**

---

## Step 3: Connect Both

1. Copy your frontend URL (e.g., `https://receipt-analyzer.onrender.com`)
2. Go to backend **Environment Variables**
3. Add:

   | Key | Value |
   |-----|-------|
   | `FRONTEND_URL` | Your frontend URL |

4. **Redeploy** backend

---

## Done!

Your app is live:
- Frontend: `https://receipt-analyzer.onrender.com`
- Backend: `https://receipt-analyzer-api.onrender.com`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Playwright fails | Use paid plan or lighter browser |
| CORS errors | Update `cors_origins` in `backend/app/config.py` |
| Sheet errors | Share sheet with service account email |
