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
    
    # --- RETRY LOGIC FOR CHROMA ---
    import asyncio
    client = None
    retries = 5
    for i in range(retries):
        try:
            client = await chromadb.AsyncHttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                ssl=settings.chroma_ssl
            )
            collection = await client.get_or_create_collection(settings.chroma_collection)
            app.state.chroma_client = client
            app.state.chroma_collection = collection
            
            count = await collection.count()
            print(f"✅ Successfully loaded collection '{settings.chroma_collection}' with {count} documents.")
            break
        except Exception as e:
            if i < retries - 1:
                wait_time = (i + 1) * 3
                print(f"⚠️ ChromaDB connection failed (Attempt {i+1}/{retries}). Retrying in {wait_time}s... Error: {e}")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Failed to load ChromaDB collection after {retries} attempts: {e}")
                # We don't raise here so the server can at least start, though notes will fail until fixed
    # -------------------------------


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