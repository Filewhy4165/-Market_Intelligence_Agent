# Autonomous Multi-Asset Market Intelligence Agent

A production-oriented MVP for multi-timeframe stock, forex, and futures research plus a separate crash/correction early-warning engine.

## What it does
- Analyzes hourly, daily, weekly, and long-term horizons independently.
- Produces LONG, SHORT, or WAIT scenarios with entry zone, stop, TP1-TP3, invalidation, confidence, and calculated risk/reward.
- Builds a crash-event catalog from index history and evaluates drawdowns, breadth proxies, volatility, trend, and macro/credit inputs.
- Separates **structural vulnerability** from **immediate downside pressure**.
- Uses time-aware walk-forward validation and reports false positives.
- Refuses false precision when data is missing or stale.
- Generates research output only. It does not place trades.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

The default provider is `demo`, so the interface runs without credentials using deterministic synthetic data clearly labeled as synthetic. For live use, set `DATA_PROVIDER=alpha_vantage` and add an API key. Futures-grade data should be connected through a properly licensed exchange/vendor feed.

## Architecture
- `app.py`: Streamlit UI
- `market_agent/data.py`: provider abstraction, freshness checks, synthetic/demo and Alpha Vantage adapters
- `market_agent/indicators.py`: technical calculations
- `market_agent/trade_engine.py`: independent horizon scenarios
- `market_agent/crash_engine.py`: event detection, factor construction, walk-forward risk model, analogs
- `market_agent/report.py`: unified report assembly
- `tests/`: smoke tests

## Important limitations
No model can reliably predict the exact date or size of a crash. This software estimates changing downside vulnerability from historical relationships. Historical analogs are not forecasts. Real deployment requires licensed, survivorship-bias-aware datasets, corporate-action handling, macro release vintages, and robust monitoring.
