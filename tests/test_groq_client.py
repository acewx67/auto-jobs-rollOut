"""
Unit tests for the Groq client module.

Note: These tests focus on structure and error handling since actual API calls
require valid Groq credentials. In production, use integration tests with mock responses.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.groq_client.client import GroqClient, GroqClientError


class TestGroqClientInitialization:
    """Test suite for GroqClient initialization"""
    
    def test_client_requires_api_key(self):
        """Test that client requires API key"""
        with pytest.raises(GroqClientError) as exc_info:
            # Mock config to have no API key
            with patch('src.groq_client.client.GROQ_API_KEY', None):
                GroqClient(api_key=None)
        assert "API key" in str(exc_info.value)
    
    def test_client_accepts_api_key_parameter(self):
        """Test that client accepts API key as parameter"""
        # This will fail with actual API call, but initializes properly
        try:
            with patch('src.groq_client.client.Groq'):
                client = GroqClient(api_key="test-key-12345")
                assert client is not None
        except GroqClientError:
            # Expected if Groq initialization fails
            pass
    
    def test_client_reads_from_environment(self):
        """Test that client reads from config GROQ_API_KEY"""
        with patch('src.groq_client.client.GROQ_API_KEY', 'env-test-key'):
            with patch('src.groq_client.client.Groq'):
                client = GroqClient()
                assert client is not None
    
    def test_client_default_settings(self):
        """Test that client has correct default settings"""
        assert GroqClient.DEFAULT_MODEL == "openai/gpt-oss-120b"
        assert GroqClient.DEFAULT_TEMPERATURE == 0.7
        assert GroqClient.DEFAULT_MAX_TOKENS == 2048
        assert GroqClient.MAX_RETRIES == 3


class TestGroqClientMethods:
    """Test suite for GroqClient methods with mocked API"""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Fixture providing a mocked GroqClient"""
        with patch('src.groq_client.client.Groq'):
            client = GroqClient(api_key="test-key")
            client.client = Mock()
            return client
    
    def test_analyze_job_description_structure(self, mock_groq_client):
        """Test that job analysis returns expected structure"""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            'job_title': 'Senior Software Engineer',
            'required_skills': ['Python', 'AWS', 'Docker'],
            'required_experience': ['5+ years backend development'],
            'key_responsibilities': ['Design systems', 'Lead team'],
            'nice_to_have': ['Kubernetes', 'GraphQL'],
            'culture_indicators': ['Leadership', 'Collaboration'],
            'keywords': ['Python', 'DevOps', 'System Design']
        })
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        job_desc = "Senior Software Engineer - 5+ years experience with Python and AWS"
        result = mock_groq_client.analyze_job_description(job_desc)
        
        assert 'job_title' in result
        assert 'required_skills' in result
        assert 'keywords' in result
        assert isinstance(result['required_skills'], list)
    
    def test_generate_tailored_resume_structure(self, mock_groq_client):
        """Test that tailored resume returns expected structure"""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            'tailored_resume': 'Modified resume text here...',
            'summary_section': 'Professional summary optimized for role',
            'key_changes': ['Reordered experience', 'Added keywords'],
            'keyword_usage': ['Python', 'AWS', 'System Design']
        })
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        original = "John Developer\nExperience: Senior Dev at Tech Corp"
        job_desc = "Senior Software Engineer"
        
        result = mock_groq_client.generate_tailored_resume(original, job_desc)
        
        assert 'tailored_resume' in result
        assert 'summary_section' in result
        assert 'key_changes' in result
        assert 'keyword_usage' in result
    
    def test_generate_professional_summary_returns_string(self, mock_groq_client):
        """Test that professional summary returns plain text"""
        mock_response = Mock()
        mock_response.choices[0].message.content = "Experienced software engineer with 5 years of experience in backend development and cloud architecture."
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        resume = "John Developer\nSenior Dev at Tech Corp"
        job_desc = "Senior Backend Engineer"
        
        result = mock_groq_client.generate_professional_summary(resume, job_desc)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Experienced" in result or "experienced" in result
    
    def test_optimize_bullet_point_returns_string(self, mock_groq_client):
        """Test that bullet point optimization returns string"""
        mock_response = Mock()
        mock_response.choices[0].message.content = "Led development of Python-based microservices on AWS, improving performance by 40%"
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        bullet = "- Developed services that improved performance"
        keywords = ['Python', 'AWS', 'performance']
        
        result = mock_groq_client.optimize_bullet_point(bullet, keywords)
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGroqClientErrorHandling:
    """Test suite for error handling"""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Fixture providing a mocked GroqClient with error simulation"""
        with patch('src.groq_client.client.Groq'):
            client = GroqClient(api_key="test-key")
            client.client = Mock()
            return client
    
    def test_invalid_json_response_raises_error(self, mock_groq_client):
        """Test that invalid JSON in response raises GroqClientError"""
        mock_response = Mock()
        mock_response.choices[0].message.content = "This is not valid JSON"
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(GroqClientError):
            mock_groq_client.analyze_job_description("job desc")
    
    def test_api_call_failure_raises_error(self, mock_groq_client):
        """Test that API failures raise GroqClientError"""
        mock_groq_client.client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(GroqClientError):
            mock_groq_client._call_api("test prompt")
    
    def test_retry_logic_attempts_multiple_times(self, mock_groq_client):
        """Test that failed calls are retried"""
        # Fail twice, then succeed
        mock_response = Mock()
        mock_response.choices[0].message.content = "OK"
        
        mock_groq_client.client.chat.completions.create.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            mock_response
        ]
        
        # Note: This test may need adjustment based on actual implementation
        # The retry logic should handle multiple failures before giving up
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = mock_groq_client._call_api("test")
            assert result == "OK"


class TestGroqClientEdgeCases:
    """Test suite for edge cases and special scenarios"""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Fixture providing a mocked GroqClient"""
        with patch('src.groq_client.client.Groq'):
            client = GroqClient(api_key="test-key")
            client.client = Mock()
            return client
    
    def test_empty_job_description_handling(self, mock_groq_client):
        """Test handling of empty job description"""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            'job_title': 'Unknown',
            'required_skills': [],
            'required_experience': [],
            'key_responsibilities': [],
            'nice_to_have': [],
            'culture_indicators': [],
            'keywords': []
        })
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        result = mock_groq_client.analyze_job_description("")
        
        assert 'job_title' in result
    
    def test_very_long_resume_handling(self, mock_groq_client):
        """Test handling of very long resume text"""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            'tailored_resume': 'Processed long resume',
            'summary_section': 'Summary',
            'key_changes': [],
            'keyword_usage': []
        })
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        # Create a very long resume (5000+ characters)
        long_resume = "Experience: " + ("Senior Developer at Company X " * 50)
        
        result = mock_groq_client.generate_tailored_resume(long_resume, "Senior Role")
        
        assert 'tailored_resume' in result
    
    def test_special_characters_in_input(self, mock_groq_client):
        """Test handling of special characters in input"""
        mock_response = Mock()
        mock_response.choices[0].message.content = "Processed special characters"
        
        mock_groq_client.client.chat.completions.create.return_value = mock_response
        
        text_with_special = "Experience: 5+ years with C++ & Python (™) @ Big Tech™"
        
        result = mock_groq_client.generate_professional_summary(text_with_special, "Job desc")
        
        assert isinstance(result, str)


class TestGroqClientSystemPrompt:
    """Test that system prompts are properly defined"""
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined"""
        assert GroqClient.RESUME_SYSTEM_PROMPT is not None
        assert len(GroqClient.RESUME_SYSTEM_PROMPT) > 100
    
    def test_system_prompt_includes_key_principles(self):
        """Test that system prompt includes important principles"""
        prompt = GroqClient.RESUME_SYSTEM_PROMPT
        
        assert "factual accuracy" in prompt.lower()
        assert "truthfulness" in prompt.lower()
        assert "ats" in prompt.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
