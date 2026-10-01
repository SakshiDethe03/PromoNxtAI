# PromoNxtAI Backend

Backend service for PromoNxtAI powering AI agents, workflow graphs, and marketing promotion tools.

## Live Demo Launcher

Run the automated demo script to start the server in demo mode (`USE_SAMPLE_DATA=true, IMAGE_MOCK=false, N8N_MOCK=true`) and print step-by-step interactive demo commands:

```powershell
# From project root or backend directory:
.\scripts\run_demo.ps1
```

---

## Setup & Running

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

---

## Testing & Benchmarking

```bash
# Run complete test suite (63+ tests)
pytest -v

# Run 40-scenario evaluation benchmark
python scripts/run_evaluation.py
```

---

## Build Order
```
1. Project setup
       ↓
2. Python venv + dependencies
       ↓
3. Configuration + .env
       ↓
4. Data models / schemas
       ↓
5. LangGraph State
       ↓
6. First agent → Product Analyzer
       ↓
7. Product Recommendation
       ↓
8. Campaign Strategy
       ↓
9. Content Generation
       ↓
10. Claim Validation
       ↓
11. Human Approval
       ↓
12. FastAPI endpoints
       ↓
13. Frontend integration
       ↓
14. Friend's Instagram module
       ↓
15. End-to-end testing
       ↓
16. Deployment
```