# Docker Deployment Guide

## Prerequisites
- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- Git

## Environment Variables
Create a `.env` file in the project root with:
```
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
MISTRAL_API_KEY=your_mistral_key
```

## Step-by-Step Local Development
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd assistant_core_v3
   ```

2. Create `.env` file with API keys

3. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Verify deployment:
   - Open http://localhost:8000
   - Check `/docs` for API documentation
   - Test endpoints with curl or Postman

## Production Deployment on Docker
1. Build the production image:
   ```bash
   docker build -t assistant-core-v3:latest .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name assistant-core \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     assistant-core-v3:latest
   ```

3. Check logs:
   ```bash
   docker logs assistant-core
   ```

## Scaling with Docker Swarm/Kubernetes
- Use `docker stack deploy` for Swarm
- Create Kubernetes deployment YAML for k8s
- Configure load balancer for multiple replicas

## Memory Optimization
- Container uses <512MB RAM
- Suitable for Render, Vercel, Railway
- Monitor with `docker stats`

## Troubleshooting
- Port conflicts: Change host port in docker-compose.yml
- API key issues: Check .env file permissions
- Build failures: Ensure all dependencies are in requirements.txt