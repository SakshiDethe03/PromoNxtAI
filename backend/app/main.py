from fastapi import FastAPI

app = FastAPI(
    title="PromoNxtAI API",
    description="AI-driven marketing and promotion engine",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Welcome to PromoNxtAI API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8000, reload=True)
