import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database.db import connect_and_sync
from routes.auth_routes import router as auth_router
from middleware.auth_middleware import require_auth

# Load environment variables
load_dotenv()

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_and_sync()
        print(f"✓ API starting on port {os.getenv('PORT', '8000')} [{os.getenv('NODE_ENV', 'dev')}]")
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        raise
    
    yield
    
    # Shutdown
    print("✓ API shutting down")


# Create FastAPI app
app = FastAPI(
    title="Android Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0"
    }

# Auth routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Protected example endpoint
@app.get("/me")
async def get_me(user: dict = Depends(require_auth)):
    return {
        "userId": user["userId"],
        "correo": user["correo"],
        "nombre": user["nombre"]
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Enable auto-reload for development
    )
