# Cloud-Driven Financial Strategies: Monte Carlo Simulation for Stock Market Risk Analysis

> MSc Data Science Project | University of Surrey | AWS + Google Cloud Platform

## Overview

A hybrid cloud platform that runs **Monte Carlo simulations** on live stock market data (MSFT) to compute **Value at Risk (VaR)** at 95% and 99% confidence levels. Built across AWS and GCP, the system identifies candlestick trading signals (Three White Soldiers / Three Black Crows) and simulates thousands of return scenarios to quantify financial risk.

Live deployment: [https://cloudmsftnew.nw.r.appspot.com](https://cloudmsftnew.nw.r.appspot.com)

---

## Architecture

```
User (Browser)
     │
     ▼
Google App Engine (GAE)          ← Frontend / UI (index.py)
     │
     ▼
Amazon API Gateway               ← Request routing & authentication
     │
     ├──── AWS Lambda ───────────── Lightweight simulations (lambda_function.py)
     │
     └──── Amazon EC2 ────────────── Heavy Monte Carlo simulations (ec2.py)
                │
                ▼
          Amazon S3               ← Results, logs, audit data
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Google App Engine (Python 3.8) | User interface & parameter input |
| Serverless Compute | AWS Lambda | Lightweight Monte Carlo simulations |
| Heavy Compute | Amazon EC2 | Large-scale simulation workloads |
| Storage | Amazon S3 | Results, audit logs, input data |
| API Management | Amazon API Gateway | Routing, throttling, authentication |
| Framework | Flask + Gunicorn | REST API on EC2 and GAE |
| Data Source | Yahoo Finance (yfinance) | Live MSFT stock data (3 years) |
| Standard | NIST SP 800-145 | Cloud computing compliance framework |

---

## Features

- **Monte Carlo Simulation** - generates thousands of randomised return scenarios using historical mean and standard deviation
- **Value at Risk (VaR)** - calculates 95% and 99% VaR thresholds from simulated distributions
- **Trading Signal Detection** - identifies Three White Soldiers (Buy) and Three Black Crows (Sell) candlestick patterns
- **Profit/Loss Evaluation** - computes actual P&L over a configurable forward window
- **Hybrid Cloud** - routes low-intensity tasks to Lambda, high-intensity to EC2
- **NIST SP 800-145 Compliant** - follows cloud security and architecture standards

---

## Project Structure

```
monte-carlo-cloud-simulation/
├── src/
│   ├── lambda_function.py      # AWS Lambda handler - serverless simulations
│   ├── ec2.py                  # EC2 Flask API - heavy compute simulations
│   └── index.py                # Google App Engine frontend
├── config/
│   ├── app.yaml                # GAE deployment configuration
│   └── requirements.txt        # Python dependencies
├── docs/
│   └── Cloud_Computing_Report.docx
├── ARCHITECTURE.md
└── README.md
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/warmup` | Initialise EC2 instance |
| `/resources_ready` | Check if resources are available |
| `/analyse` | Run Monte Carlo simulation |
| `/get_sig_vars9599` | Get significant VaR 95/99 results |
| `/get_avg_vars9599` | Get average VaR values |
| `/get_sig_profit_loss` | Get significant profit/loss records |
| `/get_tot_profit_loss` | Get total profit/loss summary |
| `/get_chart_url` | Retrieve chart visualisation URL |
| `/get_time_cost` | Get execution time and cost metrics |
| `/get_audit` | Retrieve audit log |
| `/reset` | Reset simulation state |
| `/terminate` | Terminate EC2 resources |

---

## Simulation Parameters

| Parameter | Description |
|-----------|-------------|
| `minhistory` / `history_window` | Number of historical days for mean/std calculation |
| `shots` / `num_simulations` | Number of Monte Carlo simulation runs |
| `bs` / `signal_type` | 1 = Buy signal, 0 = Sell signal |
| `profit_loss_days` | Forward window (days) to evaluate actual P&L |

---

## Sample Results

| Compute | Simulations | History | Data Points | Signal | P&L Days | VaR 95% | VaR 99% | Cost ($) | Time (s) |
|---------|------------|---------|-------------|--------|-----------|---------|---------|----------|----------|
| Lambda | 1 | 250 | 600 | Buy | 2 | -0.0285 | -0.0408 | 0.0025 | 11.01 |
| Lambda | 3 | 67 | 800 | Sell | 5 | -0.0294 | -0.0418 | 0.0056 | 24.92 |
| EC2 | 2 | 198 | 400 | Sell | 4 | -0.0349 | -0.0492 | 0.0004 | 57.81 |
| EC2 | 4 | 78 | 700 | Buy | 6 | -0.0359 | -0.0438 | 0.0013 | 100.70 |

---

## Cost Analysis (1,200 Active Users)

| Service | Monthly Cost |
|---------|-------------|
| AWS Lambda | $11.78 |
| Amazon EC2 | $604.80 |
| Amazon S3 | $90.00 |
| AWS Network | $6.00 |
| **Total** | **$712.58** |

---

## Setup & Deployment

### Deploy to Google App Engine
```bash
pip install -r config/requirements.txt
gcloud app deploy config/app.yaml
```

### Deploy Lambda Function
1. Zip `src/lambda_function.py` with dependencies
2. Upload to AWS Lambda via console or CLI
3. Set handler to `lambda_function.lambda_handler`

### Run EC2 Flask API locally
```bash
pip install -r config/requirements.txt
python src/ec2.py
# API runs on http://0.0.0.0:80
```

---

## Academic Context

- **Institution:** University of Surrey
- **Programme:** MSc Data Science
- **Module:** Cloud Computing
- **Compliance Standard:** NIST SP 800-145
- **Author:** Jeganathan Duraisamy
