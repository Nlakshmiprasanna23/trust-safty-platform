# AI-Powered Multi-Agent Trust & Safety Platform

Fraud detection, review-manipulation defense and counterfeit detection for online marketplaces.
Three cooperating AI agents behind a deterministic orchestrator, an immutable audit trail, and an
enterprise React console.

## Quick start (Windows)

    start_all.bat

Manually:

    cd backend && python -m venv .venv && .venv\Scripts\activate
    pip install -r requirements.txt
    python -m app.seed
    uvicorn app.main:app --reload --port 8000     # http://127.0.0.1:8000/docs

    cd frontend && npm install && npm run dev     # http://localhost:5173

Demo logins: `admin@trustsafety.local / Admin@123`, `analyst@trustsafety.local / Analyst@123`

## Agents
1. **Risk Scoring Agent** — COD abuse, return fraud, account takeover. Explainable rule engine plus
   optional gradient-boosted model; every score ships feature contributions.
2. **Authenticity Agent** — counterfeit detection from image heuristics, claim text and price deviation.
3. **Review Moderation Agent** — fake reviews via TF-IDF similarity, sentiment and burst analysis, plus
   graph-based reviewer-ring discovery.

The orchestrator routes each request, applies deterministic policy guardrails (an agent can never
auto-ban), and writes an immutable audit record with model + policy version.

## ML training

    python ml/training/train_risk_model.py
    python ml/training/train_review_model.py
    python ml/training/train_authenticity_model.py
    python ml/evaluation/evaluate_models.py

Scripts run on synthetic data out of the box and accept `--data <csv>` for real datasets
(see `docs/dataset-guide.md`).

## Tests

    cd backend && pytest        # 14 passing

## Honesty note
Data shipped in the SQLite seed is clearly labelled **DEMO DATA** in the UI. Image forensics uses a
deterministic heuristic pipeline, not a trained vision model, until a licensed dataset is supplied.
