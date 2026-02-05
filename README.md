# AI Assistant Backend - Production Ready

## 🚀 Project Overview

A production-grade AI Assistant backend with full integration of 8 core services: Safety, Intelligence, Enforcement, Orchestration, Execution, and Bucket logging. Features real email (SendGrid) and WhatsApp (Twilio) execution with complete trace chain tracking.

## ✅ System Status

- **Backend**: Deployed on Render.com - https://ai-assistant-backend-8hur.onrender.com
- **Email Execution**: ✅ Working (SendGrid API)
- **WhatsApp Execution**: ✅ Working (Twilio API)
- **Trace Chain**: ✅ Complete 7-stage tracking
- **Task Management**: ✅ MongoDB with trace_id indexing
- **API Version**: 3.0.0

## 🏗️ Architecture

### Core Services Integration

1. **Safety Service** (Aakansha) - Content validation and risk detection
2. **Intelligence Service** (Sankalp) - Behavioral analysis and context processing
3. **Enforcement Service** (Raj) - Policy enforcement and decision making
4. **Orchestration Service** (Nilesh) - Intent detection and workflow routing
5. **Execution Service** (Chandresh) - Real platform execution (Email, WhatsApp)
6. **Bucket Service** (Ashmit) - Centralized logging and trace tracking

### Trace Chain Flow

```
Request → Intelligence → Safety → Enforcement → Orchestration → Execution → Response
   ↓           ↓           ↓           ↓              ↓             ↓          ↓
trace_id   trace_id    trace_id    trace_id       trace_id      trace_id   trace_id
```

## 📋 Features

### ✅ Implemented

- **Real Email Execution** via SendGrid API (100 emails/day free)
- **Real WhatsApp Execution** via Twilio API (sandbox mode)
- **Full Trace Chain** with deterministic trace_id across all services
- **Task Persistence** in MongoDB with trace_id indexing
- **Safety Validation** with pattern matching and risk categorization
- **Enforcement Policies** with ALLOW/BLOCK/REWRITE decisions
- **Intent Detection** for email, WhatsApp, and general queries
- **API Documentation** via Swagger UI at /docs
- **Health Monitoring** at /health endpoint
- **CORS Support** for frontend integration

### 🔧 Configuration

#### Environment Variables (.env)

```env
# API Configuration
API_KEY=localtest

# Email Configuration (SendGrid - Production)
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=your_verified_email@example.com

# Email Configuration (SMTP - Local/Fallback)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# WhatsApp Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+your_number

# Database Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=ai_assistant
```

## 🚀 Deployment

### Backend (Render.com)

1. **Connect GitHub Repository**
   ```
   Repository: https://github.com/praj33/ai-assistant-backend
   Branch: main
   Root Directory: /
   ```

2. **Build Settings**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Environment Variables** (Set in Render Dashboard)
   - API_KEY
   - SENDGRID_API_KEY
   - SENDGRID_FROM_EMAIL
   - TWILIO_ACCOUNT_SID
   - TWILIO_AUTH_TOKEN
   - TWILIO_WHATSAPP_FROM
   - MONGODB_URI
   - DATABASE_NAME

4. **Deploy**
   - Auto-deploys on git push to main branch
   - Takes ~5-10 minutes
   - Check logs for deployment status

### Local Development

```bash
# Clone repository
git clone https://github.com/praj33/ai-assistant-backend.git
cd ai-assistant-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn app.main:app --reload --port 8000

# Access API
# Swagger UI: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
```

## 📡 API Endpoints

### Main Endpoint

**POST /api/assistant**

Request:
```json
{
  "version": "3.0.0",
  "input": {
    "message": "Send email to user@example.com with subject 'Test' saying 'Hello'",
    "summarized_payload": {}
  },
  "context": {
    "platform": "web",
    "device": "desktop",
    "session_id": null,
    "voice_input": false
  }
}
```

Response:
```json
{
  "version": "3.0.0",
  "status": "success",
  "result": {
    "type": "workflow",
    "response": "Successfully sent email message.",
    "task": {
      "task_type": "email",
      "status": "completed",
      "execution": {
        "status": "success",
        "to": "user@example.com",
        "subject": "Test",
        "message": "Hello",
        "method": "sendgrid",
        "trace_id": "trace_abc123def456",
        "timestamp": "2026-02-04T12:00:00.000000",
        "platform": "email"
      },
      "trace_id": "trace_abc123def456"
    },
    "enforcement": {
      "decision": "ALLOW",
      "scope": "both",
      "trace_id": "trace_abc123def456",
      "reason_code": "CONTENT_ALLOWED"
    },
    "safety": {
      "decision": "allow",
      "risk_category": "clean",
      "confidence": 0.0,
      "reason_code": "clean_content",
      "trace_id": "trace_abc123def456"
    }
  },
  "processed_at": "2026-02-04T12:00:00.000000Z",
  "trace_id": "trace_abc123def456"
}
```

### Task Management

- **GET /tasks** - Get all tasks
- **GET /tasks/{trace_id}** - Get task by trace_id
- **DELETE /tasks/{trace_id}** - Delete task by trace_id

### Monitoring

