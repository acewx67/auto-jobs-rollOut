"""
Groq API integration for AI-powered resume analysis and tailoring.

Uses Groq's openai/gpt-oss-120b model for:
- Intelligent job description analysis
- Resume tailoring with keyword integration
- Professional summary/objective generation
- Achievement optimization while maintaining truthfulness

This module handles all LLM interactions to keep them centralized.
"""

import json
import logging
import time
from typing import Dict, Optional, List
from groq import Groq

from src.config import GROQ_API_KEY

logger = logging.getLogger(__name__)


class GroqClientError(Exception):
    """Custom exception for Groq API errors"""
    pass


class GroqClient:
    """
    Client for interacting with Groq API for resume tailoring.
    
    Uses openai/gpt-oss-120b model for consistent, high-quality outputs.
    Implements error handling, retry logic, and structured prompting.
    """
    
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 2048
    TIMEOUT_SECONDS = 30
    MAX_RETRIES = 3
    
    # System prompt for consistent resume analysis behavior
    RESUME_SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) specialist and resume consultant.
Your role is to analyze job descriptions and tailor resumes to maximize ATS scores while maintaining truthfulness.

Key principles:
1. Always preserve factual accuracy - never fabricate experience or skills
2. Focus on keyword integration from job descriptions
3. Emphasize achievements with metrics (percentages, numbers, timeframes)
4. Use strong action verbs appropriate to the role
5. Match the tone and language of the job posting
6. Ensure all modifications are realistic and defensible

When analyzing job descriptions:
- Extract technical skills, tools, and frameworks required
- Identify key responsibilities and required competencies
- Note soft skills and cultural indicators
- Provide structured output

When tailoring resumes:
- Reorder and reframe existing experiences to match job description
- Highlight relevant achievements and responsibilities
- Add missing keywords naturally without fabrication
- Improve bullet point clarity and impact
- Maintain chronological integrity

IMPORTANT: Return the data as a SINGLE valid JSON object. Escaped characters like backslashes in LaTeX content MUST be properly handled (double-escaped as \\\\ if necessary in the JSON string)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq client.
        
        Args:
            api_key (str, optional): Groq API key. If not provided, will look for
                                    GROQ_API_KEY environment variable.
                                    
        Raises:
            GroqClientError: If API key is not provided or invalid
        """
        api_key = api_key or GROQ_API_KEY
        
        if not api_key:
            raise GroqClientError(
                "Groq API key not provided. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        try:
            self.client = Groq(api_key=api_key)
            self.logger = logging.getLogger(__name__)
            self.logger.info("Groq client initialized successfully")
        except Exception as e:
            raise GroqClientError(f"Failed to initialize Groq client: {str(e)}")
    
    def analyze_job_description(self, job_description: str) -> Dict[str, any]:
        """
        Analyze a job description to extract key requirements and qualifications.
        
        Args:
            job_description (str): Full job posting text
            
        Returns:
            Dict containing:
                - 'job_title': Extracted job title
                - 'required_skills': List of technical skills required
                - 'required_experience': List of experience requirements
                - 'key_responsibilities': List of main job responsibilities
                - 'nice_to_have': Nice-to-have skills/experience
                - 'culture_indicators': Soft skills or culture fit indicators
                - 'keywords': List of important keywords (technical + domain)
                
        Raises:
            GroqClientError: If API call fails
        """
        prompt = f"""Analyze this job description and provide structured requirements.
        
Job Description:
{job_description}

Provide a JSON response with these exact keys:
- job_title: The job title
- required_skills: List of 5-10 technical skills required
- required_experience: 2-3 key experience requirements
- key_responsibilities: 3-5 main project responsibilities
- nice_to_have: 3-5 nice-to-have skills or experience
- culture_indicators: 2-3 soft skills or culture fit indicators
- keywords: List of 10-15 important keywords for ATS (technical + domain terms)

