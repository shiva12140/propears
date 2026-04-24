from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from app.database import async_session_maker
from app.models import User
from app.config import settings
from fastapi import Request
from chromadb import AsyncHttpClient
from chromadb.api.models.Collection import Collection
from typing import Optional

security = HTTPBearer(auto_error=False)

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        token_query: Optional[str] = Query(None, alias="token"),
        db: AsyncSession = Depends(get_db)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None
    if credentials:
        token = credentials.credentials
    elif token_query:
        token = token_query
        
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    
    return user



async def get_chroma_client(request: Request) -> AsyncHttpClient:
    client = getattr(request.app.state, "chroma_client", None)
    if client is None:
        raise RuntimeError("ChromaDB client is not initialized in App State.")
    return client

def get_chroma_collection(request: Request) -> Collection:
    collection = getattr(request.app.state, "chroma_collection", None)
    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="ChromaDB is not available. The vector database failed to connect during startup. Notes and Quiz features require ChromaDB."
        )
    return collection