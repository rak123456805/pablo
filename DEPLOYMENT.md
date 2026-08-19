# Peblo TV Mini — Render (Backend) + Vercel (Frontend) Deployment Guide

This guide provides step-by-step instructions for deploying:
- **Backend (FastAPI)** $\rightarrow$ **Render**
- **Frontend (React + Vite)** $\rightarrow$ **Vercel**
- **Storage & Database** $\rightarrow$ **Supabase**

---

## 🚀 PART 1: Backend Deployment on Render

### Step 1: Push Code to GitHub
Ensure your latest code is pushed to your GitHub repository.

### Step 2: Create Web Service on Render
1. Go to [render.com](https://render.com) and log into your Dashboard.
2. Click **New +** $\rightarrow$ Select **Web Service**.
3. Connect your GitHub repository.

### Step 3: Configure Render Settings
- **Name**: `peblo-tv-api` (or your choice)
- **Region**: Oregon (US West) or nearest region
- **Branch**: `main`
- **Root Directory**: Leave blank or set to `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Add Environment Variables in Render Dashboard
Go to **Environment** tab in your Render service and add:

| Key | Value |
| :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` |
| `DATABASE_URL` | `postgresql+asyncpg://neondb_owner:npg_2MBj1QyiREeN@ep-solitary-cake-ax18ax3w.c-4.us-east-2.aws.neon.tech/neondb?ssl=require` |
| `DATABASE_SYNC_URL` | `postgresql+psycopg://neondb_owner:npg_2MBj1QyiREeN@ep-solitary-cake-ax18ax3w.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `STORAGE_BACKEND` | `supabase` |
| `SUPABASE_PROJECT_ID` | `yxlpuwplaonbagxuwdnq` |
| `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_BUCKET` | `peblo` |
| `JWT_SECRET_KEY` | `peblo-dev-secret-key-min-32-chars-for-jwt-signing` |
| `CORS_ORIGINS` | `["https://your-app.vercel.app","http://localhost:5173"]` |

Click **Deploy Web Service**. Once deployed, copy your Render API URL (e.g., `https://peblo-tv-api.onrender.com`).

---

## 🎨 PART 2: Frontend Deployment on Vercel

### Step 1: Import Project to Vercel
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **Add New...** $\rightarrow$ Select **Project**.
3. Import your GitHub repository.

### Step 2: Configure Project Settings
- **Framework Preset**: `Vite`
- **Root Directory**: Click Edit and select `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Step 3: Add Environment Variables in Vercel
Under **Environment Variables**, add:

| Key | Value |
| :--- | :--- |
| `VITE_API_BASE_URL` | `https://peblo-tv-api.onrender.com` (Your Render Backend URL) |

### Step 4: Deploy
Click **Deploy**. Vercel will build and publish your frontend app with full SPA routing (`vercel.json` rewrite included).

---

## ⚡ Step 5: Final CORS Update
Once your Vercel URL is generated (e.g. `https://peblo-tv.vercel.app`):
1. Go back to **Render Dashboard** $\rightarrow$ **Environment**.
2. Update `CORS_ORIGINS` to include your exact Vercel URL:
   `["https://peblo-tv.vercel.app", "http://localhost:5173"]`
3. Save changes — Render will automatically restart.

---

## ✅ Deployment Verification Checklist
- [x] Backend Health Endpoint: `https://peblo-tv-api.onrender.com/health` returns `{"status":"ok","db":"ok","storage":"ok"}`
- [x] OpenAPI Docs: `https://peblo-tv-api.onrender.com/docs` opens API playground
- [x] CMS Studio: `https://peblo-tv.vercel.app/publish` allows artwork upload & catalog publish
- [x] Peblo Viewer: `https://peblo-tv.vercel.app/viewer` loads published catalog and displays actual Supabase artwork!
