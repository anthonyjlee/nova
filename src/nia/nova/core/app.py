"""Nova FastAPI application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .nova_endpoints import nova_router
from .auth import validate_api_key

# Create FastAPI app
app = FastAPI(
    title="Nova API",
    description="Nova API for agent orchestration",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(nova_router)

# Health check endpoint
@app.get("/api/status")
async def health_check(key: str = Depends(validate_api_key)):
    """Health check endpoint."""
    return {"status": "ok"}
