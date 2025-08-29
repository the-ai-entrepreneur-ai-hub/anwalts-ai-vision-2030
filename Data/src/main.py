"""
German Legal AI Model Server
Optimized for Ryzen 9 7950X3D with 128GB RAM
"""

import os
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
    pipeline
)
from peft import PeftModel
import uvicorn
import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
from prometheus_client import Counter, Histogram, generate_latest
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
MODEL_INFERENCE_TIME = Histogram('model_inference_seconds', 'Model inference time')

# Global model and tokenizer
model = None
tokenizer = None
redis_client = None

class GermanLegalRequest(BaseModel):
    """Request model for German legal AI processing."""
    instruction: str = Field(..., description="Legal instruction in German")
    input_text: str = Field("", description="Additional context or document text")
    max_length: int = Field(512, ge=50, le=2048, description="Maximum response length")
    temperature: float = Field(0.7, ge=0.1, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.1, le=1.0, description="Top-p sampling parameter")
    do_sample: bool = Field(True, description="Whether to use sampling")

class GermanLegalResponse(BaseModel):
    """Response model for German legal AI."""
    response: str
    instruction: str
    processing_time: float
    model_info: Dict[str, Any]

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    system_info: Dict[str, Any]
    timestamp: float

class GermanLegalAI:
    """German Legal AI Model Handler optimized for CPU inference."""
    
    def __init__(self, 
                 model_path: str,
                 quantized_model_path: Optional[str] = None,
                 use_quantized: bool = True):
        self.model_path = model_path
        self.quantized_model_path = quantized_model_path
        self.use_quantized = use_quantized
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        
        # Optimize for Ryzen 9 7950X3D
        torch.set_num_threads(int(os.getenv("TORCH_NUM_THREADS", "28")))
        
    async def load_model(self):
        """Load the German legal model and tokenizer."""
        try:
            logger.info("Loading German Legal AI model...", 
                       model_path=self.model_path,
                       use_quantized=self.use_quantized)
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.padding_side = "right"
            
            # Load model based on quantization preference
            if self.use_quantized and self.quantized_model_path:
                # Load quantized model
                from optimum.gptq import GPTQQuantizer
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.quantized_model_path,
                    device_map="cpu",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
            else:
                # Load regular model with optimization
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    device_map="cpu",
                    torch_dtype=torch.float32,  # Better for CPU
                    trust_remote_code=True
                )
            
            # Set model to evaluation mode
            self.model.eval()
            
            logger.info("Model loaded successfully",
                       model_size=f"{self.model.num_parameters():,} parameters",
                       device=self.device)
            
            return True
            
        except Exception as e:
            logger.error("Failed to load model", error=str(e))
            raise e
    
    def format_prompt(self, instruction: str, input_text: str = "") -> str:
        """Format prompt for German legal instruction-following."""
        if input_text.strip():
            return f"### Anweisung:\n{instruction}\n\n### Eingabe:\n{input_text}\n\n### Antwort:\n"
        else:
            return f"### Anweisung:\n{instruction}\n\n### Antwort:\n"
    
    async def generate_response(self, request: GermanLegalRequest) -> str:
        """Generate response using the German legal model."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        try:
            # Format the prompt
            prompt = self.format_prompt(request.instruction, request.input_text)
            
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
                padding=False
            )
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_length=len(inputs.input_ids[0]) + request.max_length,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    do_sample=request.do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    length_penalty=1.0,
                    early_stopping=True
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][len(inputs.input_ids[0]):],
                skip_special_tokens=True
            ).strip()
            
            # Clean up response
            if "</s>" in response:
                response = response.split("</s>")[0].strip()
            
            inference_time = time.time() - start_time
            MODEL_INFERENCE_TIME.observe(inference_time)
            
            logger.info("Generated response",
                       instruction_length=len(request.instruction),
                       response_length=len(response),
                       inference_time=inference_time)
            
            return response
            
        except Exception as e:
            logger.error("Generation failed", error=str(e))
            raise e

# Initialize the AI model
ai_model = GermanLegalAI(
    model_path=os.getenv("MODEL_PATH", "./models/disco-german-legal-7b"),
    quantized_model_path=os.getenv("QUANTIZED_MODEL_PATH", "./models/disco-german-legal-7b-gptq"),
    use_quantized=os.getenv("USE_QUANTIZED", "true").lower() == "true"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("Starting German Legal AI Server...")
    
    # Initialize Redis connection
    global redis_client
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning("Redis connection failed", error=str(e))
        redis_client = None
    
    # Load the AI model
    await ai_model.load_model()
    
    logger.info("German Legal AI Server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down German Legal AI Server...")

# Create FastAPI app
app = FastAPI(
    title="German Legal AI Server",
    description="AI-powered German legal document processing and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    return HealthResponse(
        status="healthy" if ai_model.model is not None else "loading",
        model_loaded=ai_model.model is not None,
        system_info={
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "torch_threads": torch.get_num_threads()
        },
        timestamp=time.time()
    )

@app.post("/generate", response_model=GermanLegalResponse)
async def generate_legal_response(request: GermanLegalRequest):
    """Generate German legal response."""
    start_time = time.time()
    
    REQUEST_COUNT.labels(method="POST", endpoint="/generate").inc()
    
    try:
        # Check cache if Redis is available
        cache_key = None
        if redis_client:
            cache_key = f"legal:{hash(request.instruction + request.input_text)}"
            cached_response = redis_client.get(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                return GermanLegalResponse.parse_raw(cached_response)
        
        # Generate response
        response_text = await ai_model.generate_response(request)
        
        processing_time = time.time() - start_time
        REQUEST_DURATION.observe(processing_time)
        
        response = GermanLegalResponse(
            response=response_text,
            instruction=request.instruction,
            processing_time=processing_time,
            model_info={
                "model_path": ai_model.model_path,
                "quantized": ai_model.use_quantized,
                "device": ai_model.device
            }
        )
        
        # Cache the response if Redis is available
        if redis_client and cache_key:
            redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                response.json()
            )
        
        return response
        
    except Exception as e:
        logger.error("Request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()

@app.get("/model/info")
async def model_info():
    """Get model information."""
    if not ai_model.model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_path": ai_model.model_path,
        "quantized": ai_model.use_quantized,
        "device": ai_model.device,
        "parameters": ai_model.model.num_parameters(),
        "torch_threads": torch.get_num_threads(),
        "model_type": type(ai_model.model).__name__
    }

@app.post("/warmup")
async def warmup_model():
    """Warm up the model with a test request."""
    test_request = GermanLegalRequest(
        instruction="Teste die Modellverfügbarkeit.",
        max_length=50
    )
    
    try:
        await ai_model.generate_response(test_request)
        return {"status": "warmed_up", "message": "Model is ready"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Warmup failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for model serving
        log_level="info"
    )