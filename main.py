from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.database import connect_to_mongo, close_mongo_connection

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

# 先设置中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 然后导入和注册路由
from api.v1.api import router as api_v1_router
from api.v2.api import router as api_v2_router

app.include_router(
    api_v1_router,
    prefix="/api/v1",
    tags=["v1"]
)

app.include_router(
    api_v2_router,
    prefix="/api/v2",
    tags=["v2"]
)

@app.get("/")
async def root():
    return {"message": "backend for nodetree"}

@app.get("/db-test")
async def db():
    client = get_client()
    return {"message": "Connected to MongoDB"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
