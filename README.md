# Amazon Repricer

Automatically match your competitors' lowest price on Amazon — without ever going below your floor. Runs on a schedule, logs every change.

## What it does

1. Pulls current competitor pricing for each ASIN via Amazon SP-API
2. Compares your price to the lowest competitor offer
3. If you're higher, updates your price to match exactly
4. If you're already lowest or equal, does nothing
5. Never goes below your configured minimum (floor) price
6. Logs every price change with timestamp for full transparency

## Quick Start

### Test with mock data (no Amazon account needed)

```bash
pip install -r requirements.txt
python main.py --once --mock
```

You'll see 5 sample ASINs get repriced to match mock competitor prices.

### Run with real Amazon SP-API

```bash
# Set your credentials
export SELLER_ID="your_seller_id"
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export SP_API_REFRESH_TOKEN="your_refresh_token"
export LWA_CLIENT_ID="your_lwa_client_id"
export LWA_CLIENT_SECRET="your_lwa_client_secret"
export MOCK_MODE="false"

# Test once
python main.py --once

# Run on schedule (every 30 min)
python main.py
```

## Configuration

### ASINs and Floor Prices (`asins.csv`)

```csv
asin,min_price,max_price,enabled
B08N5WRWNW,25.00,45.00,true
B07XJ8C8F5,40.00,60.00,true
```

Edit this file to add/remove ASINs or change floor prices. No code changes needed.

### Admin Panel (Web UI)

Open `admin.html` in your browser to manage ASINs visually:
- Add/remove ASINs
- Set min price (floor) and max price (ceiling)
- Enable/disable individual ASINs
- Export to CSV (download as `asins.csv`)

### Timing

```bash
# Run every 15 minutes
python main.py --interval 15

# Run every hour
python main.py --interval 60

# Cron job (every 30 min)
*/30 * * * * cd /path/to/repricer && python main.py --once >> repricer.log 2>&1
```

## Amazon SP-API Setup

### Step 1: Register as Amazon Developer
1. Go to https://developer.amazon.com
2. Sign in with your Amazon seller account
3. Developer Console → Apps and Services → Create new app (type: SP-API)

### Step 2: Get LWA Credentials
1. In your app → Login with Amazon
2. Note your **Client ID** and **Client Secret**

### Step 3: Get SP-API Refresh Token
1. Go to https://sellercentral.amazon.com
2. Apps & Services → Develop Apps → Your App → "Authorize"
3. Copy the **Refresh Token**

### Step 4: Get AWS Credentials
1. AWS IAM Console → Create user with `SellingPartnerAPI` policy
2. Note **Access Key ID** and **Secret Access Key**

### Step 5: Configure
Edit `config.json` with your credentials (or use environment variables).

### Step 6: Test
```bash
python main.py --once
```

### Step 7: Deploy
**Option A: Small cloud instance (DigitalOcean, AWS EC2, etc.)**
```bash
pip install -r requirements.txt
# Add cron job (see Timing section above)
```

**Option B: AWS Lambda**
1. Package code + dependencies as zip
2. Create Lambda function (Python 3.11)
3. Set environment variables
4. Create EventBridge rule (every 30 min)
5. CloudWatch logs for monitoring

## Log Format

Every price change is logged with timestamp:

```
2026-11-24 10:30:00 [INFO] B08N5WRWNW: My price=$34.99, Lowest competitor=$29.04, Floor=$25.00
2026-11-24 10:30:00 [INFO]   -> Updated: $34.99 -> $29.04
```

Logs are saved to `repricer.log` (configurable).

## Requirements
- Python 3.10+
- Amazon Seller Account
- Amazon SP-API credentials
- AWS IAM credentials

## License
MIT