# Render Deployment Guide

## Prerequisites
- Render account (free tier available)
- GitHub repository with the code
- API keys for LLMs

## Step-by-Step Deployment
1. **Connect Repository**:
   - Go to Render Dashboard
   - Click "New" > "Web Service"
   - Connect your GitHub repo
   - Select the `assistant_core_v3` branch

2. **Configure Build Settings**:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**:
    Add these in Render's Environment section:
    ```
    ENV=production
    API_KEY=your_secure_api_key
    JWT_SECRET_KEY=your_jwt_secret_key
    DATABASE_URL=sqlite+aiosqlite:///./data/tasks.db
    OPENAI_API_KEY=your_key
    GROQ_API_KEY=your_key
    GOOGLE_API_KEY=your_key
    MISTRAL_API_KEY=your_key
    SENTRY_DSN=your_sentry_dsn (optional)
    LOG_LEVEL=INFO
    ```

4. **Advanced Settings**:
    - **Instance Type**: Starter (free, 512MB RAM) or upgrade for production workloads
    - **Region**: Choose closest to users
    - **Health Check Path**: `/health`
    - **Health Check Timeout**: 30 seconds
    - **Persistent Disk**: Add for database persistence (if using SQLite)

5. **Deploy**:
   - Click "Create Web Service"
   - Wait for build and deployment (5-10 minutes)
   - Get the URL from Render dashboard

## Post-Deployment
- Test API at `https://your-service.onrender.com`
- Check `/docs` for interactive API docs
- Verify health endpoint: `https://your-service.onrender.com/health`
- Check metrics endpoint: `https://your-service.onrender.com/metrics`
- Monitor logs in Render dashboard (now in JSON format)
- Setup monitoring alerts for health checks

## Scaling
- Upgrade to paid plans for more RAM/CPU
- Use persistent disks for data storage
- Enable auto-scaling for high traffic

## Troubleshooting
- Build fails: Check requirements.txt for missing deps
- Runtime errors: Check environment variables and logs (JSON format)
- Health check fails: Verify `/health` endpoint is accessible
- Database issues: Check persistent disk configuration
- Timeout: Optimize API response times (<30s for Render)
- Memory issues: Monitor `/metrics` endpoint and upgrade instance type