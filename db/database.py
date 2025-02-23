from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
logger.info(f"Using MongoDB URL: {MONGODB_URL}")

client: Optional[AsyncIOMotorClient] = None

async def connect_to_mongo():
    global client
    try:
        logger.info("Attempting to connect to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)

        await client.admin.command('ping')
     
        db = client['nodetree']
        await db.create_collection('nodes', check_exists=False)
        logger.info("Successfully connected to MongoDB and initialized collections")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

def get_client() -> AsyncIOMotorClient:
    if not client:
        raise RuntimeError("MongoDB client not initialized. Call connect_to_mongo() first.")
    return client

async def close_mongo_connection():
    global client
    if client:
        logger.info("Closing MongoDB connection...")
        client.close()
        client = None
        logger.info("MongoDB connection closed") 