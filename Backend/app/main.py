from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from app.config import settings
from app.database import engine, Base
from app.api.v1.api import api_router
import chromadb
from chromadb.api.models.Collection import Collection
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    print("🏗️ Server starting:", datetime.now())
    print("🔧 Creating tables if they don't exist...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    client = await chromadb.AsyncHttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        ssl=settings.chroma_ssl
    )
    app.state.chroma_client = client

    try:
        collection: Collection = await client.get_or_create_collection(settings.chroma_collection)
        app.state.chroma_collection = collection

        count = await collection.count()
        print(f"Successfully loaded collection '{settings.chroma_collection}' with {count} documents.")
    except Exception as e:
        print(f"Failed to load ChromaDB collection: {e}")

    print("✅ Tables ready!")
    yield
    print("🧹 Server shutting down:", datetime.now())


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION
    }