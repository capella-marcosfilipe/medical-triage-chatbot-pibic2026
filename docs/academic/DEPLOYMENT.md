# Deployment Guide

This guide covers different deployment options for the Medical Triage Chatbot API.

## Prerequisites

- Python 3.8 or higher
- Google Gemini API Key ([get one here](https://ai.google.dev/))
- Git

## Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/capella-marcosfilipe/chatbot-triagem-medica-pibic25-26.git
cd chatbot-triagem-medica-pibic25-26

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 3. Run the Server

```bash
python main.py
```

Access at: `http://localhost:8001`

Documentation: `http://localhost:8001/docs`

---

## Deploy to Render.com (Recommended)

[Render](https://render.com) provides free hosting for web services.

### Steps:

1. **Sign up** at [render.com](https://render.com)

2. **Create a New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure the Service**
   - **Name**: `chatbot-triagem-medica`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables**
   - Go to "Environment" tab
   - Add: `GOOGLE_API_KEY` = your_api_key

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Your API will be available at: `https://your-service.onrender.com`

### Update Frontend URL

Update the frontend's `script.js`:
```javascript
const API_BASE_URL = "https://your-service.onrender.com/api/v1";
```

---

## Deploy to Heroku

### Prerequisites
- Heroku CLI installed ([download here](https://devcenter.heroku.com/articles/heroku-cli))

### Steps:

1. **Login to Heroku**
```bash
heroku login
```

2. **Create Procfile**
```bash
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

3. **Create Heroku App**
```bash
heroku create your-app-name
```

4. **Set Environment Variables**
```bash
heroku config:set GOOGLE_API_KEY=your_api_key_here
```

5. **Deploy**
```bash
git push heroku main
```

6. **Open the App**
```bash
heroku open
```

Your API will be at: `https://your-app-name.herokuapp.com`

---

## Deploy to Railway

[Railway](https://railway.app) offers easy deployment with GitHub integration.

### Steps:

1. **Sign up** at [railway.app](https://railway.app)

2. **New Project from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   - Go to "Variables" tab
   - Add: `GOOGLE_API_KEY` = your_api_key

4. **Configure Start Command**
   - Railway auto-detects Python
   - Ensure start command is: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Deploy**
   - Railway automatically deploys on git push
   - Get your public URL from the dashboard

---

## Deploy to Google Cloud Run

### Prerequisites
- Google Cloud SDK installed
- GCP Project created

### Steps:

1. **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. **Build and Push**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-triagem
```

3. **Deploy to Cloud Run**
```bash
gcloud run deploy chatbot-triagem \
  --image gcr.io/PROJECT_ID/chatbot-triagem \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_api_key
```

---

## Deploy with Docker

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. Build Image

```bash
docker build -t chatbot-triagem-medica .
```

### 3. Run Container

```bash
docker run -d \
  -p 8001:8001 \
  -e GOOGLE_API_KEY=your_api_key \
  --name chatbot-triagem \
  chatbot-triagem-medica
```

### 4. Access

API available at: `http://localhost:8001`

---

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google Gemini API Key | Yes | - |
| `APP_HOST` | Host address | No | `0.0.0.0` |
| `APP_PORT` | Port number | No | `8001` |
| `DEBUG` | Debug mode | No | `False` |
| `FRONTEND_URL` | Frontend URL for CORS | No | `http://localhost:3000` |

---

## Testing Deployment

After deployment, test your API:

```bash
# Replace with your deployment URL
export API_URL="https://your-deployment-url.com"

# Test health check
curl $API_URL/health

# Test API info
curl $API_URL/

# Test documentation
open $API_URL/docs
```

---

## Troubleshooting

### Common Issues

1. **Port Binding Error**
   - Ensure `APP_PORT` environment variable is set correctly
   - Cloud platforms often use `$PORT` variable

2. **CORS Issues**
   - Check that frontend URL is allowed in CORS settings
   - Current config allows all origins (`*`) for development

3. **API Key Not Working**
   - Verify `GOOGLE_API_KEY` is set correctly
   - Check API key has proper permissions in Google Cloud Console

4. **Module Not Found**
   - Ensure all dependencies are in `requirements.txt`
   - Try: `pip install -r requirements.txt --upgrade`

### Logs

**Render**: View logs in dashboard

**Heroku**: `heroku logs --tail`

**Railway**: View logs in project dashboard

**Docker**: `docker logs chatbot-triagem`

---

## Monitoring

### Health Check Endpoint

Use `/health` for monitoring:

```bash
curl https://your-api.com/health
```

Response:
```json
{
  "status": "healthy"
}
```

### Uptime Monitoring Services

- [UptimeRobot](https://uptimerobot.com/)
- [Pingdom](https://www.pingdom.com/)
- [StatusCake](https://www.statuscake.com/)

---

## Security Considerations

1. **API Key Protection**
   - Never commit `.env` file
   - Use environment variables
   - Rotate keys periodically

2. **CORS Configuration**
   - Update CORS in production to allow only your frontend domain
   - Edit `main.py` CORS settings

3. **Rate Limiting**
   - Consider adding rate limiting for production
   - Use middleware or API gateway

4. **HTTPS**
   - Always use HTTPS in production
   - Most platforms provide SSL certificates automatically

---

## Next Steps

- Set up CI/CD pipeline
- Add database for persistent storage
- Implement user authentication
- Add logging and monitoring
- Set up backup strategy
