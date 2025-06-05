#!/usr/bin/env python3
"""
PRODUCTION FASTAPI SERVER - M1 OPTIMIZED
Complete API server for the M1 chatbot system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
import uvicorn
import logging
from datetime import datetime
import time
import psutil
from pathlib import Path

# Import our working chatbot system
from working_chatbot import M1ChatbotSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="M1 AI Chatbot API",
    description="Production-ready M1-optimized AI chatbot API with multiple personalities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot system
chatbot_system = M1ChatbotSystem()

# Performance tracking
request_stats = {
    "total_requests": 0,
    "total_response_time": 0.0,
    "error_count": 0
}

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    personality: Literal["technical_expert", "creative_partner", "business_advisor"] = "technical_expert"
    session_id: Optional[str] = None
    technique: Literal["standard", "chain_of_thought", "few_shot", "step_by_step", "socratic", "analogical"] = "standard"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    personality: str
    technique: str
    processing_time: float
    timestamp: datetime

class SessionRequest(BaseModel):
    personality: Literal["technical_expert", "creative_partner", "business_advisor"]

class SessionResponse(BaseModel):
    session_id: str
    personality: str
    created_at: datetime

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: Dict[str, float]
    active_sessions: int
    total_requests: int
    avg_response_time: float
    uptime: str

class PersonalityInfo(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str]

# Helper functions
def track_request(response_time: float, success: bool = True):
    """Track request metrics"""
    request_stats["total_requests"] += 1
    request_stats["total_response_time"] += response_time
    if not success:
        request_stats["error_count"] += 1

# API Endpoints
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "M1 AI Chatbot API",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "M1 MacBook Pro optimized",
            "Multiple AI personalities",
            "Advanced prompt engineering",
            "Session management",
            "Real-time analytics"
        ],
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "system": "M1 MacBook Pro",
        "version": "1.0.0"
    }

@app.get("/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get system metrics"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    avg_response_time = (
        request_stats["total_response_time"] / request_stats["total_requests"]
        if request_stats["total_requests"] > 0 else 0
    )
    
    return SystemMetrics(
        cpu_usage=cpu_percent,
        memory_usage={
            "total_gb": memory.total / (1024**3),
            "used_gb": memory.used / (1024**3),
            "available_gb": memory.available / (1024**3),
            "percent": memory.percent
        },
        active_sessions=len(chatbot_system.sessions),
        total_requests=request_stats["total_requests"],
        avg_response_time=avg_response_time,
        uptime="N/A"  # Could implement proper uptime tracking
    )

@app.get("/personalities", response_model=List[PersonalityInfo])
async def get_personalities():
    """Get available AI personalities"""
    personalities = []
    
    for personality_id, data in chatbot_system.personalities.items():
        personalities.append(PersonalityInfo(
            id=personality_id,
            name=data["name"],
            description=data["description"],
            capabilities=list(data["responses"].keys())
        ))
    
    return personalities

@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """Create new chat session"""
    try:
        session_id = chatbot_system.create_session(request.personality)
        session = chatbot_system.sessions[session_id]
        
        return SessionResponse(
            session_id=session_id,
            personality=request.personality,
            created_at=session["created_at"]
        )
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """Main chat endpoint"""
    start_time = time.time()
    
    try:
        # Create session if not provided
        if not request.session_id:
            session_id = chatbot_system.create_session(request.personality)
        else:
            session_id = request.session_id
            if session_id not in chatbot_system.sessions:
                raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate response
        result = chatbot_system.chat(
            session_id=session_id,
            user_message=request.message,
            technique=request.technique
        )
        
        response_time = time.time() - start_time
        
        # Track metrics in background
        background_tasks.add_task(track_request, response_time, True)
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            personality=result["personality"],
            technique=result["technique"],
            processing_time=result["processing_time"],
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = time.time() - start_time
        background_tasks.add_task(track_request, response_time, False)
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    sessions_info = []
    
    for session_id, session_data in chatbot_system.sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "personality": session_data["personality"],
            "created_at": session_data["created_at"],
            "message_count": len(session_data["conversation"]),
            "last_activity": session_data["conversation"][-1]["timestamp"] if session_data["conversation"] else session_data["created_at"]
        })
    
    return sessions_info

@app.get("/session/{session_id}/analysis")
async def get_session_analysis(session_id: str):
    """Get session analysis"""
    try:
        analysis = chatbot_system.get_session_analysis(session_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete specific session"""
    if session_id not in chatbot_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del chatbot_system.sessions[session_id]
    return {"message": f"Session {session_id} deleted successfully"}

@app.delete("/sessions")
async def clear_all_sessions():
    """Clear all sessions"""
    session_count = len(chatbot_system.sessions)
    chatbot_system.sessions.clear()
    return {"message": f"Cleared {session_count} sessions successfully"}

@app.post("/chat/compare")
async def compare_personalities(request: ChatRequest):
    """Compare responses from all personalities"""
    responses = {}
    
    for personality in ["technical_expert", "creative_partner", "business_advisor"]:
        try:
            # Create temporary session
            temp_session_id = chatbot_system.create_session(personality)
            
            # Get response
            result = chatbot_system.chat(
                session_id=temp_session_id,
                user_message=request.message,
                technique=request.technique
            )
            
            responses[personality] = {
                "response": result["response"],
                "processing_time": result["processing_time"],
                "personality": personality
            }
            
            # Clean up temporary session
            del chatbot_system.sessions[temp_session_id]
            
        except Exception as e:
            logger.error(f"Comparison failed for {personality}: {e}")
            responses[personality] = {"error": str(e)}
    
    return responses

@app.get("/demo/test")
async def demo_test():
    """Demo endpoint for testing"""
    # Create a test session
    session_id = chatbot_system.create_session("technical_expert")
    
    # Test message
    result = chatbot_system.chat(
        session_id=session_id,
        user_message="Hello, can you help me optimize my Python code?",
        technique="chain_of_thought"
    )
    
    return {
        "message": "Demo test completed successfully",
        "session_id": session_id,
        "test_response": result["response"][:200] + "...",
        "processing_time": result["processing_time"]
    }

if __name__ == "__main__":
    print("🚀 Starting M1 AI Chatbot API Server")
    print("=" * 50)
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔧 System Metrics: http://localhost:8000/metrics")
    print("🎭 Personalities: http://localhost:8000/personalities")
    print("💬 Chat Endpoint: POST http://localhost:8000/chat")
    print("🧪 Demo Test: http://localhost:8000/demo/test")
    print("⚡ Optimized for M1 MacBook Pro")
    print("=" * 50)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )