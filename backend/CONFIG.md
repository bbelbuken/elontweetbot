# Configuration Guide

## Quick Start

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API credentials

3. Start the application

## Required Configuration

### Twitter API (Required)
```bash
TWITTER_BEARER_TOKEN=your_actual_token_here
```

Get it from: https://developer.twitter.com/
- Create a new app
- Generate Bearer Token
- Copy token to `.env`

### Binance Testnet (Required)
```bash
BINANCE_API_KEY=your_testnet_key_here
BINANCE_API_SECRET=your_testnet_secret_here
```

Get it from: https://testnet.binance.vision/
- Register for testnet account
- Generate API key
- Copy key and secret to `.env`

⚠️ **Important**: Use TESTNET, not real Binance!

## Trading Configuration

All trading parameters are configurable via environment variables:

### Signal Threshold (0-100)
```bash
SIGNAL_THRESHOLD=70  # Minimum score to trigger trade
```
- Lower = More trades, higher risk
- Higher = Fewer trades, more selective
- Recommended: 70-80

### Position Size (0.001-0.1)
```bash
POSITION_SIZE_PERCENT=0.01  # 1% of balance per trade
```
- 0.01 = 1% (Recommended for beginners)
- 0.02 = 2% (Moderate risk)
- 0.05 = 5% (High risk)

### Stop Loss (0.01-0.2)
```bash
STOP_LOSS_PERCENT=0.02  # Exit if price drops 2%
```
- 0.02 = 2% loss (Tight stop)
- 0.05 = 5% loss (Loose stop)

### Take Profit (0.01-1.0)
```bash
TAKE_PROFIT_PERCENT=0.04  # Exit if price rises 4%
```
- Should be 2x stop loss for good risk/reward
- 0.04 = 4% profit (Recommended)

### Max Daily Drawdown (0.01-0.5)
```bash
MAX_DAILY_DRAWDOWN=0.05  # Stop trading if lose 5% in a day
```
- Protection against bad days
- 0.05 = 5% (Recommended)

### Max Open Positions (1-20)
```bash
MAX_OPEN_POSITIONS=5  # Max concurrent trades
```
- Lower = Less exposure
- Higher = More diversification

### Manual Override
```bash
MANUAL_OVERRIDE=false  # Auto-execute trades
```
- `true` = Require manual approval for each trade
- `false` = Fully automated trading

## Configuration Validation

The app automatically validates your configuration on startup:

✅ Checks for valid ranges  
✅ Warns about risky settings  
✅ Alerts if API keys are not configured

Example output:
```
==================================================
⚙️  Configuration Loaded
==================================================

📊 Trading Config:
   Signal Threshold: 70
   Position Size: 1.0%
   Stop Loss: 2.0%
   Take Profit: 4.0%
   Max Daily Drawdown: 5.0%
   Max Open Positions: 5
   Manual Override: ✗ Disabled
==================================================
```

## Environment-Specific Configs

You can create different configs for different environments:

- `.env.development` - Local development
- `.env.production` - Production deployment
- `.env.test` - Testing

Load specific env:
```bash
ENV_FILE=.env.production python -m uvicorn app.main:app
```

## Security Best Practices

❌ **Never commit `.env` to git**  
✅ Only commit `.env.example`  
✅ Use strong API keys  
✅ Rotate keys regularly  
✅ Use testnet for development

## Troubleshooting

### Config not loading
- Check `.env` file exists
- Check file permissions
- Restart application

### Invalid API keys
- Verify keys are correct
- Check for extra spaces
- Regenerate keys if needed

### Trading not starting
- Check `MANUAL_OVERRIDE` is `false`
- Verify `SIGNAL_THRESHOLD` is not too high
- Check database is running
