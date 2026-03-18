"""
Unit tests for the ATS optimizer module.

Tests cover:
- Keyword extraction
- ATS score calculation
- Formatting analysis
- Content completeness scoring
- Readability scoring
- Metric preservation
"""

import pytest
from src.utils.ats_optimizer import ATSOptimizer


class TestATSOptimizer:
    """Test suite for ATSOptimizer class"""
    
    @pytest.fixture
    def optimizer(self):
        """Fixture providing an ATSOptimizer instance"""
        return ATSOptimizer()
    
    @pytest.fixture
    def sample_job_description(self):
        """Sample job description for keyword extraction"""
        return """
        Senior Software Engineer
        
        We are looking for an experienced Senior Software Engineer to join our team.
        
        Requirements:
        - 5+ years of Python programming experience
        - Strong knowledge of AWS and cloud architecture
        - Experience with Docker and Kubernetes
        - Excellent problem-solving skills
        - Experience with microservices architecture
        - Knowledge of SQL and NoSQL databases
        - Git version control expertise
        - Agile/Scrum experience
        
        Responsibilities:
        - Design and implement scalable backend systems
        - Lead technical discussions and code reviews
        - Mentor junior developers
        - Collaborate with product and design teams
        - Optimize application performance
        """
    
    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume text for testing"""
        return """
        JOHN DEVELOPER
        john.dev@email.com | (555) 123-4567 | linkedin.com/in/johndev
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 6 years of experience building scalable applications.
        
        WORK EXPERIENCE
        Senior Software Engineer at TechCorp | 2021-2023
        - Led development of microservices architecture using Python and AWS
        - Managed Docker and Kubernetes deployments for 10+ services
        - Improved API performance by 40% through optimization
        - Mentored 3 junior developers on best practices
        
        Software Engineer at DataSystems | 2019-2021
        - Developed REST APIs using Python and Flask
        - Worked with SQL and NoSQL databases (PostgreSQL, MongoDB)
        - Used Git for version control and participated in code reviews
        - Implemented Agile/Scrum workflows in team
        
        EDUCATION
        Bachelor of Science in Computer Science | State University | 2019
        
        SKILLS
        Languages: Python, JavaScript, SQL
        Cloud: AWS, Google Cloud Platform
        Tools: Docker, Kubernetes, Git, Jenkins
        Databases: PostgreSQL, MongoDB, Redis
        Other: Microservices, REST APIs, Linux
        """
    
    def test_optimizer_initialization(self, optimizer):
        """Test that optimizer initializes correctly"""
        assert optimizer is not None
        assert hasattr(optimizer, 'extract_keywords')
        assert hasattr(optimizer, 'calculate_ats_score')
        assert len(optimizer.STRONG_ACTION_VERBS) > 0
    
    def test_extract_keywords_returns_dict(self, optimizer, sample_job_description):
        """Test that keyword extraction returns a dictionary"""
        keywords = optimizer.extract_keywords(sample_job_description)
        
        assert isinstance(keywords, dict)
        assert len(keywords) > 0
        assert len(keywords) <= 30  # Should limit to top 30
    
    def test_extract_keywords_finds_technical_terms(self, optimizer, sample_job_description):
        """Test that technical terms are extracted"""
        keywords = optimizer.extract_keywords(sample_job_description)
        
        # Check for expected technical keywords (lowercase)
        keywords_lower = {k.lower(): v for k, v in keywords.items()}
        assert any('python' in k for k in keywords_lower.keys())
        assert any('aws' in k or 'cloud' in k for k in keywords_lower.keys())
    
    def test_calculate_ats_score_returns_dict_with_required_keys(self, optimizer, sample_resume_text, sample_job_description):
        """Test that ATS score returns all required output keys"""
        score = optimizer.calculate_ats_score(sample_resume_text, sample_job_description)
        
        required_keys = [
            'overall_score', 'keyword_score', 'format_score',
            'content_score', 'readability_score', 'matched_keywords',
            'missing_keywords'
        ]
        
        for key in required_keys:
            assert key in score
    
    def test_calculate_ats_score_ranges(self, optimizer, sample_resume_text, sample_job_description):
        """Test that ATS scores are within valid ranges"""
        score = optimizer.calculate_ats_score(sample_resume_text, sample_job_description)
        
        assert 0 <= score['overall_score'] <= 100
        assert 0 <= score['keyword_score'] <= 50
        assert 0 <= score['format_score'] <= 20
        assert 0 <= score['content_score'] <= 15
        assert 0 <= score['readability_score'] <= 15
    
    def test_matched_keywords_are_found(self, optimizer, sample_resume_text, sample_job_description):
        """Test that matched keywords are actually in the resume"""
        score = optimizer.calculate_ats_score(sample_resume_text, sample_job_description)
        
        resume_lower = sample_resume_text.lower()
        for keyword in score['matched_keywords']:
            assert keyword.lower() in resume_lower
    
    def test_format_for_ats_removes_special_characters(self, optimizer):
        """Test that format_for_ats removes problematic characters"""
        text = """
        Modified text with "smart quotes" and em-dashes–check it
        Special Unicode: ñ, é, ü, →, ✓
        """
        
        formatted = optimizer.format_for_ats(text)
        
        # Should remove Unicode special characters
        assert 'ñ' not in formatted
        assert '✓' not in formatted
        # But keep basic formatting
        assert formatted.strip()  # Not completely empty
    
    def test_format_for_ats_standardizes_spacing(self, optimizer):
        """Test that format_for_ats normalizes whitespace"""
        text = "Text    with     multiple     spaces\n\n\nMultiple newlines"
        
        formatted = optimizer.format_for_ats(text)
        
        assert "    " not in formatted  # No multiple spaces
        assert "\n\n\n" not in formatted  # No triple newlines
    
    def test_preserve_metrics_finds_percentages(self, optimizer):
        """Test that metrics are preserved"""
        text = "Improved performance by 40% while reducing costs by 25%"
        
        metrics = optimizer.preserve_metrics(text)
        
        assert len(metrics) >= 2
        assert any('40' in m for m in metrics)
        assert any('25' in m for m in metrics)
    
    def test_preserve_metrics_finds_dollar_amounts(self, optimizer):
        """Test that dollar amounts are preserved"""
        text = "Managed budget of $2,500,000 and saved $150,000 annually"
        
        metrics = optimizer.preserve_metrics(text)
        
        assert len(metrics) > 0
        assert any('2,500' in m or '2500' in m.replace(',', '') for m in metrics)
    
    def test_preserve_metrics_finds_time_periods(self, optimizer):
        """Test that time periods are preserved"""
        text = "Led team from 2019 to 2022 and managed Q3 2021 release"
        
        metrics = optimizer.preserve_metrics(text)
        
        assert any('2019' in m or '2022' in m for m in metrics)
    
    def test_optimize_bullet_point_preserves_metrics(self, optimizer, sample_job_description):
        """Test that bullet point optimization preserves metrics"""
        bullet = "- Improved system performance by 35% and reduced latency"
        job_keywords = optimizer.extract_keywords(sample_job_description)
        
        optimized = optimizer.optimize_bullet_point(bullet, job_keywords)
        
        assert '35%' in optimized
        assert optimized  # Not empty
    
    def test_score_formatting_penalizes_excessive_special_chars(self, optimizer):
        """Test that formatting score accounts for special characters"""
        dirty_text = "Text with ™ ® © € ¥ symbols throughout ♦ ★ ◆"
        
        score = optimizer._score_formatting(dirty_text)
        
        assert score < 100  # Should penalize
        assert score >= 0
    
    def test_score_formatting_handles_line_spacing(self, optimizer):
        """Test formatting score considers line spacing"""
        sparse_text = "Line 1\n\n\n\nLine 2\n\n\n\nLine 3"
        
        score = optimizer._score_formatting(sparse_text)
        
        assert score >= 0
        assert score <= 100
    
    def test_score_content_completeness_with_sections(self, optimizer):
        """Test content scoring with resume sections"""
        sections = {
            'contact': 'john@email.com',
            'summary': 'Senior developer',
            'experience': 'Tech Corp, 2020-2023',
            'education': 'BS Computer Science',
            'skills': 'Python, AWS'
        }
        
        score = optimizer._score_content_completeness(sections)
        
        assert score >= 80  # Should be high for complete resume
        assert score <= 100
    
    def test_score_content_completeness_missing_sections(self, optimizer):
        """Test content scoring with incomplete resume"""
        sections = {'experience': 'Tech Corp'}
        
        score = optimizer._score_content_completeness(sections)
        
        assert score < 50  # Should be lower for incomplete
        assert score >= 0
    
    def test_generate_optimization_report_structure(self, optimizer, sample_resume_text, sample_job_description):
        """Test that optimization report has required structure"""
        ats_score = optimizer.calculate_ats_score(sample_resume_text, sample_job_description)
        report = optimizer.generate_optimization_report(ats_score, sample_resume_text, sample_job_description)
        
        assert 'score' in report
        assert 'breakdown' in report
        assert 'matched_keywords' in report
        assert 'recommendations' in report
        assert 'metrics_preserved' in report
    
    def test_strong_action_verbs_populated(self, optimizer):
        """Test that strong action verbs are defined"""
        assert len(optimizer.STRONG_ACTION_VERBS) > 20
        assert 'achieved' in optimizer.STRONG_ACTION_VERBS
        assert 'developed' in optimizer.STRONG_ACTION_VERBS
    
    def test_score_readability_counts_action_verbs(self, optimizer):
        """Test that readability score recognizes action verbs"""
        text_with_verbs = """
        - Achieved 40% improvement in performance
        - Developed microservices architecture
        - Led team of 5 engineers
        - Implemented automated testing
        """
        
        score = optimizer._score_readability(text_with_verbs)
        
        assert score >= 50  # Should be decent with action verbs
        assert score <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
