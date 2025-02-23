from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.api import router as api_v1_router
from mongodb_client import get_client, connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前连接数据库
    await connect_to_mongo()
    yield
    # 关闭时断开连接
    await close_mongo_connection()

app = FastAPI(
    title="nodetree backend",
    version="1.0.0",
    lifespan=lifespan
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

def get_db():
    return get_client()

@app.get("/db-test")
async def db():
    client = get_db()
    return {"message": "Connected to MongoDB"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
