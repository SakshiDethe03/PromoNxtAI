# PromoNxtAI Backend

Backend service for PromoNxtAI powering AI agents, workflow graphs, and marketing promotion tools.

## Setup & Running

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m app.main
# or
uvicorn app.main:app --reload
```

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