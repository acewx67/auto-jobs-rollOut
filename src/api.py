"""
FastAPI for the resume tailoring pipeline.

Provides HTTP endpoints for:
- Tailoring resumes
- Analyzing job descriptions
- Checking ATS scores
- Batch processing
- Downloading generated PDFs
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import PORT, DEBUG, MAX_FILE_SIZE_BYTES, ALLOWED_RESUME_EXTENSIONS, setup_logging
from src.core.resume_tailor import TailorPipeline, TailorPipelineError, PipelineConfig
from src.utils.ats_optimizer import ATSOptimizer
from src.groq_client.client import GroqClient, GroqClientError

# Initialize FastAPI app
app = FastAPI(
    title="Jobs Automaton API",
    description="API for resume tailoring and ATS optimization",
    version="0.2.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Ensure directories exist
PipelineConfig.initialize_directories()

# Models
class ATSScoreRequest(BaseModel):
    resume_text: str
    job_description: str

class JobAnalysisRequest(BaseModel):
    job_description: str

# Helper functions
def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_RESUME_EXTENSIONS

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "jobs-automaton-api",
        "version": "0.2.0"
    }

@app.post("/api/tailor")
async def tailor_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    output_format: str = Form("txt")
):
    """
    Tailor a resume for a specific job.
    """
    try:
        # Validate file
        if not allowed_file(resume.filename):
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_RESUME_EXTENSIONS)}")
        
        # Validate job description
        job_description = job_description.strip()
        if not job_description:
            raise HTTPException(status_code=400, detail="Job description cannot be empty")
        
        # Validate output format
        if output_format not in PipelineConfig.SUPPORTED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Invalid output format. Supported: {', '.join(PipelineConfig.SUPPORTED_FORMATS)}")
        
        # Save uploaded resume
        input_folder = Path(PipelineConfig.INPUT_RESUME_DIR)
        input_folder.mkdir(parents=True, exist_ok=True)
        
        resume_path = input_folder / resume.filename
        with open(resume_path, "wb") as buffer:
            content = await resume.read()
            buffer.write(content)
        
        logger.info(f"Processing tailoring request: {resume.filename}")
        
        # Initialize pipeline
        pipeline = TailorPipeline(output_dir=PipelineConfig.OUTPUT_RESUME_DIR)
        
        # Tailor resume
        result = pipeline.tailor(str(resume_path), job_description, output_format)
        
        # Format output filename for download link
        output_file_path = Path(result['output_file'])
        download_url = f"/api/download/{output_file_path.name}"
        
        return {
            "success": True,
            "original_ats_score": result['original_ats_score'],
            "final_ats_score": result['final_ats_score'],
            "ats_improvement": result['ats_improvement'],
            "ats_improvement_percentage": result['ats_improvement_percentage'],
            "key_changes": result['key_changes'],
            "matched_keywords": result['matched_keywords'],
            "missing_keywords": result['missing_keywords'],
            "metrics_preserved": result['metrics_preserved'],
            "output_file": result['output_file'],
            "download_url": download_url,
            "processing_time_seconds": result['processing_time_seconds'],
            "report": result['report']
        }
        
    except TailorPipelineError as e:
        logger.error(f"Tailoring error: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Tailoring failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/ats-score")
async def check_ats_score(request: ATSScoreRequest):
    """
    Calculate ATS score for a resume against a job description.
    """
    try:
        resume_text = request.resume_text.strip()
        job_description = request.job_description.strip()
        
        if not resume_text or not job_description:
            raise HTTPException(status_code=400, detail="Both resume_text and job_description are required")
        
        logger.info("Processing ATS score request")
        
        optimizer = ATSOptimizer()
        ats_score = optimizer.calculate_ats_score(resume_text, job_description)
        report = optimizer.generate_optimization_report(ats_score, resume_text, job_description)
        
        return {
            "success": True,
            "overall_score": ats_score['overall_score'],
            "keyword_score": ats_score['keyword_score'],
            "format_score": ats_score['format_score'],
            "content_score": ats_score['content_score'],
            "readability_score": ats_score['readability_score'],
            "matched_keywords": ats_score['matched_keywords'],
            "missing_keywords": ats_score['missing_keywords'],
            "report": report
        }
    except Exception as e:
        logger.error(f"ATS score error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate ATS score")

@app.post("/api/analyze-job")
async def analyze_job(request: JobAnalysisRequest):
    """
    Analyze a job description to extract requirements.
    """
    try:
        job_description = request.job_description.strip()
        if not job_description:
            raise HTTPException(status_code=400, detail="job_description is required")
        
        logger.info("Processing job analysis request")
        
        groq_client = GroqClient()
        analysis = groq_client.analyze_job_description(job_description)
        
        return {"success": True, **analysis}
    except GroqClientError as e:
        logger.error(f"Groq API error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"API error: {str(e)}")
    except Exception as e:
        logger.error(f"Job analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze job")

@app.get("/api/status")
async def status():
    """Get API status and capabilities"""
    return {
        "service": "jobs-automaton",
        "version": "0.2.0",
        "status": "operational",
        "capabilities": [
            "Resume tailoring",
            "ATS scoring",
            "Job analysis",
            "LaTeX PDF generation"
        ]
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    Download a generated file with correct MIME type.
    """
    file_path = Path(PipelineConfig.OUTPUT_RESUME_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Map extensions to MIME types
    extension = file_path.suffix.lower()
    content_types = {
        '.pdf': 'application/pdf',
        '.tex': 'text/x-tex',
        '.txt': 'text/plain',
        '.json': 'application/json',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    media_type = content_types.get(extension, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

# Serve static files for the frontend
# Important: This should be at the end to not interfere with API routes
try:
    static_path = Path(__file__).parent / "static"
    if not static_path.exists():
        static_path.mkdir(parents=True, exist_ok=True)
    
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting FastAPI server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
