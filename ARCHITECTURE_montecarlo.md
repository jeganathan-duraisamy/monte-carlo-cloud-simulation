# Architecture: Monte Carlo Cloud Simulation Platform

## Overview

This platform implements a hybrid cloud architecture spanning AWS and Google Cloud Platform, designed for executing Monte Carlo simulations on live stock market data. The system adheres to the NIST SP 800-145 cloud computing framework and routes workloads intelligently between serverless (Lambda) and dedicated compute (EC2) based on simulation complexity.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                         │
└─────────────────────────┬───────────────────────────────────┘
                          │  HTTP Request
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              GOOGLE APP ENGINE (GAE)                        │
│              index.py | Flask | Gunicorn                    │
│              Runtime: Python 3.8 | Standard Env             │
│              1 instance | 0.5GB RAM | 10GB disk             │
└─────────────────────────┬───────────────────────────────────┘
                          │  API calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              AMAZON API GATEWAY                             │
│  - Authenticates requests                                   │
│  - Throttles and rate-limits traffic                        │
│  - Routes to Lambda or EC2 based on workload type           │
└──────────┬──────────────────────────────┬───────────────────┘
           │ Low-intensity                │ High-intensity
           ▼                              ▼
┌─────────────────────┐      ┌────────────────────────────┐
│    AWS LAMBDA       │      │       AMAZON EC2            │
│  lambda_function.py │      │  ec2.py | Flask API         │
│  - Serverless       │      │  - Auto-scaling instances   │
│  - Pay-per-use      │      │  - Complex simulations      │
│  - Auto-scaling     │      │  - port 80, host 0.0.0.0    │
└─────────────────────┘      └────────────┬───────────────┘
           │                              │
           └──────────────┬───────────────┘
                          │  Store results
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    AMAZON S3                                │
│  - Simulation results                                       │
│  - Input data                                               │
│  - Audit logs                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Google App Engine — Frontend (`index.py`)

| Property | Value |
|----------|-------|
| Runtime | Python 3.8 (Standard) |
| Entry point | `gunicorn -t 0 -b :$PORT index:app` |
| Scaling | Manual (1 instance) |
| Resources | 1 CPU, 0.5GB RAM, 10GB disk |
| Config | `config/app.yaml` |

Hosts the user-facing Flask web application. Users input simulation parameters (history window, simulation count, signal type, P&L days) and receive VaR results and charts.

### AWS Lambda — Serverless Compute (`lambda_function.py`)

| Property | Value |
|----------|-------|
| Handler | `lambda_function.lambda_handler` |
| Trigger | API Gateway (low-intensity requests) |
| Scaling | Automatic (serverless) |
| Pricing | Pay-per-invocation |

Handles lighter Monte Carlo workloads. Fetches 3 years of MSFT data from Yahoo Finance, identifies Three White Soldiers / Three Black Crows signals, runs Gaussian simulations, and returns VaR 95/99 and P&L per signal date.

### Amazon EC2 — Heavy Compute (`ec2.py`)

| Property | Value |
|----------|-------|
| Framework | Flask REST API |
| Port | 80 |
| Scaling | Auto-scaling groups |
| Use case | Large simulation batches |

Handles computationally intensive Monte Carlo runs. Implements the same signal detection and simulation logic as Lambda but is optimised for larger `num_simulations` and `history_window` values.

### Amazon S3 — Storage

Stores simulation outputs, intermediate results, and audit logs. Object-based storage handles large datasets from high-volume simulations efficiently.

### Amazon API Gateway

Acts as the system's entry point — authenticates users, throttles traffic, and routes requests to Lambda or EC2 depending on workload classification.

---

## Monte Carlo Simulation Logic

```
1. Fetch 3 years of MSFT daily OHLCV data (Yahoo Finance)
        │
        ▼
2. Identify candlestick signals
   - Three White Soldiers → Buy signal
   - Three Black Crows    → Sell signal
        │
        ▼
3. For each signal date:
   a. Calculate mean and std of % returns over history_window days
   b. Generate `num_simulations` random values: gauss(mean, std)
   c. Sort descending
   d. Extract VaR 95% = value at 95th percentile
      Extract VaR 99% = value at 99th percentile
   e. Calculate actual P&L = Close[i + profit_loss_days] - Close[i]
        │
        ▼
4. Return list of {date, VaR95, VaR99, Profit/Loss}
```

---

## NIST SP 800-145 Compliance

| NIST Characteristic | Implementation |
|--------------------|----------------|
| On-demand self-service | Users trigger simulations independently via GAE UI |
| Broad network access | GAE accessible globally via internet |
| Resource pooling | Shared Lambda + EC2 infrastructure across users |
| Rapid elasticity | Lambda auto-scales; EC2 uses auto-scaling groups |
| Measured service | AWS pay-per-use billing; per-invocation Lambda cost tracking |
| PaaS model | GAE abstracts server management from developer |
| Hybrid deployment | Combined GCP (frontend) + AWS (compute/storage) |

---

## Design Decisions

1. **Lambda for light tasks, EC2 for heavy** — avoids cold-start penalties on large simulations while keeping costs low for simple requests
2. **GAE Standard environment** — chosen for zero server management and fast cold starts on the frontend
3. **Yahoo Finance (yfinance)** — free real-time data source; `pdr_override()` applied for pandas compatibility
4. **Gaussian simulation** — uses `random.gauss(mean, std)` to generate return distributions consistent with historical behaviour
5. **S3 for persistence** — simulation results stored for audit, replay, and cost tracking
