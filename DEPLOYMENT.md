# Deployment Guide

## ⚠️ Important Note on Vercel

**Vercel is NOT recommended for this app** because:
- Vercel uses serverless functions (stateless)
- SQLite file database won't persist between requests
- File uploads won't work

**Better alternatives:** Railway, Render, Fly.io, DigitalOcean

---

## 🚀 Option 1: Railway (Recommended)

Railway is the easiest option with free tier and PostgreSQL support.

### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Initialize project
   cd Personal_Finance_Tool
   railway init
   ```

3. **Add PostgreSQL**
   - In Railway dashboard, click "New" → "Database" → "PostgreSQL"
   - Copy the `DATABASE_URL`

4. **Set Environment Variables**
   ```bash
   railway variables set SECRET_KEY="your-super-secret-key-here"
   railway variables set DEBUG="false"
   railway variables set JSON_LOGS="true"
   ```

5. **Deploy**
   ```bash
   railway up
   ```

6. **Get URL**
   - Railway will provide a public URL like `https://your-app.up.railway.app`

---

## 🌐 Option 2: Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)

2. **Create PostgreSQL Database**
   - Dashboard → New → PostgreSQL
   - Copy Internal Database URL

3. **Create Web Service**
   - Dashboard → New → Web Service
   - Connect GitHub repo
   - Settings:
     - **Root Directory:** `backend`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**
   ```
   SECRET_KEY=your-super-secret-key
   DATABASE_URL=postgresql://... (from step 2)
   DEBUG=false
   JSON_LOGS=true
   ```

5. **Deploy** - Automatic on push

---

## 🔷 Option 3: Vercel (Limited)

⚠️ **Limitations:** SQLite won't work. Need external PostgreSQL (Neon, Supabase).

### Steps:

1. **Get External PostgreSQL**
   - Use [Neon](https://neon.tech) (free tier)
   - Or [Supabase](https://supabase.com)
   - Copy connection string

2. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

3. **Set Secrets**
   ```bash
   cd Personal_Finance_Tool
   vercel secrets add secret-key "your-super-secret-key"
   vercel secrets add database-url "postgresql://..."
   ```

4. **Deploy**
   ```bash
   vercel
   ```

5. **Production Deploy**
   ```bash
   vercel --prod
   ```

---

## 🐳 Option 4: Docker (Any Cloud)

Already included! Use `docker-compose.yml` for any cloud that supports Docker.

```bash
# Build and run
docker-compose up -d

# With PostgreSQL
docker-compose -f docker-compose.yml up -d
```

Deploy to:
- **DigitalOcean App Platform**
- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Apps**

---

## 🔐 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | `your-256-bit-secret` |
| `DATABASE_URL` | Database connection | `postgresql://user:pass@host/db` |
| `DEBUG` | Enable debug mode | `false` |
| `JSON_LOGS` | JSON formatted logs | `true` |
| `CORS_ORIGINS` | Allowed origins | `["https://yourdomain.com"]` |

---

## 📋 Pre-Deployment Checklist

- [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set `DEBUG=false`
- [ ] Configure PostgreSQL database
- [ ] Test locally with production settings
- [ ] Set up monitoring/logging

---

## 🔍 Monitoring

The app includes:
- **Health endpoint:** `GET /health`
- **Structured JSON logs** (when `JSON_LOGS=true`)
- **Request ID** in all logs and response headers

Example log:
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "message": "[abc123] GET /expenses - 200 (45.2ms)",
  "request_id": "abc123",
  "status_code": 200,
  "duration_ms": 45.2
}
```

