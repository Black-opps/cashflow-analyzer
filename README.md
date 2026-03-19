# 📊 Cashflow Analyzer Microservice

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=for-the-badge&logo=python)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-24.0-2496ED.svg?style=for-the-badge&logo=docker)](https://docker.com)
[![Kafka](https://img.shields.io/badge/Kafka-Ready-231F20.svg?style=for-the-badge&logo=apache-kafka)](https://kafka.apache.org)
[![Redis](https://img.shields.io/badge/Redis-Ready-DC382D.svg?style=for-the-badge&logo=redis)](https://redis.io)

A production-ready microservice for real-time cashflow analysis and pattern recognition, designed for the M-PESA SaaS platform.

## 📋 **Overview**

The Cashflow Analyzer Microservice transforms raw transaction data into actionable business intelligence. It provides REST APIs for analyzing cashflow trends, detecting patterns, and generating exportable reports.

### ✨ **Key Features**

- **Real-time Cashflow Analysis**: Analyze inflows, outflows, and net cashflow over custom periods
- **Time-series Aggregation**: Group by day, week, or month for trend analysis
- **Pattern Recognition**: Detect seasonal patterns, trends, anomalies, and recurring transactions
- **Multi-format Exports**: Generate reports in CSV and JSON formats
- **Tenant Isolation**: Built for multi-tenancy with tenant_id scoping
- **Event-Ready**: Kafka integration for consuming transaction streams
- **Production Ready**: Comprehensive logging, health checks, and metrics

## 🏗️ **Architecture**

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ API Layer │────▶│ Service Layer │────▶│ Data Layer │
│ (FastAPI) │ │ (Analysis) │ │ (Redis/DB) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│ │ │
▼ ▼ ▼
┌─────────────────────────────────────────────────────────────┐
│ Event Bus (Kafka) │
└─────────────────────────────────────────────────────────────┘




## 📊 **API Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/cashflow/analyze` | Custom cashflow analysis with date range |
| `GET` | `/api/v1/cashflow/summary/{tenant_id}` | Quick summary for last N days |
| `POST` | `/api/v1/cashflow/patterns` | Detect patterns in cashflow data |
| `GET` | `/api/v1/cashflow/export/{report_id}` | Export report in CSV/JSON |
| `GET` | `/health` | Service health check |
| `GET` | `/` | Service information |

## 🚀 **Quick Start**

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for containerized run)
- Redis (optional, for caching)
- Kafka (optional, for event streaming)

### Local Development

1. **Clone and navigate**
```bash
git clone https://github.com/Black-opps/cashflow-analyzer.git
cd cashflow-analyzer
