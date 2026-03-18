"""
ATS (Applicant Tracking System) optimization module.

Provides comprehensive tools for:
- Extracting keywords from job descriptions
- Analyzing resume for ATS compatibility
- Optimizing resume formatting for ATS systems
- Generating ATS compatibility scores
- Rewriting bullet points while preserving metrics

ATS systems scan resumes for:
1. Keyword relevance (50% of score)
2. Formatting compatibility (20% of score)
3. Content completeness (15% of score)
4. Readability & structure (15% of score)
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter

logger = logging.getLogger(__name__)


class ATSOptimizer:
    """
    Comprehensive ATS optimization and scoring system.
    
    Analyzes resume and job description to:
    - Extract relevant keywords
    - Calculate ATS compatibility score
    - Suggest formatting improvements
    - Optimize content for ATS systems
    """
    
    # Common ATS formatting issues
    ATS_COMPATIBLE_FONTS = ['Arial', 'Calibri', 'Courier New', 'Helvetica', 'Times New Roman']
    ATS_UNSAFE_ELEMENTS = ['images', 'tables', 'graphics', 'custom fonts', 'colors', 'headers/footers']
    
    # Keywords that ATS systems look for
    STRONG_ACTION_VERBS = [
        'achieved', 'accelerated', 'accomplished', 'advanced', 'amplified',
        'cultivated', 'developed', 'designed', 'directed', 'discovered',
        'engineered', 'enhanced', 'established', 'generated', 'grew',
        'guided', 'implemented', 'improved', 'increased', 'innovated',
        'launched', 'led', 'managed', 'optimized', 'pioneered',
        'produced', 'programmed', 'promoted', 'reduced', 'transformed'
    ]
    
    # Resume sections that ATS prioritizes
    PRIORITY_SECTIONS = ['experience', 'skills', 'education', 'summary']
    
    def __init__(self):
        """Initialize the ATS optimizer"""
        self.logger = logging.getLogger(__name__)
    
    def extract_keywords(self, job_description: str, top_n: int = 30) -> Dict[str, int]:
        """
        Extract and rank keywords from job description.
        
        Prioritizes:
        - Technical skills
        - Industry terms
        - Action verbs
        - Specific tools/frameworks
        
        Args:
            job_description (str): Full job description text
            top_n (int): Number of top keywords to return
            
        Returns:
            Dict[keyword, frequency]: Keywords ranked by frequency
        """
        text = job_description.lower()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'is',
            'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'we', 'you', 'he', 'she', 'it', 'they', 'this', 'that'
        }
        
        # Extract words (2+ characters)
        words = re.findall(r'\b[a-z]{2,}\b', text)
        
        # Filter out stop words
        keywords = [w for w in words if w not in stop_words]
        
        # Look for technical terms (capitalized in original or common tech terms)
        tech_pattern = r'\b[A-Z][a-z]+([\s+][A-Z][a-z]+)*\b'
        tech_terms = re.findall(tech_pattern, job_description)
        keywords.extend([t.lower() for t in tech_terms])
        
        # Count frequencies
        keyword_freq = Counter(keywords)
        
        # Return top N keywords
        top_keywords = dict(keyword_freq.most_common(top_n))
        
        self.logger.debug(f"Extracted {len(top_keywords)} keywords from job description")
        return top_keywords
    
    def calculate_ats_score(self, resume_text: str, job_description: str, 
                           resume_sections: Optional[Dict] = None) -> Dict[str, any]:
        """
        Calculate comprehensive ATS compatibility score (0-100).
        
        Scoring breakdown:
        - Keyword matching: 50 points
        - Formatting compatibility: 20 points
        - Content completeness: 15 points
        - Readability & structure: 15 points
        
        Args:
            resume_text (str): Normalized resume text
            job_description (str): Job description text
            resume_sections (Dict, optional): Parsed resume sections
            
        Returns:
            Dict containing:
                - 'overall_score': Total ATS score (0-100)
                - 'keyword_score': Keyword matching score
                - 'format_score': Formatting compatibility score
                - 'content_score': Content completeness score
                - 'readability_score': Readability & structure score
                - 'missing_keywords': Keywords in job that aren't in resume
                - 'matched_keywords': Keywords found in resume
        """
        scores = {}
        
        # 1. Keyword matching (50 points)
        job_keywords = self.extract_keywords(job_description)
        keyword_score, matched, missing = self._score_keywords(resume_text, job_keywords)
        scores['keyword_score'] = keyword_score * 0.5  # Max 50
        scores['matched_keywords'] = matched
        scores['missing_keywords'] = missing
        
        # 2. Format compatibility (20 points)
        format_score = self._score_formatting(resume_text)
        scores['format_score'] = format_score * 0.2  # Max 20
        
        # 3. Content completeness (15 points)
        content_score = self._score_content_completeness(resume_sections or {})
        scores['content_score'] = content_score * 0.15  # Max 15
        
        # 4. Readability & structure (15 points)
        readability_score = self._score_readability(resume_text)
        scores['readability_score'] = readability_score * 0.15  # Max 15
        
        # Calculate overall score
        overall_score = round(
            scores['keyword_score'] + 
            scores['format_score'] + 
            scores['content_score'] + 
            scores['readability_score']
        )
        
        self.logger.info(f"ATS Score calculated: {overall_score}/100")
        
        return {
            'overall_score': min(overall_score, 100),
            'keyword_score': round(scores['keyword_score'], 1),
            'format_score': round(scores['format_score'], 1),
            'content_score': round(scores['content_score'], 1),
            'readability_score': round(scores['readability_score'], 1),
            'matched_keywords': scores['matched_keywords'],
            'missing_keywords': scores['missing_keywords'],
        }
    
    def _score_keywords(self, resume_text: str, job_keywords: Dict[str, int]) -> Tuple[float, List, List]:
        """
        Score keyword matching between resume and job description.
        
        Returns score (0-100), matched keywords, and missing keywords.
        """
        resume_lower = resume_text.lower()
        matched_keywords = []
        missing_keywords = []
        
        for keyword, freq in job_keywords.items():
            # Case-insensitive keyword search with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, resume_lower):
                matched_keywords.append(keyword)
            else:
                missing_keywords.append((keyword, freq))
        
        # Calculate score based on match percentage
        match_percentage = len(matched_keywords) / len(job_keywords) if job_keywords else 0
        score = match_percentage * 100
        
        # Bonus for high-frequency missing keywords
        missing_keywords.sort(key=lambda x: x[1], reverse=True)
        missing_keywords = [kw[0] for kw in missing_keywords[:10]]  # Top 10 missing
        
        self.logger.debug(f"Keyword match: {len(matched_keywords)}/{len(job_keywords)}")
        return score, matched_keywords, missing_keywords
    
    def _score_formatting(self, resume_text: str) -> float:
        """
        Score formatting compatibility for ATS.
        
        Checks for:
        - Proper line breaks (not too fragmented)
        - Consistent spacing
        - Absence of special characters
        - Proper section headers
        """
        score = 100.0
        
        # Check for excessive special characters (bad for ATS)
        special_char_count = len(re.findall(r'[^a-zA-Z0-9\s\n\-\.\,\(\)]', resume_text))
        if special_char_count > 20:
            score -= min(20, special_char_count / 2)
        
        # Check for consistent spacing
        lines = resume_text.split('\n')
        empty_lines = sum(1 for line in lines if not line.strip())
        total_lines = len(lines)
        
        # Some empty lines are good, but too many indicate poor structure
        empty_ratio = empty_lines / total_lines if total_lines > 0 else 0
        if empty_ratio > 0.3:  # More than 30% empty
            score -= 15
        if empty_ratio < 0.05:  # Less than 5% empty
            score -= 10
        
        # Check for readable line length (not too long paragraphs)
        long_lines = sum(1 for line in lines if len(line.strip()) > 120)
        if long_lines > len(lines) * 0.5:
            score -= 10
        
        return max(score, 0)
    
    def _score_content_completeness(self, sections: Dict) -> float:
        """
        Score based on resume section completeness.
        
        Ideal resume includes:
        - Contact information
        - Professional summary/objective
        - Work experience
        - Education
        - Skills
        """
        score = 0.0
        required_sections = {'contact', 'summary', 'experience', 'education', 'skills'}
        
        found_sections = set(sections.keys())
        matched_sections = found_sections.intersection(required_sections)
        
        # Base score for each section found
        score = (len(matched_sections) / len(required_sections)) * 100
        
        # Bonus for additional sections
        additional = len(found_sections) - len(matched_sections)
        if additional > 0:
            score += min(10, additional * 2)
        
        self.logger.debug(f"Content completeness: {len(matched_sections)}/{len(required_sections)} sections")
        return min(score, 100)
    
    def _score_readability(self, resume_text: str) -> float:
        """
        Score readability and structure quality.
        
        Based on:
        - Sentence structure
        - Use of action verbs
        - Bullet point format
        - Proper capitalization
        """
        score = 50.0  # Base score
        
        resume_lower = resume_text.lower()
        
        # Check for action verbs (positive indicator)
        action_verb_count = sum(1 for verb in self.STRONG_ACTION_VERBS 
                                if re.search(r'\b' + verb + r'\b', resume_lower))
        if action_verb_count > 0:
            score += min(25, action_verb_count * 2)
        
        # Check for bullet points or organized content
        bullet_chars = resume_text.count('•') + resume_text.count('-') + resume_text.count('*')
        if bullet_chars >= 5:
            score += 15
        
        # Check for proper capitalization (headers)
        capitalized_lines = sum(1 for line in resume_text.split('\n') 
                               if line.strip() and line[0].isupper())
        if capitalized_lines > len(resume_text.split('\n')) * 0.1:
            score += 10
        
        return min(score, 100)
    
    def format_for_ats(self, resume_text: str) -> str:
        """
        Format resume text for optimal ATS compatibility.
        
        Applies transformations:
        - Remove special formatting characters
        - Standardize spacing and line breaks
        - Clean up inconsistent formatting
        - Preserve readable structure
        
        Args:
            resume_text (str): Original resume text
            
        Returns:
            str: ATS-optimized resume text
        """
        text = resume_text
        
        # Replace em-dashes and other dashes with standard dash
        text = re.sub(r'[–—]', '-', text)
        
        # Replace smart quotes with standard quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"['']", "'", text)
        
        # Remove most special Unicode characters but keep common ones
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Standardize whitespace
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n  +', '\n', text)  # Remove indentation
        
        # Normalize line breaks (max 2 consecutive)
        text = re.sub(r'\n\n\n+', '\n\n', text)
        
        # Remove bullet symbols but keep line structure
        text = re.sub(r'[•○◆★✓▪]', '-', text)
        
        self.logger.info("Resume formatted for ATS compatibility")
        return text.strip()
    
    def optimize_bullet_points(self, bullet_point: str, job_keywords: Dict[str, int]) -> str:
        """
        Optimize a bullet point to include relevant keywords while maintaining truth.
        
        This method DOES NOT use AI - it applies template-based keyword injection.
        AI-based optimization is handled in the Groq integration layer.
        
        Current approach:
        - Identifies metrics and achievements
        - Suggests keyword additions
        - Preserves factual accuracy
        
        Args:
            bullet_point (str): Original bullet point
            job_keywords (Dict[str, int]): Keywords from job description
            
        Returns:
            str: Optimized bullet point with suggested improvements
        """
        point = bullet_point.strip()
        
        # Remove leading bullet characters
        point = re.sub(r'^[\s•\-\*]+', '', point)
        
        # Preserve existing metrics (numbers, percentages, years)
        metrics = re.findall(r'\d+[%\$K\+]?|20\d{2}', point)
        
        # Count how many top keywords already exist
        top_keywords = list(job_keywords.keys())[:5]
        existing_keywords = []
        
        for keyword in top_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', point.lower()):
                existing_keywords.append(keyword)
        
        # If missing high-frequency keywords, note them
        missing_top = [kw for kw in top_keywords if kw not in existing_keywords]
        
        # Recommendation: Inject keywords naturally (specific instruction for LLM)
        suggestion = point
        if missing_top and metrics:
            # Mark for AI enhancement with specific keywords
            suggestion = f"[KEYWORD_BOOST: {', '.join(missing_top[:2])}] {point}"
        
        self.logger.debug(f"Optimized bullet point - Keywords: {len(existing_keywords)} found")
        return suggestion
    
    def preserve_metrics(self, text: str) -> List[str]:
        """
        Extract and preserve important metrics from resume.
        
        Identifies:
        - Percentages (growth, improvement)
        - Dollar amounts (revenue, budget)
        - Quantities (team size, users impacted)
        - Dates and years
        
        Args:
            text (str): Resume text
            
        Returns:
            List[str]: Important metrics found
        """
        metrics = []
        
        # Find percentages
        metrics.extend(re.findall(r'\d+%', text))
        
        # Find dollar amounts
        metrics.extend(re.findall(r'\$[\d,]+', text))
        metrics.extend(re.findall(r'[\d,]+\s*(?:million|billion|K|M|B)', text, re.IGNORECASE))
        
        # Find quantities (people, customers, etc.)
        metrics.extend(re.findall(r'\d+\s+(?:people|users|customers|clients|employees)', text, re.IGNORECASE))
        
        # Find time periods
        metrics.extend(re.findall(r'20\d{2}|Q[1-4]\s*20\d{2}', text))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_metrics = []
        for metric in metrics:
            if metric.lower() not in seen:
                unique_metrics.append(metric)
                seen.add(metric.lower())
        
        self.logger.debug(f"Preserved {len(unique_metrics)} metrics from resume")
        return unique_metrics
    
    def generate_optimization_report(self, ats_score: Dict, resume_text: str,
                                    job_description: str) -> Dict[str, any]:
        """
        Generate a comprehensive ATS optimization report.
        
        Args:
            ats_score (Dict): Output from calculate_ats_score()
            resume_text (str): Resume text
            job_description (str): Job description
            
        Returns:
            Dict containing detailed recommendations
        """
        report = {
            'score': ats_score['overall_score'],
            'breakdown': {
                'keywords': ats_score['keyword_score'],
                'format': ats_score['format_score'],
                'content': ats_score['content_score'],
                'readability': ats_score['readability_score'],
            },
            'matched_keywords': ats_score['matched_keywords'],
            'top_missing_keywords': ats_score['missing_keywords'][:5],
            'metrics_preserved': self.preserve_metrics(resume_text),
            'recommendations': self._generate_recommendations(ats_score),
        }
        
        return report
    
    def _generate_recommendations(self, ats_score: Dict) -> List[str]:
        """Generate actionable recommendations based on ATS score breakdown"""
        recommendations = []
        
        if ats_score['keyword_score'] < 30:
            recommendations.append("⚠️  Low keyword match: Add missing technical skills and job-specific terms")
        
        if ats_score['format_score'] < 10:
            recommendations.append("⚠️  Poor formatting: Remove tables, images, and special formatting")
        
        if ats_score['content_score'] < 10:
            recommendations.append("⚠️  Incomplete sections: Ensure all major resume sections are present")
        
        if ats_score['readability_score'] < 10:
            recommendations.append("⚠️  Poor readability: Add action verbs and organize content with bullet points")
        
        if ats_score['overall_score'] >= 70:
            recommendations.append("✓ Good ATS compatibility - Ready to apply")
        
        if ats_score['overall_score'] >= 80:
            recommendations.append("✓ Excellent ATS compatibility - High chances of passing screening")
        
        return recommendations
