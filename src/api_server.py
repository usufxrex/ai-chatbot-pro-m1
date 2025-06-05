"""
ADVANCED API SERVER - M1 OPTIMIZED
Production-ready FastAPI server with advanced features
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Union
import asyncio
import uvicorn
import logging
from datetime import datetime, timedelta
import json
import time
from contextlib import asynccontextmanager
import psutil
import threading
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Import our advanced LLM system
from advanced_llm import AdvancedChatbot, LLMConfig, LLMMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('../logs/api.log')
    ]
)
logger = logging.getLogger(__name__)

# Global session management
class AdvancedSessionManager:
    def __init__(self):
        self.sessions: Dict[str, AdvancedChatbot] = {}
        self.session_metadata: Dict[str, Dict] = {}
        self.max_sessions = 100
        self.session_timeout = timedelta(hours=4)
        
        # Performance tracking
        self.request_counter = 0
        self.response_times = []
        self.error_counter = 0
        
        # Start cleanup task
        self.cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("🚀 Advanced Session Manager initialized")
    
    def create_session(self, personality: str, config: Optional[Dict] = None) -> str:
        """Create new session with advanced configuration"""
        # Cleanup if needed
        if len(self.sessions) >= self.max_sessions:
            self._cleanup_old_sessions()
        
        # Create LLM config
        llm_config = LLMConfig()
        if config:
            for key, value in config.items():
                if hasattr(llm_config, key):
                    setattr(llm_config, key, value)
        
        # Create chatbot
        chatbot = AdvancedChatbot(personality, llm_config)
        session_id = chatbot.session_id
        
        # Store session
        self.sessions[session_id] = chatbot
        self.session_metadata[session_id] = {
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "personality": personality,
            "config": config or {},
            "request_count": 0
        }
        
        logger.info(f"📝 Created session {session_id} with personality {personality}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[AdvancedChatbot]:
        """Get session and update activity"""
        if session_id in self.sessions:
            self.session_metadata[session_id]["last_activity"] = datetime.now()
            self.session_metadata[session_id]["request_count"] += 1
            return self.sessions[session_id]
        return None
    
    def _cleanup_old_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, metadata in self.session_metadata.items():
            if now - metadata["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.sessions.pop(session_id, None)
            self.session_metadata.pop(session_id, None)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def _periodic_cleanup(self):
        """Periodic cleanup thread"""
        while True:
            time.sleep(1800)  # Run every 30 minutes
            self._cleanup_old_sessions()
    
    def get_stats(self) -> Dict:
        """Get session manager statistics"""
        return {
            "active_sessions": len(self.sessions),
            "total_requests": self.request_counter,
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "error_rate": self.error_counter / max(self.request_counter, 1),
            "sessions_by_personality": self._get_personality_distribution()
        }
    
    def _get_personality_distribution(self) -> Dict[str, int]:
        """Get distribution of sessions by personality"""
        distribution = {}
        for metadata in self.session_metadata.values():
            personality = metadata["personality"]
            distribution[personality] = distribution.get(personality, 0) + 1
        return distribution

# Initialize session manager
session_manager = AdvancedSessionManager()

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Advanced M1-Optimized AI API Server")
    system_info = {
        "cpu_cores": psutil.cpu_count(),
        "memory_gb": psutil.virtual_memory().total / (1024**3),
        "platform": "M1 MacBook Pro"
    }
    logger.info(f"💻 System: {system_info}")
    yield
    # Shutdown
    logger.info("🛑 Shutting down API server")

# Initialize FastAPI
app = FastAPI(
    title="Advanced AI Chatbot API",
    description="M1-optimized professional AI chatbot API with advanced prompt engineering",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    personality: Literal["helpful_assistant", "technical_expert", "creative_partner", "business_advisor", "learning_tutor"] = "helpful_assistant"
    session_id: Optional[str] = None
    prompt_technique: Literal["standard", "chain_of_thought", "few_shot", "role_playing", "socratic", "step_by_step"] = "standard"
    temperature: Optional[float] = Field(None, ge=0.1, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=50, le=500)
    advanced_config: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    personality: str
    prompt_technique: str
    metadata: Dict
    performance: Dict
    timestamp: datetime

class SessionCreateRequest(BaseModel):
    personality: Literal["helpful_assistant", "technical_expert", "creative_partner", "business_advisor", "learning_tutor"]
    config: Optional[Dict] = None

class SessionResponse(BaseModel):
    session_id: str
    personality: str
    created_at: datetime
    config: Dict

class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: Dict[str, float]
    api_stats: Dict
    active_sessions: int
    uptime: str

class ConversationAnalysis(BaseModel):
    session_id: str
    analysis: Dict
    export_timestamp: datetime

# Request tracking
def track_request(response_time: float, success: bool = True):
    """Track request metrics"""
    session_manager.request_counter += 1
    session_manager.response_times.append(response_time)
    
    if not success:
        session_manager.error_counter += 1
    
    # Keep only last 1000 response times
    if len(session_manager.response_times) > 1000:
        session_manager.response_times = session_manager.response_times[-1000:]

# API Endpoints
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Advanced AI Chatbot API",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "M1 Metal acceleration",
            "Advanced prompt engineering",
            "Multiple AI personalities",
            "Real-time analytics",
            "Session management"
        ],
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "system": "M1 MacBook Pro Optimized"
    }

@app.get("/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get comprehensive system metrics"""
    # System metrics
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # API stats
    api_stats = session_manager.get_stats()
    
    return SystemMetrics(
        cpu_usage=cpu_percent,
        memory_usage={
            "total_gb": memory.total / (1024**3),
            "used_gb": memory.used / (1024**3),
            "available_gb": memory.available / (1024**3),
            "percent": memory.percent
        },
        api_stats=api_stats,
        active_sessions=len(session_manager.sessions),
        uptime=str(timedelta(seconds=int(time.time() - session_manager.request_counter)))
    )

