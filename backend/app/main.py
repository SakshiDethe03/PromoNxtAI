from fastapi import FastAPI
from app.api.campaigns import router as campaigns_router
from app.api.n8n_callback import router as n8n_callback_router
from app.config.settings import settings

app = FastAPI(
    title="PromoNxtAI API",
    description="AI-driven marketing and promotion engine for SMB shopkeepers",
    version="1.0.0",
)

app.include_router(campaigns_router)
app.include_router(n8n_callback_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "use_sample_data": settings.use_sample_data,
        "image_mock": settings.image_mock,
        "n8n_mock": settings.n8n_mock,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
