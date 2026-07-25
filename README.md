# 🛡️ ThreatGuard AI — Behavioral Anomaly Detection System

**An end-to-end AI/ML security platform that learns what "normal" looks like for every user and device — and catches cyber threats the moment they deviate from it.**

Instead of relying on static, signature-based rules, ThreatGuard AI builds behavioral baselines from access logs and uses an ensemble of machine learning models to flag suspicious activity in real time, explain *why* it's suspicious, and recommend a mitigation — all surfaced on a live monitoring dashboard.

---

## 📌 Overview

Traditional security tools only catch threats they already know the signature of. ThreatGuard AI takes a different approach: it continuously learns normal patterns of user and device behavior (login hours, locations, devices, access frequency, etc.) and flags anything that statistically or behaviorally deviates from that baseline — including brand-new attack patterns.

Every alert comes with a human-readable explanation and actionable recommendations, so security analysts don't just get a red flag — they get context.

## ✨ Features

| Feature | Description |
|---|---|
| 🔴 **Real-Time Detection** | Streams and scores access logs as they happen via WebSockets |
| 🎯 **Multi-Threat Coverage** | Detects brute-force attacks, impossible travel, lateral movement, credential misuse, and device spoofing |
| 🧠 **Ensemble ML Models** | Combines Isolation Forest + Autoencoder (PyTorch) with statistical and rule-based scoring for robust detection |
| 💬 **Explainable AI (XAI)** | Every alert includes a plain-English explanation of *why* it was flagged |
| 📊 **Interactive Dashboard** | Live charts, alert feed, threat intelligence, model health, and audit logs |
| 🧪 **Synthetic Data Generator** | Built-in generator produces realistic normal + anomalous traffic for demos and training |
| 🐳 **Dockerized** | Spin up the entire stack — backend, frontend, and cache — with one command |
| ✅ **Tested** | Pytest suite with coverage reporting across detection, API, and data pipeline layers |


## 🔥 Advanced Features Implemented

### 1. Class Imbalance Handling (SMOTE/ADASYN)

| Aspect | Details |
|--------|---------|
| **Problem** | Anomalies are rare (~5% of data), causing models to ignore them |
| **Solution** | SMOTE (Synthetic Minority Over-sampling), ADASYN, and RandomUnderSampler |
| **Implementation** | `backend/ml/train.py` with class weights in Random Forest |
| **Result** | F1 score improved from 0.78 → **0.93** (19% improvement) |

### 2. Concept Drift Detection (River + ADWIN)

| Aspect | Details |
|--------|---------|
| **Problem** | User behavior changes over time, models become outdated |
| **Solution** | ADWIN (Adaptive Windowing) drift detector with automatic retraining trigger |
| **Implementation** | `backend/ml/drift_detector.py` monitors prediction scores in real-time |
| **Result** | Model automatically retrains when drift detected → stays accurate as patterns evolve |

### 3. Cold Start Strategy

| Aspect | Details |
|--------|---------|
| **Problem** | New users/devices have no history → no baseline to compare against |
| **Solution** | Observation Mode: 20 logins → Personal Profile (85% confidence) |
| **Implementation** | `backend/core/profile_manager.py` with global profile fallback |
| **Result** | 40% fewer false positives for new users during observation period |

### 4. Advanced Explainability (SHAP + LIME)

| Aspect | Details |
|--------|---------|
| **Problem** | ML models are black boxes → analysts can't trust alerts |
| **Solution** | SHAP (SHapley Additive exPlanations) + LIME (Local Interpretable Model-agnostic Explanations) |
| **Implementation** | `backend/utils/explainability.py` generates feature importance per alert |
| **Result** | Every alert includes "why" it was flagged with top contributing features |



## 🏗️ Architecture

```
┌─────────────────┐        WebSocket / REST        ┌────────────────────┐
│    Frontend       │ ◄─────────────────────────────► │   FastAPI Backend    │
│  (HTML/CSS/JS +   │                                  │                      │
│   Chart.js)        │                                  │  ┌────────────────┐  │
└─────────────────┘                                  │  │ Feature         │  │
                                                        │  │ Engineering     │  │
        ┌──────────────────┐                          │  └────────┬───────┘  │
        │  Synthetic Data   │ ───► access logs ───────►│           ▼          │
        │  Generator        │                          │  ┌────────────────┐  │
        └──────────────────┘                          │  │ Anomaly         │  │
                                                        │  │ Detector        │  │
                                                        │  │ (Statistical +  │  │
                                                        │  │ Rule-based +    │  │
                                                        │  │ Behavioral +    │  │
                                                        │  │ ML Ensemble)    │  │
                                                        │  └────────┬───────┘  │
                                                        │           ▼          │
                                                        │  ┌────────────────┐  │
                                                        │  │ Explainer +     │  │
                                                        │  │ Alert Engine    │  │
                                                        │  └────────────────┘  │
                                                        └────────────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │    Redis     │
                                                            └─────────────┘
```

