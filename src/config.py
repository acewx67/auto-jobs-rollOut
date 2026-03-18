"""
Centralized configuration module for the Jobs Automaton application.

Loads environment variables from .env file and provides them
as module-level constants for use throughout the application.

All configuration is loaded once at import time.
"""

import os
import logging
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# ============================================================================
# Groq API Configuration
# ============================================================================

GROQ_API_KEY: Optional[str] = os.getenv('GROQ_API_KEY')
"""Groq API key for LLM interactions. Required for resume tailoring."""

GROQ_MODEL: str = "openai/gpt-oss-120b"
"""Groq model to use for resume analysis and tailoring."""

GROQ_TIMEOUT_SECONDS: int = 30
"""Timeout for Groq API calls in seconds."""

GROQ_MAX_RETRIES: int = 3
"""Maximum number of retries for failed Groq API calls."""

# ============================================================================
# Application Settings
# ============================================================================

LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
"""Logging level for the application (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""

DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
"""Debug mode flag. Set to True for development, False for production."""

PORT: int = int(os.getenv('PORT', '5000'))
"""Port number for the REST API server."""

HOST: str = os.getenv('HOST', '0.0.0.0')
"""Host address for the REST API server."""

# ============================================================================
# Feature Toggles (for future use)
# ============================================================================

ENABLE_AUTO_FETCH: bool = os.getenv('ENABLE_AUTO_FETCH', 'False').lower() == 'true'
"""Enable auto job fetching feature (Feature 2)."""

ENABLE_AUTO_APPLY: bool = os.getenv('ENABLE_AUTO_APPLY', 'False').lower() == 'true'
"""Enable auto job application feature (Feature 3)."""

# ============================================================================
# File Upload Settings
# ============================================================================

MAX_FILE_SIZE_MB: int = 50
"""Maximum file size for uploads in megabytes."""

MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
"""Maximum file size for uploads in bytes."""

ALLOWED_RESUME_EXTENSIONS: set = {'pdf', 'docx', 'doc', 'txt', 'md'}
"""Allowed file extensions for resume uploads."""

# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        level (str, optional): Logging level to use. 
                              Defaults to LOG_LEVEL from config.
    """
    import logging
    import os
    
    if level is None:
        level = LOG_LEVEL
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    logging_level = getattr(logging, level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/tailoring.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {level}")


# ============================================================================
# Validation
# ============================================================================

def validate_config() -> None:
    """
    Validate that all required configuration is present.
    
    Raises:
        ValueError: If required configuration is missing.
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )


# ============================================================================
# Configuration Summary
# ============================================================================

def get_config_summary() -> dict:
    """
    Get a summary of the current configuration.
    
    Returns:
        dict: Dictionary containing configuration info (with API key masked).
    """
    return {
        'groq_api_key': '***' + GROQ_API_KEY[-4:] if GROQ_API_KEY else None,
        'groq_model': GROQ_MODEL,
        'log_level': LOG_LEVEL,
        'debug': DEBUG,
        'port': PORT,
        'host': HOST,
        'enable_auto_fetch': ENABLE_AUTO_FETCH,
        'enable_auto_apply': ENABLE_AUTO_APPLY,
    }
