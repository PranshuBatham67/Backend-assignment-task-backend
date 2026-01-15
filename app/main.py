from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import time
import logging
import os
from .config import settings
from .core.rate_limiter import limiter
from .core.exceptions import CustomHTTPException
from .api.v1 import api_router as v1_router
from .api.v2 import api_router as v2_router
from .database import engine, Base

# Set up logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A scalable REST API with authentication, RBAC, and advanced backend features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(CustomHTTPException)
async def custom_exception_handler(request: Request, exc: CustomHTTPException):
    """Handle custom exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with better formatting"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors}
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.3f}s"
        )
        
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise

# Include API routers with versioning
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
app.include_router(v2_router, prefix=settings.API_V2_PREFIX)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    Useful for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_versions": ["v1", "v2"]
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to the Backend Assignment API",
        "documentation": "/docs",
        "health_check": "/health",
        "api_v1": settings.API_V1_PREFIX,
        "api_v2": settings.API_V2_PREFIX
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Run on application startup.
    Database tables will be created via Alembic migrations in production.
    """
    logger.info("Application starting up...")
    logger.info(f"API v1 prefix: {settings.API_V1_PREFIX}")
    logger.info(f"API v2 prefix: {settings.API_V2_PREFIX}")
    
    # In development, create tables if they don't exist
    # In production, use Alembic migrations instead
    if settings.DEBUG:
        logger.info("Creating database tables (development mode)...")
        Base.metadata.create_all(bind=engine)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