@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """Create new chat session"""
    try:
        session_id = session_manager.create_session(request.personality, request.config)
        metadata = session_manager.session_metadata[session_id]
        
        return SessionResponse(
            session_id=session_id,
            personality=request.personality,
            created_at=metadata["created_at"],
            config=metadata["config"]
        )
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """Advanced chat endpoint with M1 optimization"""
    start_time = time.time()
    
    try:
        # Get or create session
        if request.session_id:
            chatbot = session_manager.get_session(request.session_id)
            if not chatbot:
                raise HTTPException(status_code=404, detail="Session not found")
            session_id = request.session_id
        else:
            session_id = session_manager.create_session(request.personality, request.advanced_config)
            chatbot = session_manager.get_session(session_id)
        
        # Generate response
        response_msg = chatbot.chat(
            user_message=request.message,
            prompt_technique=request.prompt_technique,
            temperature=request.temperature
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Track metrics in background
        background_tasks.add_task(track_request, response_time, True)
        
        # Get conversation analysis
        analysis = chatbot.get_conversation_analysis()
        
        return ChatResponse(
            response=response_msg.content,
            session_id=session_id,
            personality=request.personality,
            prompt_technique=request.prompt_technique,
            metadata={
                "processing_time": response_msg.processing_time,
                "token_count": response_msg.token_count,
                "model_used": response_msg.model_used,
                "prompt_type": response_msg.prompt_type,
                "confidence_score": response_msg.confidence_score,
                "api_response_time": response_time
            },
            performance=analysis["performance"],
            timestamp=response_msg.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        background_tasks.add_task(track_request, time.time() - start_time, False)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/sessions", response_model=List[Dict])
async def list_sessions():
    """List all active sessions"""
    sessions_info = []
    for session_id, metadata in session_manager.session_metadata.items():
        chatbot = session_manager.sessions.get(session_id)
        if chatbot:
            sessions_info.append({
                "session_id": session_id,
                "personality": metadata["personality"],
                "created_at": metadata["created_at"].isoformat(),
                "last_activity": metadata["last_activity"].isoformat(),
                "request_count": metadata["request_count"],
                "message_count": len(chatbot.messages)
            })
    return sessions_info

@app.get("/session/{session_id}/analysis", response_model=ConversationAnalysis)
async def get_conversation_analysis(session_id: str):
    """Get detailed conversation analysis"""
    chatbot = session_manager.get_session(session_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Session not found")
    
    analysis = chatbot.get_conversation_analysis()
    
    return ConversationAnalysis(
        session_id=session_id,
        analysis=analysis,
        export_timestamp=datetime.now()
    )

@app.post("/chat/compare", response_model=Dict[str, ChatResponse])
async def compare_personalities(request: ChatRequest):
    """Compare responses across all personalities"""
    personalities = ["helpful_assistant", "technical_expert", "creative_partner", "business_advisor", "learning_tutor"]
    responses = {}
    
    for personality in personalities:
        try:
            # Create temporary session for comparison
            temp_session_id = session_manager.create_session(personality)
            temp_chatbot = session_manager.get_session(temp_session_id)
            
            # Generate response
            response_msg = temp_chatbot.chat(
                user_message=request.message,
                prompt_technique=request.prompt_technique,
                temperature=request.temperature or 0.7
            )
            
            # Get analysis
            analysis = temp_chatbot.get_conversation_analysis()
            
            responses[personality] = ChatResponse(
                response=response_msg.content,
                session_id=temp_session_id,
                personality=personality,
                prompt_technique=request.prompt_technique,
                metadata={
                    "processing_time": response_msg.processing_time,
                    "token_count": response_msg.token_count,
                    "model_used": response_msg.model_used
                },
                performance=analysis["performance"],
                timestamp=response_msg.timestamp
            )
            
        except Exception as e:
            logger.error(f"Comparison failed for {personality}: {e}")
            continue
    
    return responses

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete specific session"""
    if session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.sessions.pop(session_id, None)
    session_manager.session_metadata.pop(session_id, None)
    
    return {"message": f"Session {session_id} deleted successfully"}

@app.delete("/sessions")
async def clear_all_sessions():
    """Clear all sessions (admin operation)"""
    session_count = len(session_manager.sessions)
    session_manager.sessions.clear()
    session_manager.session_metadata.clear()
    
    return {"message": f"Cleared {session_count} sessions successfully"}

@app.get("/personalities")
async def get_personalities():
    """Get available AI personalities with detailed information"""
    return [
        {
            "id": "helpful_assistant",
            "name": "General Assistant",
            "description": "Versatile AI assistant for general questions and tasks",
            "strengths": ["Broad knowledge", "Balanced responses", "Adaptable communication"],
            "best_for": ["General inquiries", "Explanations", "Daily tasks"],
            "example_use_cases": ["Explaining concepts", "Planning activities", "General problem-solving"]
        },
        {
            "id": "technical_expert",
            "name": "Technical Expert",
            "description": "Senior software engineer and system architect",
            "strengths": ["Debugging expertise", "System design", "Best practices"],
            "best_for": ["Code review", "Architecture decisions", "Technical troubleshooting"],
            "example_use_cases": ["API optimization", "Database design", "Performance tuning"]
        },
        {
            "id": "creative_partner",
            "name": "Creative Writer",
            "description": "Creative writing mentor and storytelling expert",
            "strengths": ["Story development", "Character creation", "Creative inspiration"],
            "best_for": ["Writing projects", "Creative brainstorming", "Overcoming blocks"],
            "example_use_cases": ["Plot development", "Character arcs", "Genre exploration"]
        },
        {
            "id": "business_advisor",
            "name": "Business Consultant", 
            "description": "Strategic business advisor and operations expert",
            "strengths": ["Strategic analysis", "Market insights", "ROI optimization"],
            "best_for": ["Business strategy", "Market analysis", "Growth planning"],
            "example_use_cases": ["Pricing strategy", "Market entry", "Competitive analysis"]
        },
        {
            "id": "learning_tutor",
            "name": "Learning Tutor",
            "description": "Patient educator and knowledge mentor",
            "strengths": ["Clear explanations", "Step-by-step teaching", "Adaptive learning"],
            "best_for": ["Learning concepts", "Skill development", "Educational support"],
            "example_use_cases": ["Complex topics", "Skill building", "Academic support"]
        }
    ]

@app.get("/benchmark")
async def run_benchmark():
    """Run performance benchmark"""
    start_time = time.time()
    
    # Create test session
    session_id = session_manager.create_session("helpful_assistant")
    chatbot = session_manager.get_session(session_id)
    
    # Benchmark tests
    test_cases = [
        {"message": "Hello, how are you?", "technique": "standard"},
        {"message": "Explain machine learning", "technique": "chain_of_thought"},
        {"message": "Help me debug Python code", "technique": "few_shot"},
        {"message": "Plan a marketing strategy", "technique": "step_by_step"},
        {"message": "Write a story outline", "technique": "role_playing"}
    ]
    
    results = []
    for test in test_cases:
        test_start = time.time()
        response = chatbot.chat(
            user_message=test["message"],
            prompt_technique=test["technique"]
        )
        test_time = time.time() - test_start
        
        results.append({
            "message": test["message"],
            "technique": test["technique"],
            "response_time": test_time,
            "token_count": response.token_count,
            "response_length": len(response.content)
        })
    
    total_time = time.time() - start_time
    avg_time = sum(r["response_time"] for r in results) / len(results)
    
    return {
        "benchmark_completed": datetime.now().isoformat(),
        "total_time": total_time,
        "average_response_time": avg_time,
        "test_count": len(test_cases),
        "system_info": {
            "cpu_cores": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "platform": "M1 MacBook Pro"
        },
        "detailed_results": results
    }

if __name__ == "__main__":
    print("🚀 Starting Advanced M1-Optimized AI Chatbot API")
    print("=" * 60)
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔧 System Metrics: http://localhost:8000/metrics")
    print("🧪 Performance Benchmark: http://localhost:8000/benchmark")
    print("💬 Chat Endpoint: POST http://localhost:8000/chat")
    print("🎭 Personalities: GET http://localhost:8000/personalities")
    print("⚡ Optimized for M1 MacBook Pro with Metal acceleration")
    print("=" * 60)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["./"],
        log_level="info",
        access_log=True
    )