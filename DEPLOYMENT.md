# Backend Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init

# Add PostgreSQL and Redis
railway add postgresql
railway add redis

# Set environment variables
railway variables set TWITTER_BEARER_TOKEN=your_token
railway variables set BINANCE_API_KEY=your_key
railway variables set BINANCE_API_SECRET=your_secret

# Deploy
railway up
```

### Option 2: Fly.io
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Add PostgreSQL
fly postgres create

# Add Redis
fly redis create

# Set secrets
fly secrets set TWITTER_BEARER_TOKEN=your_token
fly secrets set BINANCE_API_KEY=your_key
fly secrets set BINANCE_API_SECRET=your_secret

# Deploy
fly deploy
```

### Option 3: Render
1. Connect GitHub repo
2. Create PostgreSQL database
3. Create Redis instance
4. Create Web Service
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Add environment variables
6. Deploy

## 🐳 Docker Deployment

### Local Development
```bash
# Start all services (DB, Redis, Grafana)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

### Production Build
```bash
# Build backend image
docker build -t trading-bot-backend ./backend

# Run backend
docker run -p 8000:8000 --env-file .env trading-bot-backend
```

## 📋 Pre-Deployment Checklist

- [ ] `.env` file configured with real API keys
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Test endpoints working (`/health`, `/metrics`)
- [ ] Celery workers configured
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Logs configured
- [ ] Secrets secured (not in git)

## 🔧 Environment Variables (Production)

Required:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# API Keys
TWITTER_BEARER_TOKEN=actual_token
BINANCE_API_KEY=actual_key
BINANCE_API_SECRET=actual_secret

# App Config
DEBUG=false
APP_VERSION=1.0.0
```

## 🏃 Running Components

### 1. FastAPI Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Celery Worker
```bash
celery -A workers.celery_app worker -l info
```

### 3. Celery Beat (Scheduler)
```bash
celery -A workers.celery_app beat -l info
```

## 📊 Health Checks

- **Backend**: `http://your-domain.com/health`
- **API Docs**: `http://your-domain.com/docs`
- **Metrics**: `http://your-domain.com/metrics`
- **Grafana**: `http://your-domain.com:3001` (if deployed)

## 🔐 Security Notes

- Use PostgreSQL SSL in production
- Enable CORS only for your frontend domain
- Use strong passwords for Redis/PostgreSQL
- Rotate API keys regularly
- Use environment variables, never hardcode secrets

## 📈 Monitoring

Prometheus metrics available at `/metrics`:
- `tweets_processed_total` - Total tweets processed
- `trades_executed_total` - Total trades executed
- `current_pnl` - Current profit/loss
- `worker_task_duration_seconds` - Task execution time
- `health_check_status` - Service health

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check database connection
psql $DATABASE_URL

# Check Redis connection
redis-cli -u $REDIS_URL ping
```

### Workers not running
```bash
# Check Celery logs
docker-compose logs tweet-worker

# Check Redis connection
redis-cli -u $REDIS_URL ping

# Restart workers
docker-compose restart tweet-worker
```

### Database migration issues
```bash
# Check current version
alembic current

# Run migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## 🔄 CI/CD Example (GitHub Actions)

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## 📝 Notes

- **Database**: PostgreSQL 15+ recommended
- **Redis**: 7.0+ recommended
- **Python**: 3.11+ required
- **Memory**: Minimum 512MB, recommended 1GB+
- **Storage**: Minimum 1GB for logs and data

## 🆘 Support

If deployment fails:
1. Check environment variables
2. Verify API keys are valid
3. Check service logs
4. Ensure database is accessible
5. Verify Redis connection
