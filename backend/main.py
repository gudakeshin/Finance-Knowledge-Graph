import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.process import router as process_router
from routers.upload import router as upload_router
from routers.extraction import router as extraction_router
from dotenv import load_dotenv
from app.config import settings

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Finance Knowledge Graph API",
    description="API for building and managing a knowledge graph of financial data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:5174", 
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(process_router, prefix="/api/v1", tags=["process"])
app.include_router(upload_router, prefix="/api/v1", tags=["upload"])
app.include_router(extraction_router, tags=["extraction"])

# Custom endpoints (keep these)

@app.get("/")
async def root():
    return {"message": "Welcome to the Finance Knowledge Graph API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Set up logging to file and console
log_dir = os.path.join(os.path.dirname(__file__), '../logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'backend.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
