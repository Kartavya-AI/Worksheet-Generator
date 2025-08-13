import os
import logging
import traceback
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import structlog

from src.worksheet_generator.crew import get_worksheet_crew

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Environment validation
REQUIRED_ENV_VARS = ["GEMINI_API_KEY"]
OPTIONAL_ENV_VARS = ["PORT", "ENVIRONMENT", "LOG_LEVEL"]

def validate_environment():
    """Validate required environment variables"""
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    logger.info("Environment validation successful")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    try:
        # Startup
        logger.info("Starting Worksheet Generator API")
        validate_environment()
        logger.info("API startup complete")
        yield
    except Exception as e:
        logger.error("Startup failed", error=str(e), traceback=traceback.format_exc())
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Worksheet Generator API")

# FastAPI application with lifespan management
app = FastAPI(
    title="Worksheet Generator API",
    description="A production-ready AI-powered worksheet generation service using CrewAI and Google Gemini",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
    lifespan=lifespan
)

# Security and CORS middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Request/Response Models
class WorksheetRequest(BaseModel):
    """Request model for worksheet generation"""
    topic: str = Field(
        ..., 
        min_length=2, 
        max_length=200,
        description="The specific topic or chapter for the worksheet",
        example="Electromagnetic Induction"
    )
    grade: str = Field(
        ..., 
        min_length=1, 
        max_length=10,
        description="The grade/class level",
        example="12"
    )
    num_questions: int = Field(
        default=10, 
        ge=5, 
        le=20,
        description="Number of questions to generate (5-20)",
        example=10
    )
    board: str = Field(
        default="CBSE",
        min_length=2,
        max_length=20,
        description="School board",
        example="CBSE"
    )
    subject: str = Field(
        default="Science",
        min_length=2,
        max_length=50,
        description="Subject name",
        example="Physics"
    )
    stream: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Stream for higher classes (optional)",
        example="Science"
    )

    @validator('topic', 'grade', 'board', 'subject')
    def validate_strings(cls, v):
        if v:
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or just whitespace")
        return v

    @validator('stream')
    def validate_stream(cls, v):
        if v:
            v = v.strip()
            if not v:
                return None
        return v

class WorksheetResponse(BaseModel):
    """Response model for successful worksheet generation"""
    success: bool = Field(default=True)
    worksheet: str = Field(..., description="Generated worksheet content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(default=None)

# Custom exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.error("Validation error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=str(exc),
            error_code="VALIDATION_ERROR",
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error("HTTP error", 
                status_code=exc.status_code, 
                error=exc.detail, 
                path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code="HTTP_ERROR",
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unexpected error", 
                error=str(exc), 
                traceback=traceback.format_exc(),
                path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="An internal server error occurred. Please try again later.",
            error_code="INTERNAL_ERROR",
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    request_id = f"req_{int(start_time.timestamp() * 1000)}"
    request.state.request_id = request_id
    
    logger.info("Request started", 
               method=request.method, 
               path=request.url.path, 
               request_id=request_id)
    
    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("Request completed",
                   method=request.method,
                   path=request.url.path,
                   status_code=response.status_code,
                   duration_seconds=duration,
                   request_id=request_id)
        
        response.headers["X-Request-ID"] = request_id
        return response
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error("Request failed",
                    method=request.method,
                    path=request.url.path,
                    error=str(e),
                    duration_seconds=duration,
                    request_id=request_id)
        raise

# Health check endpoints
@app.get("/", 
         summary="Root endpoint",
         description="Basic API status check")
async def read_root():
    """Root endpoint returning API status"""
    return {
        "status": "healthy",
        "service": "Worksheet Generator API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", 
         summary="Detailed health check",
         description="Comprehensive health check including environment validation")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Validate environment
        validate_environment()
        
        health_status = {
            "status": "healthy",
            "service": "Worksheet Generator API",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "gemini_api_configured": bool(os.environ.get("GEMINI_API_KEY")),
                "environment": os.environ.get("ENVIRONMENT", "development"),
                "log_level": os.environ.get("LOG_LEVEL", "INFO")
            },
            "checks": {
                "environment_vars": "ok",
                "crew_initialization": "pending"  # Will be validated on first request
            }
        }
        
        logger.info("Health check passed")
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/ready",
         summary="Readiness check",
         description="Kubernetes/Cloud Run readiness probe")
