# Amazon Repricer

Automated Amazon repricer that matches the lowest competitor price while respecting your floor price. Runs on a schedule, logs every change.

## Features

- 📊 Pulls competitor pricing via Amazon SP-API
- ⚖️ Matches lowest competitor price (never higher, never below floor)
- 🛡️ Per-ASIN minimum price (floor) enforcement
- 📝 Logs every price change for transparency
- ⏰ Cron-scheduled (adjustable interval)
- 🧪 Mock mode for testing (no Amazon account needed)
- 📄 CSV config for ASINs and min prices

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
Edit `asins.csv` with your ASINs and minimum prices:
```csv
asin,min_price,max_price,enabled
B08N5WRWNW,25.00,45.00,true
```

### 3. Test with mock mode (no Amazon account needed)
```bash
python main.py --once --mock
```

### 4. Run with real SP-API
Set environment variables or edit `config.json`:
```bash
export SELLER_ID="your_seller_id"
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export SP_API_REFRESH_TOKEN="your_refresh_token"
export LWA_CLIENT_ID="your_lwa_client_id"
export LWA_CLIENT_SECRET="your_lwa_client_secret"
export MOCK_MODE="false"

python main.py --once
```

### 5. Run on schedule
```bash
python main.py  # runs every 30 minutes (configurable)
```

## Amazon SP-API Setup Guide

### Step 1: Register as Amazon Developer
1. Go to https://developer.amazon.com
2. Sign in with your Amazon seller account
3. Go to "Developer Console" → "Apps and Services"
4. Create a new app (type: "SP-API")

### Step 2: Get LWA Credentials
1. In your app, go to "Login with Amazon"
2. Note your **Client ID** and **Client Secret**

### Step 3: Get SP-API Refresh Token
1. Go to https://sellercentral.amazon.com
2. Apps & Services → Develop Apps → Your App → "Authorize"
3. Copy the **Refresh Token**

### Step 4: Get AWS Credentials
1. Go to AWS IAM Console
2. Create a user with `SellingPartnerAPI` policy
3. Note **Access Key ID** and **Secret Access Key**

### Step 5: Configure
Edit `config.json`:
```json
{
  "seller_id": "YOUR_SELLER_ID",
  "marketplace_id": "ATVPDKIKX0DER",
  "region": "us-east-1",
  "access_key": "YOUR_AWS_ACCESS_KEY",
  "secret_key": "YOUR_AWS_SECRET_KEY",
  "refresh_token": "YOUR_SP_API_REFRESH_TOKEN",
  "lwa_client_id": "YOUR_LWA_CLIENT_ID",
  "lwa_client_secret": "YOUR_LWA_CLIENT_SECRET",
  "mock_mode": false,
  "schedule_interval_minutes": 30,
  "log_file": "repricer.log"
}
```

### Step 6: Deploy on Cloud (Cron)
```bash
# On a small VPS (DigitalOcean, AWS EC2, etc.)
# Install Python and dependencies
pip install -r requirements.txt

# Run with cron (every 30 minutes)
crontab -e
# Add: */30 * * * * cd /path/to/repricer && python main.py --once >> repricer.log 2>&1
```

### Step 7: Deploy on AWS Lambda
1. Package the code with dependencies
2. Create Lambda function (Python 3.11)
3. Set environment variables
4. Create EventBridge rule (every 30 minutes)
5. CloudWatch logs for monitoring

## Log Format
Every price change is logged:
```
2026-11-24 10:30:00 [INFO] B08N5WRWNW: My price=$34.99, Lowest competitor=$28.99, Floor=$25.00
2026-11-24 10:30:00 [INFO]   -> Updated: $34.99 -> $28.99
```

## Requirements
- Python 3.10+
- Amazon Seller Account
- Amazon SP-API credentials
- AWS IAM credentials

## License
MIT