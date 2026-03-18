"""
Tests for the resume tailoring pipeline.

Focus on integration, error handling, and workflow validation.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core.resume_tailor import (
    TailorPipeline, TailorPipelineError, PipelineConfig
)


class TestTailorPipeline:
    """Test suite for TailorPipeline"""
    
    @pytest.fixture
    def mock_pipeline(self, tmp_path):
        """Fixture providing a mocked TailorPipeline"""
        with patch('src.core.resume_tailor.ResumeParser'), \
             patch('src.core.resume_tailor.ATSOptimizer'), \
             patch('src.core.resume_tailor.GroqClient'):
            pipeline = TailorPipeline(output_dir=str(tmp_path))
            
            # Mock the components
            pipeline.parser = Mock()
            pipeline.optimizer = Mock()
            pipeline.groq_client = Mock()
            
            return pipeline
    
    def test_pipeline_initialization(self, mock_pipeline):
        """Test that pipeline initializes correctly"""
        assert mock_pipeline is not None
        assert mock_pipeline.parser is not None
        assert mock_pipeline.optimizer is not None
        assert mock_pipeline.groq_client is not None
    
    def test_pipeline_requires_groq_key(self):
        """Test that pipeline requires Groq API key"""
        with patch('src.core.resume_tailor.GroqClient') as mock_groq:
            mock_groq.side_effect = Exception("API key required")
            
            with pytest.raises(TailorPipelineError):
                TailorPipeline()
    
    def test_load_job_description_from_string(self, mock_pipeline):
        """Test loading job description from string input"""
        job_text = "Senior Software Engineer - 5+ years experience"
        
        result = mock_pipeline._load_job_description(job_text)
        
        assert result == job_text
    
    def test_load_job_description_from_file(self, mock_pipeline, tmp_path):
        """Test loading job description from file"""
        job_file = tmp_path / "job.txt"
        job_text = "Senior Software Engineer position"
        job_file.write_text(job_text)
        
        result = mock_pipeline._load_job_description(str(job_file))
        
        assert result == job_text
    
    def test_load_job_description_missing_file_raises_error(self, mock_pipeline):
        """Test that missing file raises error"""
        with pytest.raises(TailorPipelineError):
            mock_pipeline._load_job_description("/nonexistent/job.txt")
    
    def test_load_job_description_empty_raises_error(self, mock_pipeline):
        """Test that empty description raises error"""
        with pytest.raises(TailorPipelineError):
            mock_pipeline._load_job_description("")
    
    def test_extract_tailored_text_from_response(self, mock_pipeline):
        """Test extracting tailored resume from response"""
        response = {
            'tailored_resume': 'John Developer\nSenior Engineer...',
            'key_changes': [],
        }
        
        result = mock_pipeline._extract_tailored_text(response)
        
        assert 'John Developer' in result
    
    def test_extract_tailored_text_missing_field_raises_error(self, mock_pipeline):
        """Test that missing 'tailored_resume' field raises error"""
        response = {'key_changes': []}
        
        with pytest.raises(TailorPipelineError):
            mock_pipeline._extract_tailored_text(response)
    
    def test_save_output_creates_file(self, mock_pipeline, tmp_path):
        """Test that output is saved to file"""
        mock_pipeline.output_dir = tmp_path
        
        content = "Tailored Resume Content"
        output_file = mock_pipeline._save_output(content, "txt", "resume.pdf")
        
        assert output_file.exists()
        assert output_file.read_text() == content
    
    def test_save_output_json_format(self, mock_pipeline, tmp_path):
        """Test saving output in JSON format"""
        mock_pipeline.output_dir = tmp_path
        
        content = "Tailored Resume"
        output_file = mock_pipeline._save_output(content, "json", "resume.pdf")
        
        assert output_file.exists()
        assert output_file.suffix == ".json"
        
        data = json.loads(output_file.read_text())
        assert 'tailored_resume' in data
        assert data['tailored_resume'] == content
    
    def test_tailor_complete_workflow(self, mock_pipeline):
        """Test complete tailor workflow with mocked components"""
        # Mock all the returns
        mock_pipeline.parser.parse.return_value = {
            'normalized_text': 'Original resume text',
            'sections': {'experience': 'Work exp'},
            'character_count': 1000,
        }
        
        mock_pipeline.optimizer.calculate_ats_score.side_effect = [
            {
                'overall_score': 60,
                'keyword_score': 30,
                'format_score': 15,
                'content_score': 10,
                'readability_score': 5,
                'matched_keywords': ['Python', 'AWS'],
                'missing_keywords': ['Kubernetes', 'Docker'],
            },
            {
                'overall_score': 75,
                'keyword_score': 40,
                'format_score': 18,
                'content_score': 12,
                'readability_score': 5,
                'matched_keywords': ['Python', 'AWS', 'Kubernetes', 'Docker'],
                'missing_keywords': [],
            }
        ]
        
        mock_pipeline.optimizer.format_for_ats.return_value = 'Formatted resume'
        mock_pipeline.optimizer.preserve_metrics.return_value = ['5 years', '40% improvement']
        mock_pipeline.optimizer.generate_optimization_report.return_value = {
            'score': 75,
            'recommendations': []
        }
        
        mock_pipeline.groq_client.analyze_job_description.return_value = {
            'job_title': 'Senior Engineer',
            'required_skills': ['Python', 'AWS'],
        }
        
        mock_pipeline.groq_client.generate_tailored_resume.return_value = {
            'tailored_resume': 'Tailored content',
            'key_changes': ['Reordered experience'],
        }
        
        result = mock_pipeline.tailor("resume.pdf", "Senior Software Engineer position")
        
        assert result['success'] is True
        assert result['original_ats_score'] == 60
        assert result['final_ats_score'] == 75
        assert result['ats_improvement'] == 15
        assert 'tailored_resume' in result
        assert 'output_file' in result


class TestPipelineConfig:
    """Test suite for PipelineConfig"""
    
    def test_config_directories_defined(self):
        """Test that config has required directories defined"""
        assert PipelineConfig.INPUT_RESUME_DIR
        assert PipelineConfig.OUTPUT_RESUME_DIR
        assert PipelineConfig.JOB_DESCRIPTIONS_DIR
    
    def test_config_supported_formats(self):
        """Test that config specifies supported formats"""
        assert 'txt' in PipelineConfig.SUPPORTED_FORMATS
        assert 'json' in PipelineConfig.SUPPORTED_FORMATS
    
    def test_initialize_directories(self, tmp_path):
        """Test that directories are created"""
        # Temporarily override paths
        original_input = PipelineConfig.INPUT_RESUME_DIR
        original_output = PipelineConfig.OUTPUT_RESUME_DIR
        
        try:
            PipelineConfig.INPUT_RESUME_DIR = str(tmp_path / "input")
            PipelineConfig.OUTPUT_RESUME_DIR = str(tmp_path / "output")
            PipelineConfig.JOB_DESCRIPTIONS_DIR = str(tmp_path / "jobs")
            PipelineConfig.REPORTS_DIR = str(tmp_path / "reports")
            PipelineConfig.LOGS_DIR = str(tmp_path / "logs")
            
            PipelineConfig.initialize_directories()
            
            assert Path(PipelineConfig.INPUT_RESUME_DIR).exists()
            assert Path(PipelineConfig.OUTPUT_RESUME_DIR).exists()
            assert Path(PipelineConfig.JOB_DESCRIPTIONS_DIR).exists()
            
        finally:
            # Restore original values
            PipelineConfig.INPUT_RESUME_DIR = original_input
            PipelineConfig.OUTPUT_RESUME_DIR = original_output


class TestBatchTailoring:
    """Test suite for batch tailoring functionality"""
    
    @pytest.fixture
    def mock_pipeline(self, tmp_path):
        """Fixture providing a mocked pipeline"""
        with patch('src.core.resume_tailor.ResumeParser'), \
             patch('src.core.resume_tailor.ATSOptimizer'), \
             patch('src.core.resume_tailor.GroqClient'):
            pipeline = TailorPipeline(output_dir=str(tmp_path))
            pipeline.parser = Mock()
            pipeline.optimizer = Mock()
            pipeline.groq_client = Mock()
            return pipeline
    
    def test_batch_tailor_requires_valid_directory(self, mock_pipeline):
        """Test that batch tailoring requires valid job directory"""
        with pytest.raises(TailorPipelineError):
            mock_pipeline.batch_tailor("resume.pdf", "/nonexistent/jobs")
    
    def test_batch_tailor_processes_multiple_jobs(self, mock_pipeline, tmp_path):
        """Test that batch tailoring processes multiple jobs"""
        # Create job files
        jobs_dir = tmp_path / "jobs"
        jobs_dir.mkdir()
        
        job1 = jobs_dir / "job1.txt"
        job1.write_text("Senior Backend Engineer")
        
        job2 = jobs_dir / "job2.txt"
        job2.write_text("Senior Frontend Engineer")
        
        # Mock tailor method
        mock_pipeline.tailor = Mock(return_value={
            'success': True,
            'final_ats_score': 75,
            'ats_improvement': 15,
        })
        
        result = mock_pipeline.batch_tailor("resume.pdf", str(jobs_dir))
        
        assert result['total_jobs'] == 2
        assert result['successful'] == 2
        assert result['failed'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
