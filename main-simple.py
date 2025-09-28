"""
SRM Guide Bot - Simplified FastAPI Backend
Main application entry point - No complex dependencies
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="SRM Guide Bot API",
        description="Intelligent AI Assistant for SRM University - Simplified Version",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # CORS middleware - Allow your frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:4173", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        allow_origin_regex=None,
    )
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "SRM Guide Bot API",
            "version": "2.0.0",
            "environment": "development"
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "Welcome to SRM Guide Bot API",
            "version": "2.0.0",
            "description": "Intelligent AI Assistant for SRM University",
            "docs": "/api/docs",
            "health": "/health"
        }
    
    # Simple chat endpoint
    @app.post("/api/chat", tags=["Chat"])
    async def chat(message: dict):
        """Simple chat endpoint"""
        try:
            user_message = message.get("message", "")
            
            # Simple response logic (you can replace this with your own AI)
            if "hello" in user_message.lower() or "hi" in user_message.lower():
                response = "Hello! I'm your SRM Guide Bot. How can I help you today?"
            elif "admission" in user_message.lower():
                response = "For SRM admissions, visit our website or contact the admissions office. Requirements include 10th & 12th marksheets and entrance exam scores."
            elif "courses" in user_message.lower():
                response = "SRM offers various courses including Engineering, Medicine, Management, and Arts. Popular ones are Computer Science, Electronics, and Mechanical Engineering."
            elif "hostel" in user_message.lower():
                response = "SRM provides hostel facilities with modern amenities. Fees range from ₹80,000 to ₹1,50,000 per year depending on room type."
            else:
                response = "I'm here to help with SRM University information. You can ask about admissions, courses, hostel facilities, or any other queries."
            
            return {
                "success": True,
                "response": response,
                "message": user_message
            }
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": True,
                    "message": "Failed to process chat message"
                }
            )
    
    # OPTIONS handler for CORS preflight
    @app.options("/api/chat", tags=["Chat"])
    async def chat_options():
        """Handle CORS preflight request for chat endpoint"""
        return {"message": "OK"}
    
    # Exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation exceptions"""
        logger.error(f"Validation Error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Internal server error",
                "status_code": 500
            }
        )
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    print("🚀 Starting SRM Guide Bot Backend (Simplified)...")
    print("✅ No complex dependencies required")
    print("🌐 Backend will be available at: http://localhost:8000")
    print("📚 API docs will be at: http://localhost:8000/api/docs")
    print("💬 Test chat at: http://localhost:8000/api/chat")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    uvicorn.run(
        "main-simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