async def readiness_check():
    """Simple readiness check for container orchestration"""
    try:
        validate_environment()
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

# Main worksheet generation endpoint
@app.post("/generate-worksheet/",
          response_model=WorksheetResponse,
          responses={
              400: {"model": ErrorResponse, "description": "Bad Request"},
              500: {"model": ErrorResponse, "description": "Internal Server Error"},
              503: {"model": ErrorResponse, "description": "Service Unavailable"}
          },
          summary="Generate educational worksheet",
          description="Generate an AI-powered educational worksheet with multiple choice questions")
async def generate_worksheet(request: WorksheetRequest):
    """
    Generate an educational worksheet based on the provided parameters.
    
    This endpoint uses CrewAI with Google Gemini to generate contextually appropriate
    multiple choice questions for the specified topic and grade level.
    """
    request_start = datetime.now()
    
    logger.info("Worksheet generation started", 
               topic=request.topic, 
               grade=request.grade,
               num_questions=request.num_questions,
               board=request.board,
               subject=request.subject)
    
    try:
        # Validate API key availability
        if not os.environ.get("GEMINI_API_KEY"):
            logger.error("GEMINI_API_KEY not configured")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not properly configured. Please contact administrator."
            )

        # Prepare inputs for the crew
        crew_inputs = {
            'topic': request.topic,
            'grade': request.grade,
            'num_questions': request.num_questions,
            'board': request.board,
            'class_level': request.grade,
            'subject': request.subject,
            'stream': request.stream
        }

        logger.info("Initializing CrewAI", inputs=crew_inputs)
        
        # Get the crew and execute
        try:
            crew = get_worksheet_crew()
            logger.info("Crew initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize crew", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service initialization failed. Please try again later."
            )

        # Execute the crew
        logger.info("Starting worksheet generation process")
        try:
            result = crew.kickoff(inputs=crew_inputs)
            worksheet_content = str(result)
        except Exception as e:
            logger.error("Crew execution failed", error=str(e), traceback=traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Worksheet generation failed. Please try again with different parameters."
            )

        # Validate result
        if not worksheet_content or len(worksheet_content.strip()) < 100:
            logger.warning("Generated worksheet appears to be too short", length=len(worksheet_content))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generated worksheet appears to be incomplete. Please try again."
            )

        generation_time = (datetime.now() - request_start).total_seconds()
        
        logger.info("Worksheet generated successfully", 
                   generation_time_seconds=generation_time,
                   content_length=len(worksheet_content))

        response = WorksheetResponse(
            worksheet=worksheet_content,
            metadata={
                "topic": request.topic,
                "grade": request.grade,
                "num_questions": request.num_questions,
                "board": request.board,
                "subject": request.subject,
                "stream": request.stream,
                "generation_time_seconds": round(generation_time, 2),
                "content_length": len(worksheet_content)
            }
        )

        return response

    except HTTPException:
        raise
    
    except Exception as e:
        generation_time = (datetime.now() - request_start).total_seconds()
        logger.error("Unexpected error in worksheet generation",
                    error=str(e),
                    traceback=traceback.format_exc(),
                    generation_time_seconds=generation_time)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during worksheet generation. Please try again later."
        )

@app.get("/api-info",
         summary="API Information",
         description="Get detailed API information and supported parameters")
async def api_info():
    """Get API information and supported parameters"""
    return {
        "api": {
            "name": "Worksheet Generator API",
            "version": "2.0.0",
            "description": "AI-powered educational worksheet generation service"
        },
        "supported_parameters": {
            "boards": ["CBSE", "ICSE", "State Boards"],
            "grades": ["1-12"],
            "subjects": ["Mathematics", "Science", "Physics", "Chemistry", "Biology", "English", "History", "Geography"],
            "streams": ["Science", "Commerce", "Arts"],
            "question_count": {"min": 5, "max": 20}
        },
        "features": [
            "Multiple choice questions with 4 options",
            "Answer keys provided",
            "Grade-appropriate content",
            "Curriculum-aligned questions",
            "Professional formatting"
        ],
        "powered_by": "CrewAI + Google Gemini"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    log_level = os.environ.get("LOG_LEVEL", "info").lower()
    logger.info("Starting development server", port=port, log_level=log_level)
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=False  # Disabled for production
    )