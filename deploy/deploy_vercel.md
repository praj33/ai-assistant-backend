# Vercel Deployment Guide

## Prerequisites
- Vercel account (free tier available)
- GitHub repository
- Vercel CLI (optional, for advanced config)

## Step-by-Step Deployment
1. **Connect Repository**:
   - Go to Vercel Dashboard
   - Click "New Project"
   - Import your GitHub repo
   - Select `assistant_core_v3` directory if nested

2. **Configure Project**:
    - **Framework Preset**: Other
    - **Root Directory**: assistant_core_v3 (if applicable)
    - **Build Command**: Docker build (Vercel will use Dockerfile)
    - **Output Directory**: (leave empty)
    - **Install Command**: (leave empty when using Docker)

3. **Environment Variables**:
    Add in Vercel project settings:
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
   - **Node.js Version**: 18.x (for compatibility)
   - **Regions**: All (global deployment)
   - **Build Image**: python3.11 (specify Python runtime)

5. **Deploy**:
   - Click "Deploy"
   - Wait for build (may take 5-10 minutes)
   - Get production URL

## API Configuration
- FastAPI routes are handled by Vercel's serverless functions
- Access API at `https://your-project.vercel.app/api/*`
- Interactive docs at `https://your-project.vercel.app/docs`
- Health check at `https://your-project.vercel.app/health`
- Metrics at `https://your-project.vercel.app/metrics`

## Optimization for Vercel
- Keep response times <10 seconds (Vercel limit)
- Use caching for frequent requests
- Minimize cold starts with warm-up functions

## Scaling
- Vercel auto-scales serverless functions
- Monitor usage in dashboard
- Upgrade to Pro for higher limits

## Troubleshooting
- Build fails: Check Python version compatibility and Dockerfile
- Runtime errors: Verify environment variables and check JSON logs
- CORS issues: Configure in FastAPI middleware
- Function timeouts: Keep responses <10 seconds (Vercel limit)
- Health check fails: Verify `/health` endpoint accessibility
- Database persistence: Use Vercel Postgres for production data