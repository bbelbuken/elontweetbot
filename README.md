# Tweet-Driven Crypto Trading Bot

A full-stack, production-ready trading bot that monitors social media for crypto-related content, analyzes sentiment, and executes automated trades on Binance Testnet.

## Architecture

- **Backend**: FastAPI + Celery workers for async processing
- **Frontend**: Next.js dashboard with real-time monitoring
- **Database**: PostgreSQL for data persistence
- **Message Queue**: Redis for Celery task distribution
- **Monitoring**: Prometheus + Grafana for observability

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd tweet-crypto-trading-bot
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API credentials
# - Twitter API credentials from https://developer.twitter.com/
# - Binance Testnet API credentials from https://testnet.binance.vision/
```

### 3. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 4. Access the Application

- **Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload

# Start Celery workers
celery -A workers.tweet_ingestion worker --loglevel=info
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Configuration

### Environment Variables

Key configuration options:

- `SIGNAL_THRESHOLD`: Minimum signal score to trigger trades (default: 70)
- `POSITION_SIZE_PERCENT`: Position size as % of account balance (default: 0.01)
- `MAX_DAILY_DRAWDOWN`: Maximum daily loss limit (default: 0.05)
- `MANUAL_OVERRIDE`: Require manual approval for trades (default: false)

### Trading Parameters

Adjust trading behavior via environment variables:

```bash
SIGNAL_THRESHOLD=75
POSITION_SIZE_PERCENT=0.005
STOP_LOSS_PERCENT=0.02
TAKE_PROFIT_PERCENT=0.04
MAX_OPEN_POSITIONS=3
```

## Security

- **Testnet Only**: Uses Binance Testnet API exclusively
- **Environment Variables**: All secrets managed via environment variables
- **Container Security**: Non-root users in Docker containers
- **Input Validation**: Pydantic models for request validation

## Monitoring

### Health Checks

- **Backend**: `GET /health`
- **Database**: Connection pooling with health checks
- **Redis**: Connection monitoring
- **External APIs**: Circuit breaker pattern

### Metrics

- Tweets processed per minute
- Trades executed and PnL
- API response times
- Worker queue lengths
- System resource usage

## Deployment

### Local Development

Use Docker Compose for local development with hot reloading.

### Production Deployment

#### Backend (Fly.io/Railway)

```bash
# Build and deploy backend
docker build -t trading-bot-backend ./backend
# Deploy to your preferred platform
```

#### Frontend (Vercel)

```bash
cd frontend
# Deploy to Vercel
vercel --prod
```

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/                # Main application
│   ├── workers/            # Celery workers
│   ├── config/             # Configuration management
│   └── migrations/         # Database migrations
├── frontend/               # Next.js frontend
│   ├── src/pages/         # Next.js pages
│   ├── src/components/    # React components
│   └── src/lib/           # Utilities and API client
├── monitoring/            # Prometheus and Grafana config
├── docker-compose.yml     # Local development setup
└── .env.example          # Environment variables template
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.