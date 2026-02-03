# Production Deployment Configuration

## Render.com Deployment

### Environment Variables Required

Set these in your Render.com dashboard under your service's **Environment** section:

#### Required
- `API_KEY` - Your API key for authentication (default: `localtest` for development)

#### Optional (for Production Frontend)
- `FRONTEND_URL` - Your production frontend URL (e.g., `https://your-frontend.vercel.app`)
  - This will be added to CORS allowed origins
  - If not set, only localhost origins are allowed

#### Optional (for Monitoring)
- `SENTRY_DSN` - Sentry DSN for error tracking
- `ENV` - Environment name (default: `production`)

### Example Environment Variables

```bash
API_KEY=your_secure_api_key_here
FRONTEND_URL=https://your-frontend-app.vercel.app
ENV=production
```

### CORS Configuration

The backend automatically includes:
- **Localhost origins** (for development):
  - `http://localhost:3000`
  - `http://localhost:3001`
  - `http://127.0.0.1:3000`
  - `http://127.0.0.1:3001`

- **Production origin** (if `FRONTEND_URL` is set):
  - The value of `FRONTEND_URL`
  - Both `http://` and `https://` versions

### Port Configuration

Render automatically sets the `PORT` environment variable. The backend uses:
- Default: `8000` (for local development)
- Production: Uses `os.getenv("PORT", "8000")` if needed

**Note:** Uvicorn should bind to `0.0.0.0` and use the PORT environment variable in production.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Or if Render doesn't support `${PORT}` syntax:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Health Check

After deployment, verify the health endpoint:
```bash
curl https://ai-assistant-backend-70rt.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "3.0.0",
  "timestamp": "2026-01-09T05:28:03.789308Z"
}
```

### Root Endpoint

The root endpoint (`/`) is now available and returns API information:
```bash
curl https://ai-assistant-backend-70rt.onrender.com/
```

### Testing the API

```bash
curl -X POST https://ai-assistant-backend-70rt.onrender.com/api/assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "version": "3.0.0",
    "input": {
      "message": "hello"
    },
    "context": {
      "platform": "web",
      "device": "desktop"
    }
  }'
```

### Frontend Configuration

Update your frontend API URL to:
```typescript
const API_URL = 'https://ai-assistant-backend-70rt.onrender.com/api/assistant';
```

Make sure `FRONTEND_URL` environment variable in Render matches your frontend deployment URL.

---

## Current Deployment Status

✅ Backend deployed at: `https://ai-assistant-backend-70rt.onrender.com`
✅ Health endpoint working: `/health`
✅ Root endpoint working: `/`
✅ Database initialized
✅ CORS configured for localhost + production frontend (if `FRONTEND_URL` is set)

### Next Steps

1. **Set `FRONTEND_URL`** in Render environment variables when you deploy your frontend
2. **Set secure `API_KEY`** in Render (don't use `localtest` in production)
3. **Update frontend** to use the production backend URL
4. **Test the connection** from your deployed frontend

