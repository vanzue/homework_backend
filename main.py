import logging
from fastapi import FastAPI
from enterprise_routes import router as enterprise_router
from refugee_routes import router as refugee_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(enterprise_router)
app.include_router(refugee_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    logger.info("Debug: Entering main block")
    try:
        import uvicorn
        logger.info("Debug: About to run uvicorn")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    logger.info("Debug: After uvicorn.run (this line should not be reached normally)")