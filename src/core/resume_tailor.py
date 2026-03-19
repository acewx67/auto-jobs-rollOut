"""
Core resume tailoring pipeline - Main orchestration layer.

Coordinates all components:
- Resume parsing
- Job description analysis
- ATS optimization
- AI-powered tailoring
- Output generation

This is the main entry point for resume tailoring operations.
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime

from src.core.resume_parser import ResumeParser, ResumeParseError
from src.utils.ats_optimizer import ATSOptimizer
from src.utils.latex_generator import LatexResumeGenerator, LatexGeneratorError
from src.groq_client.client import GroqClient, GroqClientError

logger = logging.getLogger(__name__)


class TailorPipelineError(Exception):
    """Custom exception for pipeline errors"""
    pass


class TailorPipeline:
    """
    Main orchestration for resume tailoring.
    
    Manages the complete workflow:
    1. Parse resume file (PDF/DOCX)
    2. Analyze job description with Groq
    3. Calculate initial ATS score
    4. Generate AI-tailored resume
    5. Apply ATS optimizations
    6. Calculate final ATS score
    7. Generate comprehensive report
    8. Export tailored resume
    
    Example usage:
        pipeline = TailorPipeline()
        result = pipeline.tailor(resume_path, job_desc, output_format="pdf")
        print(f"ATS Score: {result['final_ats_score']}")
    """
    
    def __init__(self, groq_api_key: Optional[str] = None, 
                 output_dir: str = "data/resumes/output"):
        """
        Initialize the tailoring pipeline.
        
        Args:
            groq_api_key (str, optional): Groq API key. If not provided,
                                         uses GROQ_API_KEY environment variable
            output_dir (str): Directory to save tailored resumes
        """
        try:
            self.parser = ResumeParser()
            self.optimizer = ATSOptimizer()
            self.groq_client = GroqClient(api_key=groq_api_key)
            self.generator = LatexResumeGenerator()
            
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("TailorPipeline initialized successfully")
            
        except Exception as e:
            raise TailorPipelineError(f"Failed to initialize pipeline: {str(e)}")
    
    def tailor(self, resume_path: str, job_description: str,
               output_format: str = "txt") -> Dict[str, any]:
        """
        Main entry point: Tailor a resume for a specific job.
        
        Args:
            resume_path (str): Path to resume file (PDF or DOCX)
            job_description (str): Job posting text or path to job file
            output_format (str): Output format ("txt", "json", "pdf", "docx")
            
        Returns:
            Dict containing:
                - 'success': Boolean indicating if process succeeded
                - 'original_ats_score': ATS score before tailoring
                - 'tailored_resume': Full tailored resume text
                - 'final_ats_score': ATS score after tailoring
                - 'ats_improvement': Percentage improvement in score
                - 'key_changes': List of modifications made
                - 'matched_keywords': Keywords from job found in resume
                - 'missing_keywords': Important keywords still missing
                - 'metrics_preserved': Important metrics found in resume
                - 'output_file': Path to saved output file
                - 'report': Comprehensive optimization report
                - 'timestamp': Processing timestamp
                
        Raises:
            TailorPipelineError: If any step in the pipeline fails
        """
        start_time = datetime.now()
        self.logger.info(f"Starting tailor pipeline for resume: {resume_path}")
        
        try:
            # Step 1: Parse resume file
            self.logger.info("Step 1/6: Parsing resume...")
            parsed_resume = self._parse_resume(resume_path)
            
            # Step 2: Load job description (file or string)
            self.logger.info("Step 2/6: Loading job description...")
            job_desc = self._load_job_description(job_description)
            
            # Step 3: Calculate initial ATS score
            self.logger.info("Step 3/6: Calculating initial ATS score...")
            initial_ats = self.optimizer.calculate_ats_score(
                self._flatten_structured_resume(parsed_resume),
                job_desc
            )
            
            # Step 4: Analyze job with Groq
            self.logger.info("Step 4/6: Analyzing job description with AI...")
            job_analysis = self.groq_client.analyze_job_description(job_desc)
            
            # Step 5/6: Generating tailored resume with AI...
            self.logger.info("Step 5/6: Generating tailored resume with AI...")
            
            # Initial generation: Pass the structured parsed_resume (name, contact, experience, etc.)
            tailored_response = self.groq_client.generate_tailored_resume(
                parsed_resume, 
                job_desc,
                job_analysis
            )
            
            # Validation: Ensure core sections are present in the JSON
            required_keys = ['experience', 'education', 'projects', 'skills', 'summary']
            missing_keys = [k for k in required_keys if not tailored_response.get(k)]
            
            if missing_keys:
                self.logger.warning(f"Tailored JSON is missing essential keys: {', '.join(missing_keys)}. Retrying once...")
                feedback = f"The previous attempt was missing the following structured sections: {', '.join(missing_keys)}. " \
                           f"Please return the FULL tailored resume in the requested JSON format."
                
                tailored_response = self.groq_client.generate_tailored_resume(
                    parsed_resume, 
                    job_desc,
                    job_analysis,
                    retry_feedback=feedback
                )
            
            # Create a plain text version for ATS scoring
            tailored_text = self._flatten_structured_resume(tailored_response)
            
            # Apply ATS formatting (for the text version used in scoring/report)
            tailored_text = self.optimizer.format_for_ats(tailored_text)
            
            # Step 6: Calculate final ATS score
            self.logger.info("Step 6/6: Calculating final ATS score...")
            final_ats = self.optimizer.calculate_ats_score(tailored_text, job_desc)
            
            # Calculate improvement
            improvement = final_ats['overall_score'] - initial_ats['overall_score']
            improvement_pct = (improvement / initial_ats['overall_score'] * 100) if initial_ats['overall_score'] > 0 else 0
            
            # Generate report
            report = self.optimizer.generate_optimization_report(
                final_ats,
                tailored_text,
                job_desc
            )
            
            # Save output
            output_file = self._save_output(tailored_response, parsed_resume, job_desc, output_format, self.output_dir)
            
            # Compile result
            result = {
                'success': True,
                'original_ats_score': initial_ats['overall_score'],
                'final_ats_score': final_ats['overall_score'],
                'ats_improvement': improvement,
                'ats_improvement_percentage': round(improvement_pct, 1),
                'tailored_resume': tailored_text,
                'key_changes': tailored_response.get('key_changes', []),
                'matched_keywords': final_ats['matched_keywords'],
                'missing_keywords': final_ats['missing_keywords'],
                'metrics_preserved': self.optimizer.preserve_metrics(tailored_text),
                'output_file': str(output_file),
                'report': report,
                'job_analysis': job_analysis,
                'timestamp': datetime.now().isoformat(),
                'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
            }
            
            self.logger.info(f"Pipeline complete. ATS Score: {initial_ats['overall_score']} → {final_ats['overall_score']}")
            return result
            
        except (ResumeParseError, GroqClientError) as e:
            self.logger.error(f"Pipeline error: {str(e)}")
            raise TailorPipelineError(f"Tailoring failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected pipeline error: {str(e)}")
            raise TailorPipelineError(f"Unexpected error: {str(e)}")
    
    def _parse_resume(self, resume_path: str) -> Dict:
        """Parse resume file and return rich AI data structure"""
        # Step 1.1: Basic text extraction (needed for the AI to read)
        basic_parsed = self.parser.parse(resume_path)
        
        # Step 1.2: AI-powered rich structure extraction
        self.logger.info("Extracting rich resume structure with AI...")
        ai_parsed = self.groq_client.parse_resume(basic_parsed['raw_text'])
        
        # Ensure we keep the normalized text for the optimizer if needed
        ai_parsed['normalized_text'] = basic_parsed['normalized_text']
        ai_parsed['source_path'] = resume_path
        
        self.logger.info(f"AI-Parsed resume for: {ai_parsed.get('name', 'Unknown')}")
        return ai_parsed
    
    def _load_job_description(self, job_input: str) -> str:
        """Load job description from string or file."""
        job_path = Path(job_input)
        if job_path.exists() and job_path.is_file():
            content = job_path.read_text(encoding='utf-8')
            if not content.strip():
                raise TailorPipelineError("Job description file is empty")
            return content
        
        if not job_input or not job_input.strip():
            raise TailorPipelineError("Job description is empty")
        
        return job_input
    
    def _flatten_structured_resume(self, data: Dict) -> str:
        """Convert structured resume back to plain text for ATS scoring"""
        text = [f"{data.get('name', '')}\n"]
        
        if data.get('summary'):
            text.append(f"SUMMARY\n{data['summary']}\n")
            
        if data.get('experience'):
            text.append("EXPERIENCE")
            for exp in data['experience']:
                text.append(f"{exp.get('company', '')} - {exp.get('role', '')}")
                text.append('\n'.join(exp.get('achievements', [])))
            text.append("")
                
        if data.get('projects'):
            text.append("PROJECTS")
            for proj in data['projects']:
                text.append(f"{proj.get('title', '')} ({proj.get('tech_stack', '')})")
                text.append('\n'.join(proj.get('description', [])))
            text.append("")
                
        if data.get('skills'):
            text.append("TECHNICAL SKILLS")
            for cat, items in data['skills'].items():
                text.append(f"{cat}: {', '.join(items) if isinstance(items, list) else items}")
            text.append("")
            
        return '\n'.join(text)

    def _compile_pdf(self, latex_code: str, output_path: str) -> str:
        """Helper to compile LaTeX code directly to PDF"""
        output_dir = Path(output_path).parent
        output_filename = Path(output_path).name
        tex_file_path = output_dir / f"{output_filename}.tex"
        pdf_file_path = output_dir / f"{output_filename}.pdf"
        
        try:
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(latex_code)
            
            for _ in range(2):
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(output_dir), str(tex_file_path)],
                    check=True, capture_output=True, timeout=120
                )
            return str(pdf_file_path)
        except Exception as e:
            self.logger.error(f"Direct PDF compilation failed: {e}")
            return ""

    def _save_output(self, content: Dict, original_data: Dict, job_desc: str, 
                    output_format: str, result_dir: Path) -> Path:
        """Save tailored resume in specified format."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(original_data.get('source_path', 'resume')).stem
        
        if output_format == "docx":
            output_path = result_dir / f"{source_name}_tailored_{timestamp}.docx"
            txt_content = self._flatten_structured_resume(content)
            self._save_as_docx(txt_content, output_path)
            return output_path
            
        elif output_format == "json":
            output_path = result_dir / f"{source_name}_tailored_{timestamp}.json"
            output_path.write_text(json.dumps(content, indent=2), encoding='utf-8')
            return output_path
            
        elif output_format == 'latex':
            latex_code = self.generator.generate_from_structure(content)
            output_path = result_dir / f"{source_name}_tailored_{timestamp}.tex"
            output_path.write_text(latex_code, encoding='utf-8')
            return output_path
            
        elif output_format == "latex-pdf":
            output_path_base = result_dir / f"{source_name}_tailored_{timestamp}"
            latex_code = self.generator.generate_from_structure(content)
            pdf_path = self._compile_pdf(latex_code, str(output_path_base))
            if pdf_path:
                return Path(pdf_path)
            return output_path_base.with_suffix('.tex')
            
        else:  # Default to txt
            txt_content = self._flatten_structured_resume(content)
            output_path = result_dir / f"{source_name}_tailored_{timestamp}.txt"
            output_path.write_text(txt_content, encoding='utf-8')
            return output_path

    def _save_as_docx(self, content: str, output_path: Path) -> None:
        """Save resume content as DOCX."""
        try:
            from docx import Document
            from docx.shared import Pt, Inches
        except ImportError:
            self.logger.warning("python-docx not installed, saving as TXT instead")
            output_path.with_suffix('.txt').write_text(content, encoding='utf-8')
            return
        
        doc = Document()
        for section in doc.sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
        
        for line in content.split('\n'):
            line_stripped = line.strip()
            if not line_stripped: continue
            
            if (line_stripped.isupper() and len(line_stripped) < 40):
                doc.add_heading(line_stripped, level=1)
            elif line_stripped.startswith('•'):
                doc.add_paragraph(line_stripped[1:].strip(), style='List Bullet')
            else:
                doc.add_paragraph(line_stripped)
        
        doc.save(str(output_path))


class PipelineConfig:
    """Configuration for tailoring pipeline"""
    
    # Resume storage paths
    INPUT_RESUME_DIR = "data/resumes/input"
    OUTPUT_RESUME_DIR = "data/resumes/output"
    JOB_DESCRIPTIONS_DIR = "data/job_posts"
    
    # Output paths
    REPORTS_DIR = "data/reports"
    LOGS_DIR = "logs"
    
    # Pipeline settings
    DEFAULT_OUTPUT_FORMAT = "txt"
    SUPPORTED_FORMATS = ["txt", "json", "pdf", "docx", "latex-pdf"]
    
    @classmethod
    def initialize_directories(cls):
        """Create required directories if they don't exist"""
        directories = [
            cls.INPUT_RESUME_DIR,
            cls.OUTPUT_RESUME_DIR,
            cls.JOB_DESCRIPTIONS_DIR,
            cls.REPORTS_DIR,
            cls.LOGS_DIR,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info("Pipeline directories initialized")
