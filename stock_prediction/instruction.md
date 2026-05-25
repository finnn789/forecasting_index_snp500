# AI Refactoring & Re-Architecture Prompt (Optimized for Opus + Ruflo)

You are a senior AI software architect and ML systems engineer.

Your task is NOT to rebuild my project from scratch.

Your task is to:

* analyze the existing project,
* perform incremental refactoring,
* improve architecture quality,
* modularize the system,
* and redesign the codebase into a clean Layered Architecture.

The project already exists and partially works.

==================================================================
PRIMARY GOAL
============

Refactor the existing AI stock forecasting system into:

* clean Layered Architecture,
* modular ML pipeline,
* scalable FastAPI backend,
* reusable PyTorch training pipeline,
* realtime process monitoring system,
* and maintainable production-style codebase.

==================================================================
IMPORTANT CONSTRAINTS
=====================

DO NOT:

* rewrite the entire project,
* regenerate unnecessary files,
* duplicate existing working logic,
* change business logic unnecessarily,
* create placeholder code,
* generate excessive explanations,
* overengineer abstractions,
* create unused classes/modules,
* introduce microservices,
* use Docker/Kubernetes unless requested,
* generate frontend code unless requested,
* generate full datasets,
* create fake implementations,
* modify working APIs unless necessary,
* add unnecessary dependencies,
* produce verbose documentation,
* output long theoretical explanations.

ONLY:

* refactor incrementally,
* improve maintainability,
* improve readability,
* improve modularity,
* preserve compatibility when possible,
* preserve existing workflows,
* isolate responsibilities properly,
* minimize token usage,
* focus on actionable architecture decisions.

==================================================================
PROJECT CONTEXT
===============

Tech Stack:

* FastAPI
* PyTorch
* Pandas
* Scikit-learn
* Local FinBERT
* Swagger/OpenAPI

Project Features:

* Financial sentiment analysis
* Stock preprocessing
* LSTM forecasting
* API endpoints
* Realtime process monitoring

Current Problems:

* mixed responsibilities,
* fat API routes,
* preprocessing tightly coupled,
* ML pipeline not modular,
* poor folder structure,
* weak separation of concerns,
* difficult maintenance,
* realtime progress system incomplete.

==================================================================
REFactoring TARGET
==================

Refactor into Layered Architecture:

1. Presentation Layer
2. API Layer
3. Service Layer
4. Domain Layer
5. Repository Layer
6. ML Pipeline Layer
7. Infrastructure Layer

Apply:

* SOLID principles,
* clean code,
* separation of concerns,
* async-first design,
* reusable services,
* dependency injection where useful.

==================================================================
WORKFLOW REQUIREMENTS
=====================

1. SENTIMENT ANALYSIS PIPELINE

---

Input:
data/raw/news/sp500_headlines_2008_2024.csv

Model:
models/finbert/models--ProsusAI--finbert

Requirements:

* local FinBERT inference,
* batch processing,
* GPU support if CUDA available,
* async processing,
* realtime progress reporting,
* remove "CP" column,
* filter:
  2018-01-02 → 2024-03-04

Output columns:

* Date
* Sentiment_Score_Mean
* Sentiment_Score_Positive
* Sentiment_Score_Negative
* Sentiment_Label

Output path:
data/processed/sentiment/

Required APIs:

* start processing,
* process status,
* realtime logs stream,
* download result.

==================================================================

2. STOCK PREPROCESSING PIPELINE

---

Input:
data/raw/stocks/GSPC_2018_2024.csv

Requirements:

* missing value handling,
* feature engineering,
* technical indicators,
* merge with sentiment dataset by Date,
* reusable transformers,
* modular preprocessing,
* validation pipeline.

Suggested Features:

* OHLCV,
* RSI,
* MACD,
* Moving Average,
* Sentiment features.

==================================================================

3. NORMALIZATION & FEATURE PIPELINE

---

Requirements:

* MinMaxScaler,
* train/test split for time-series,
* sliding window generation,
* configurable sequence length,
* prevent data leakage,
* save scaler artifacts.

==================================================================

4. LSTM TRAINING PIPELINE

---

Framework:
PyTorch

Requirements:

* modular training engine,
* configurable hyperparameters,
* early stopping,
* checkpoint manager,
* metrics tracking,
* GPU support,
* realtime epoch streaming,
* save best model.

Metrics:

* RMSE,
* MAE,
* MAPE.

==================================================================

5. REALTIME PROCESS MONITORING

---

Every long-running process must support:

* realtime logs,
* progress percentage,
* current stage,
* streaming updates.

Use:

* WebSocket OR SSE.

Frontend behavior should resemble:

* terminal stream,
* live training logs,
* live preprocessing status.

==================================================================
API REFACTORING
===============

Refactor FastAPI into:

* thin routers,
* service-based logic,
* centralized exception handling,
* DTO/Pydantic schemas,
* async endpoints,
* Swagger-compatible structure.

==================================================================
EXPECTED OUTPUT FORMAT
======================

Provide ONLY:

1. recommended architecture changes,
2. folder structure,
3. service responsibilities,
4. pipeline separation strategy,
5. API restructuring strategy,
6. realtime monitoring architecture,
7. refactoring priorities,
8. minimal code examples only when necessary.

DO NOT:

* generate full implementations unless requested,
* generate long tutorials,
* explain basic concepts,
* output repeated information,
* generate unnecessary boilerplate.

Focus on:

* architecture quality,
* maintainability,
* scalability,
* clean separation,
* production-ready organization,
* efficient token usage.
