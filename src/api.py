"""
Simple REST API for the resume tailoring pipeline.

Provides HTTP endpoints for:
- Tailoring resumes
- Analyzing job descriptions
- Checking ATS scores
- Batch processing

Uses Flask for easy deployment.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from src.config import PORT, DEBUG, MAX_FILE_SIZE_BYTES, ALLOWED_RESUME_EXTENSIONS, setup_logging
from src.core.resume_tailor import TailorPipeline, TailorPipelineError, PipelineConfig
from src.utils.ats_optimizer import ATSOptimizer
from src.groq_client.client import GroqClient, GroqClientError

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_BYTES
ALLOWED_EXTENSIONS = ALLOWED_RESUME_EXTENSIONS
UPLOAD_FOLDER = PipelineConfig.INPUT_RESUME_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def error_response(message: str, status_code: int = 400) -> Tuple[Dict, int]:
    """Create standardized error response"""
    return {
        'success': False,
        'error': message
    }, status_code


def success_response(data: Dict = None, **kwargs) -> Dict:
    """Create standardized success response"""
    response = {'success': True}
    if data:
        response.update(data)
    response.update(kwargs)
    return response


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'jobs-automaton-api',
        'version': '0.1.0'
    }), 200


# Tailor resume endpoint
@app.route('/api/tailor', methods=['POST'])
def tailor_resume():
    """
    Tailor a resume for a specific job.
    
    Request format:
    - Form data:
      - resume: File (PDF/DOCX) - required
      - job_description: Text or file path - required
      - output_format: str (txt/json) - optional, default: txt
      
    Returns:
      JSON with tailoring results including ATS scores
    """
    try:
        # Validate request
        if 'resume' not in request.files:
            return error_response("Resume file is required")
        
        if 'job_description' not in request.form:
            return error_response("Job description is required")
        
        resume_file = request.files['resume']
        if resume_file.filename == '':
            return error_response("Resume file must be selected")
        
        if not allowed_file(resume_file.filename):
            return error_response(f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
        
        job_description = request.form['job_description'].strip()
        if not job_description:
            return error_response("Job description cannot be empty")
        
        output_format = request.form.get('output_format', 'txt')
        if output_format not in ['txt', 'json']:
            return error_response("Invalid output format. Use: txt, json")
        
        # Save uploaded resume
        folder = Path(UPLOAD_FOLDER)
        folder.mkdir(parents=True, exist_ok=True)
        
        filename = secure_filename(resume_file.filename)
        resume_path = folder / filename
        resume_file.save(str(resume_path))
        
        logger.info(f"Processing tailoring request: {filename}")
        
        # Initialize pipeline
        pipeline = TailorPipeline(output_dir=PipelineConfig.OUTPUT_RESUME_DIR)
        
        # Tailor resume
        result = pipeline.tailor(str(resume_path), job_description, output_format)
        
        # Return results
        return jsonify(success_response({
            'original_ats_score': result['original_ats_score'],
            'final_ats_score': result['final_ats_score'],
            'ats_improvement': result['ats_improvement'],
            'ats_improvement_percentage': result['ats_improvement_percentage'],
            'key_changes': result['key_changes'],
            'matched_keywords': result['matched_keywords'],
            'missing_keywords': result['missing_keywords'],
            'metrics_preserved': result['metrics_preserved'],
            'output_file': result['output_file'],
            'processing_time_seconds': result['processing_time_seconds'],
            'report': result['report'],
        })), 200
        
    except TailorPipelineError as e:
        logger.error(f"Tailoring error: {str(e)}")
        return error_response(f"Tailoring failed: {str(e)}", 422)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return error_response("Internal server error", 500)


# Check ATS score endpoint
@app.route('/api/ats-score', methods=['POST'])
def check_ats_score():
    """
    Calculate ATS score for a resume against a job description.
    
    Request format:
    - JSON:
      - resume_text: str - resume content
      - job_description: str - job posting
      
    Returns:
      JSON with ATS score breakdown
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required")
        
        resume_text = data.get('resume_text', '').strip()
        job_description = data.get('job_description', '').strip()
        
        if not resume_text:
            return error_response("resume_text is required")
        if not job_description:
            return error_response("job_description is required")
        
        logger.info("Processing ATS score request")
        
        # Calculate score
        optimizer = ATSOptimizer()
        ats_score = optimizer.calculate_ats_score(resume_text, job_description)
        
        # Generate report
        report = optimizer.generate_optimization_report(ats_score, resume_text, job_description)
        
        return jsonify(success_response({
            'overall_score': ats_score['overall_score'],
            'keyword_score': ats_score['keyword_score'],
            'format_score': ats_score['format_score'],
            'content_score': ats_score['content_score'],
            'readability_score': ats_score['readability_score'],
            'matched_keywords': ats_score['matched_keywords'],
            'missing_keywords': ats_score['missing_keywords'],
            'report': report,
        })), 200
        
    except Exception as e:
        logger.error(f"ATS score error: {str(e)}")
        return error_response("Failed to calculate ATS score", 500)


# Analyze job endpoint
@app.route('/api/analyze-job', methods=['POST'])
def analyze_job():
    """
    Analyze a job description to extract requirements.
    
    Request format:
    - JSON:
      - job_description: str - job posting
      
    Returns:
      JSON with analysis including required skills, experience, keywords
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required")
        
        job_description = data.get('job_description', '').strip()
        
        if not job_description:
            return error_response("job_description is required")
        
        logger.info("Processing job analysis request")
        
        # Initialize Groq client
        groq_client = GroqClient()
        
        # Analyze job
        analysis = groq_client.analyze_job_description(job_description)
        
        return jsonify(success_response(analysis)), 200
        
    except GroqClientError as e:
        logger.error(f"Groq API error: {str(e)}")
        return error_response(f"API error: {str(e)}", 503)
    except Exception as e:
        logger.error(f"Job analysis error: {str(e)}")
        return error_response("Failed to analyze job", 500)


# Status endpoint
@app.route('/api/status', methods=['GET'])
def status():
    """Get API status and capabilities"""
    return jsonify({
        'service': 'jobs-automaton',
        'version': '0.1.0',
        'status': 'operational',
        'capabilities': [
            'Resume tailoring',
            'ATS scoring',
            'Job analysis',
            'Batch processing'
        ],
        'endpoints': {
            '/health': 'Health check',
            '/api/tailor': 'Tailor resume (POST)',
            '/api/ats-score': 'Calculate ATS score (POST)',
            '/api/analyze-job': 'Analyze job description (POST)',
            '/api/status': 'API status'
        }
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return error_response("Endpoint not found", 404)


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return error_response("Method not allowed", 405)


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large"""
    return error_response("File too large (max 50MB)", 413)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return error_response("Internal server error", 500)


def create_app(config_override=None):
    """Application factory for testing"""
    if config_override:
        app.config.update(config_override)
    return app


if __name__ == '__main__':
    # Setup logging
    setup_logging()
    
    # Initialize directories
    PipelineConfig.initialize_directories()
    
    # Run development server
    logger.info(f"Starting Jobs Automaton API on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