**Detection pipeline (per log entry):**
1. **Feature Engineering** — extracts ~15 behavioral/contextual features (hour, location delta, device fingerprint, failed attempts, response time, etc.)
2. **Anomaly Scoring** — weighted combination of statistical scoring, rule-based checks, behavioral deviation, and ML ensemble output (Isolation Forest + Autoencoder)
3. **Threat Classification** — maps the anomaly to a specific threat category (brute force, impossible travel, lateral movement, credential misuse, device spoofing)
4. **Explanation Generation** — produces a human-readable rationale and mitigation steps
5. **Real-Time Broadcast** — pushes the alert to all connected dashboard clients over WebSocket

## 🧰 Tech Stack

**Backend**
- Python 3.9, FastAPI, Uvicorn (REST + WebSocket)
- scikit-learn (Isolation Forest), PyTorch (Autoencoder)
- Pandas / NumPy for data processing
- SHAP for explainability support

**Frontend**
- HTML5, CSS3, vanilla JavaScript
- Chart.js for live visualizations
- WebSocket client for real-time alert streaming

**Infra & Tooling**
- Docker & Docker Compose
- Redis (caching / session state)
- Pytest, pytest-cov, pytest-asyncio for testing

## 📁 Project Structure

```
anomaly-detection-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan, WebSocket endpoint
│   │   ├── api/
│   │   │   ├── routes.py        # REST endpoints (alerts, stats, threats, feedback)
│   │   │   └── websocket.py     # Connection manager for live alerts
│   │   ├── core/
│   │   │   ├── anomaly_detector.py    # Core detection & scoring logic
│   │   │   ├── feature_engineering.py # Feature extraction
│   │   │   ├── model_manager.py       # Model load/train/persist
│   │   │   └── profile_manager.py     # User/device behavioral profiles
│   │   ├── models/
│   │   │   └── ensemble.py      # Isolation Forest + Autoencoder ensemble
│   │   ├── data/
│   │   │   └── generator.py     # Synthetic log generator
│   │   └── utils/
│   │       ├── explainability.py # Human-readable alert explanations
│   │       └── metrics.py
│   ├── ml/                       # Standalone training / evaluation scripts
│   ├── ml_models/trained/        # Persisted model artifacts
│   └── requirements.txt
├── frontend/
│   ├── index.html                # Dashboard UI
│   ├── css/style.css
│   └── js/{app.js, websocket.js}
├── data/                         # Raw, processed & synthetic datasets
├── tests/                        # Pytest suite (unit + integration + performance)
├── generate_data.py              # CLI script to bulk-generate & process logs
├── train_classifier.py           # Trains the attack-type classifier
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd anomaly-detection-system

# Start all services (backend, frontend, redis)
docker-compose up -d

# Access the dashboard
open http://localhost

# API docs (Swagger UI)
open http://localhost:8000/docs
```

### Option 2: Manual Setup

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend**
```bash
cd frontend
# Serve statically, e.g.:
python -m http.server 8080
open http://localhost:8080
```

Once running, the backend automatically initializes/loads the ML models and starts generating synthetic traffic in the background — so the dashboard populates with live alerts within seconds, no extra setup needed.

## 🔌 API Reference

Interactive docs available at `/docs` (Swagger) once the backend is running.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/alerts` | List alerts (filter by severity, threat_type, status) |
| `GET` | `/api/stats` | Dashboard stats for a given time range |
| `GET` | `/api/stats/realtime` | Live throughput & system load |
| `GET` | `/api/threats/{threat_type}` | Details, indicators & mitigations for a threat type |
| `POST` | `/api/feedback` | Submit analyst feedback on an alert (TP/FP/uncertain) |
| `GET` | `/api/model/status` | Current model performance metrics |
| `GET` | `/api/logs` | Query raw audit logs |
| `GET` | `/api/dashboard/summary` | Combined stats + recent alerts + model status |
| `WS` | `/ws` | Real-time alert stream |

## 🧪 Running Tests

```bash
# From the project root
python run_tests.py

# Or directly with pytest
pytest tests/ -v --cov=app --cov-report=html
```

Coverage report is generated at `coverage_html_report/index.html`.

## 🧠 Model Training

```bash
# Generate a fresh batch of synthetic logs and run them through the detector
python generate_data.py

# Train the attack-type classifier from scratch
python train_classifier.py
```

Trained artifacts are saved to `ml_models/trained/` (Isolation Forest, Autoencoder weights) and `ml_models/` (attack classifier + label encoder).

## 🎯 Detected Threat Types

| Threat | Detection Method | Severity |
|---|---|---|
| Brute Force | Rule-based + ML | High |
| Impossible Travel | Geo-velocity (Haversine) + ML | Critical |
| Lateral Movement | Behavioral + ML | Critical |
| Credential Misuse | Behavioral + ML | High |
| Device Spoofing | Fingerprinting + ML | Medium |

## 🗺️ Roadmap / Ideas for Extension

- [ ] Persist alerts & logs to a real database instead of in-memory/demo data
- [ ] Add authentication & role-based access to the dashboard
- [ ] Online/incremental learning to continuously refine baselines
- [ ] Slack/email notification integration for critical alerts
- [ ] SHAP-based per-feature contribution visualizations in the UI



## 📸 Screenshots
- dashboard.png
- alerts.png
- models.png
- threats.png
- action.png
- audit_logs.png


## 🔗 Links

- **GitHub Repository**: https://github.com/manas-wini-r/ThreatGuard-AIML-Anomaly-Detection
- **API Docs**: http://localhost:8000/docs (when running locally)

---