- **GET /health** - Health check
- **GET /docs** - Swagger UI documentation
- **GET /openapi.json** - OpenAPI schema

## 🧪 Testing

### Test Email Execution

```bash
curl -X POST https://ai-assistant-backend-8hur.onrender.com/api/assistant \
  -H "x-api-key: localtest" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "3.0.0",
    "input": {
      "message": "Send email to test@example.com with subject '\''Test'\'' saying '\''Hello'\''",
      "summarized_payload": {}
    },
    "context": {
      "platform": "web",
      "device": "desktop",
      "session_id": null,
      "voice_input": false
    }
  }'
```

### Test WhatsApp Execution

```bash
curl -X POST https://ai-assistant-backend-8hur.onrender.com/api/assistant \
  -H "x-api-key: localtest" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "3.0.0",
    "input": {
      "message": "Send WhatsApp to +1234567890 saying '\''Hello from AI Assistant'\''",
      "summarized_payload": {}
    },
    "context": {
      "platform": "web",
      "device": "desktop",
      "session_id": null,
      "voice_input": false
    }
  }'
```

## 📊 Trace Chain Verification

Every request generates a unique trace_id that flows through all 7 stages:

1. **request_received** - Initial request logged
2. **intelligence_processing** - Behavioral analysis
3. **safety_validation** - Content safety check
4. **enforcement_decision** - Policy enforcement
5. **orchestration_processing** - Intent detection and routing
6. **action_execution** - Real platform execution
7. **response_generated** - Final response with full chain

Check Render logs to see complete trace chain for each request.

## ⚠️ Known Issues & Solutions

### Issue 1: Frontend Timeout on Cold Start

**Problem**: Render free tier sleeps after 15 minutes. First request takes 30-60 seconds.

**Solution**: 
- Frontend timeout increased to 90 seconds
- Keep-alive script available: `python keep_alive.py`
- Or upgrade to Render paid tier ($7/month)

### Issue 2: MongoDB Connection Warning

**Problem**: Tasks not saving to database (localhost connection refused)

**Solution**: Set MONGODB_URI environment variable in Render dashboard to MongoDB Atlas connection string.

**Impact**: Emails/WhatsApp still work, only task persistence affected.

## 🔐 Security

- API Key authentication required (X-API-Key header)
- Content safety validation on all inputs
- Enforcement policies for harmful content
- CORS configured for specific origins
- Sensitive data in environment variables only

## 📈 Performance

- **Local**: 2-5 seconds per request
- **Production (warm)**: 2-5 seconds per request
- **Production (cold start)**: 30-60 seconds first request after 15 min inactivity
- **Email delivery**: ~1 second via SendGrid
- **WhatsApp delivery**: ~1 second via Twilio

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.10+
- **Database**: MongoDB (Motor async driver)
- **Email**: SendGrid API
- **WhatsApp**: Twilio API
- **Deployment**: Render.com
- **Logging**: Structured JSON logging

## 📝 Project Structure

```
Backend/
├── app/
│   ├── api/
│   │   └── assistant.py          # Main API endpoint
│   ├── core/
│   │   ├── assistant_orchestrator.py  # Central orchestration
│   │   ├── database.py           # MongoDB connection
│   │   ├── intentflow.py         # Intent detection
│   │   ├── summaryflow.py        # Text summarization
│   │   └── taskflow.py           # Task building
│   ├── services/
│   │   ├── safety_service.py     # Aakansha's service
│   │   ├── intelligence_service.py  # Sankalp's service
│   │   ├── enforcement_service.py   # Raj's service
│   │   ├── execution_service.py     # Chandresh's service
│   │   └── bucket_service.py        # Ashmit's service
│   ├── executors/
│   │   ├── email_executor.py     # SendGrid/SMTP email
│   │   └── whatsapp_executor.py  # Twilio WhatsApp
│   ├── routers/
│   │   └── task.py               # Task management endpoints
│   └── main.py                   # FastAPI app initialization
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (local)
├── keep_alive.py                 # Keep server awake script
└── README.md                     # This file
```

## 👥 Team Integration

- **Aakansha** - Safety Service (Content validation)
- **Sankalp** - Intelligence Service (Behavioral analysis)
- **Raj** - Enforcement Service (Policy decisions)
- **Nilesh** - Orchestration Service (Intent & routing)
- **Chandresh** - Execution Service (Platform APIs)
- **Ashmit** - Bucket Service (Centralized logging)
- **Chandragupta** - Frontend UX
- **Yash** - Frontend Integration

## 📞 Support

- **Backend Issues**: Check Render logs at https://dashboard.render.com
- **API Documentation**: https://ai-assistant-backend-8hur.onrender.com/docs
- **Health Check**: https://ai-assistant-backend-8hur.onrender.com/health

## 📄 License

MIT License - See LICENSE file for details

## 🎯 Future Enhancements

- [ ] Instagram execution support
- [ ] Task scheduling and reminders
- [ ] Multi-language support
- [ ] Voice input processing
- [ ] Advanced analytics dashboard
- [ ] Rate limiting per user
- [ ] Webhook support for async notifications

---

**Status**: ✅ Production Ready | **Version**: 3.0.0 | **Last Updated**: February 4, 2026