Return ONLY valid JSON, no additional text."""

        response = self._call_api(prompt, temperature=0.3, max_tokens=1500)
        
        try:
            # Extract JSON from response
            result = json.loads(response)
            self.logger.info("Successfully analyzed job description")
            return result
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse job analysis response: {e}")
            raise GroqClientError(f"Invalid JSON response from API: {str(e)}")
    
    def generate_tailored_resume(self, original_resume: str, job_description: str,
                                parsed_job_analysis: Optional[Dict] = None,
                                retry_feedback: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a job-specific tailored version of the resume.
        
        The output preserves all factual information while reframing experiences
        and emphasizing relevant achievements to match the job description.
        
        Args:
            original_resume (str): The original resume text
            job_description (str): The target job description
            parsed_job_analysis (Dict, optional): Pre-analyzed job data
            retry_feedback (str, optional): Feedback to correct previous attempt
            
        Returns:
            Dict containing:
                - 'tailored_resume': Full tailored resume text
                - 'summary_section': Optimized professional summary
                - 'key_changes': List of specific changes made
                - 'keyword_usage': Keywords added/emphasized
                
        Raises:
            GroqClientError: If API call fails
        """
        # Optionally use pre-analyzed job data for better results
        analysis_str = ""
        if parsed_job_analysis:
            analysis_str = f"\n\nKey job requirements (for reference):\n{json.dumps(parsed_job_analysis, indent=2)}"
        
        feedback_str = ""
        if retry_feedback:
            feedback_str = f"\n\nIMPORTANT CORRECTION FROM PREVIOUS ATTEMPT:\n{retry_feedback}\nPlease ensure all requested sections are present in this new version."
        
        prompt = f"""Your task is to tailor a resume for a specific job posting.

IMPORTANT RULES:
1. NEVER fabricate experience or skills - only reframe and reorganize existing ones
2. MAINTAIN FACTUAL ACCURACY - if something isn't in the original, don't add it
3. Focus on keyword matching and achievement highlighting
4. Keep the same companies, positions, dates, and achievements
5. Improve clarity and ATS compatibility

FORMATTING RULES FOR OUTPUT:
- Use **bold format** (with double asterisks) to emphasize: company names, key technologies, and important achievements
- Example: **Google** - **Senior Python Engineer**
- Example: Built using **FastAPI**, **Docker**, and **Kubernetes**
- This bold formatting will be converted to proper LaTeX formatting automatically

Original Resume:
{original_resume}

Target Job Description:
{job_description}
{analysis_str}

Produce a JSON response with:
- tailored_resume: The full tailored resume (preserve all sections, reorder/reframe content, use **bold** for emphasis)
- summary_section: A new professional summary optimized for this role
- key_changes: List of 3-5 specific changes made (descriptions of what was reorganized/reframed)
- keyword_usage: 5-10 job keywords that are now present in tailored resume

CRITICAL: 
1. DO NOT add any watermarks or footer text like "Resume built with Resuminator" or similar.
2. ENSURE all contact information (LinkedIn, GitHub) is correctly mapped and not swapped.
3. DO NOT add placeholder bullet points like "--" or dummy entries.
4. YOU MUST INCLUDE ALL OF THE FOLLOWING SECTIONS: **Professional Summary**, **Technical Skills**, **Experience**, **Projects**, and **Education**. DO NOT OMIT ANY OF THESE SECTIONS.
5. Use standard headers for these sections (e.g., "Projects" not "Recent Projects").
6. If the original resume has projects, you MUST include a Projects section in the tailored version.
{feedback_str}

Keep the resume truthful and defensible. Return ONLY valid JSON."""

        response = self._call_api(prompt, temperature=0.7 if not retry_feedback else 0.8, max_tokens=4096)
        
        try:
            result = json.loads(response)
            if retry_feedback:
                self.logger.info("Successfully regenerated tailored resume with feedback")
            else:
                self.logger.info("Generated tailored resume")
            return result
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse tailored resume response: {e}")
            self.logger.debug(f"Response (first 500 chars): {response[:500]}")
            self.logger.debug(f"Response (last 500 chars): {response[-500:]}")
            raise GroqClientError(f"Invalid JSON response from API: {str(e)}")
    
    def generate_professional_summary(self, resume_text: str, job_description: str) -> str:
        """
        Generate an optimized professional summary for a specific job.
        
        Args:
            resume_text (str): Full resume text
            job_description (str): Target job description
            
        Returns:
            str: Tailored professional summary (2-4 lines)
            
        Raises:
            GroqClientError: If API call fails
        """
        prompt = f"""Based on this professional's background and target job, write an optimal professional summary.

Resume Background:
{resume_text[:1000]}

Target Job Description:
{job_description[:1000]}

Requirements for the summary:
- 3-4 sentences maximum
- Lead with strongest match to job requirements
- Include 2-3 relevant keywords from the job
- Use strong action word in first sentence
- Emphasis quantifiable achievements if any
- Professional tone, ATS-friendly

Return ONLY the summary text, no JSON or additional content."""

        response = self._call_api(prompt, temperature=0.6, max_tokens=300)
        self.logger.info("Generated professional summary")
        return response.strip()
    
    def optimize_bullet_point(self, bullet_point: str, job_keywords: List[str]) -> str:
        """
        AI-assisted bullet point optimization with keyword integration.
        
        Enhances clarity and ATS compatibility while preserving factual accuracy.
        
        Args:
            bullet_point (str): Original bullet point
            job_keywords (List[str]): Relevant keywords from job description
            
        Returns:
            str: Optimized bullet point
            
        Raises:
            GroqClientError: If API call fails
        """
        keywords_str = ", ".join(job_keywords[:5])  # Top 5 keywords
        
        prompt = f"""Optimize this bullet point for ATS systems and job fit.

Original: {bullet_point}

Relevant keywords to integrate naturally: {keywords_str}

Requirements:
- Keep all factual details and metrics
- Add relevant keywords naturally where applicable
- Improve clarity and impact
- Use strong action verb if not present
- Keep under 15 words if possible
- Maintain professional tone

Return ONLY the optimized bullet point, no additional text."""

        response = self._call_api(prompt, temperature=0.5, max_tokens=100)
        self.logger.info("Optimized bullet point")
        return response.strip()
    
    def _call_api(self, prompt: str, temperature: float = 0.7,
                  max_tokens: int = 2048) -> str:
        """
        Make an API call to Groq with error handling and retry logic.
        
        Args:
            prompt (str): The prompt to send
            temperature (float): Temperature for response randomness (0-1)
            max_tokens (int): Maximum tokens in response
            
        Returns:
            str: API response content
            
        Raises:
            GroqClientError: If all retry attempts fail
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                message = self.client.chat.completions.create(
                    model=self.DEFAULT_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": self.RESUME_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.TIMEOUT_SECONDS,
                )
                
                response_content = message.choices[0].message.content
                self.logger.debug(f"API call successful on attempt {attempt + 1}")
                return response_content
                
            except Exception as e:
                self.logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.MAX_RETRIES - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise GroqClientError(
                        f"API call failed after {self.MAX_RETRIES} attempts: {str(e)}"
                    )
    
    def benchmark_model_speed(self) -> Dict[str, float]:
        """
        Quick benchmark to measure API response times.
        
        Useful for monitoring performance degradation.
        
        Returns:
            Dict with timing metrics
        """
        import time
        
        simple_prompt = "Say 'OK' and nothing else."
        
        start = time.time()
        response = self._call_api(simple_prompt, temperature=0.3, max_tokens=10)
        elapsed = time.time() - start
        
        self.logger.info(f"Benchmark complete - Response time: {elapsed:.2f}s")
        
        return {
            'response_time_seconds': round(elapsed, 2),
            'model': self.DEFAULT_MODEL,
            'timestamp': time.time()
        }
