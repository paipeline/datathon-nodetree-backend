from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

client: Optional[AsyncIOMotorClient] = None

async def connect_to_mongo():
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        await client.admin.command('ping')
        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

def get_client() -> AsyncIOMotorClient:
    if not client:
        raise RuntimeError("MongoDB client not initialized. Call connect_to_mongo() first.")
    return client 