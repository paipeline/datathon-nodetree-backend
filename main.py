from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.api import router as api_v1_router

app = FastAPI(
    title="nodetree backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_v1_router,
    prefix="/api/v1",
    tags=["v1"]
)

@app.get("/")
async def root():
    return {"message": "backend for nodetree"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
