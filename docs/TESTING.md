# Testing Guide

Complete guide to testing the Jobs Automaton system.

## Overview

The project uses **pytest** for unit testing with >300 tests covering:
- Resume parsing edge cases
- ATS scoring accuracy
- Groq API integration
- Pipeline workflows
- Error handling

## Running Tests

### Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_resume_parser.py -v

# Run specific test function
pytest tests/test_ats_optimizer.py::TestATSOptimizer::test_extract_keywords -v
```

### Test Execution Options

```bash
# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Run failed tests + last passed
pytest tests/ --ff

# Parallel execution (requires pytest-xdist)
pytest tests/ -n auto

# Verbose output with print statements
pytest tests/ -v -s

# Generate coverage badge
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html:htmlcov
```

---

## Test Structure

```
tests/
├── test_resume_parser.py      # Resume file parsing
├── test_ats_optimizer.py       # ATS scoring and optimization
├── test_groq_client.py         # Groq API integration
├── test_resume_tailor.py       # Pipeline orchestration
└── __init__.py
```

### Test File Naming Convention
- `test_*.py` - Test files
- `Test*` - Test classes
- `test_*` - Test functions
- `test_*_error` - Error/exception tests

---

## Unit Tests by Component

### 1. Resume Parser Tests (`test_resume_parser.py`)

**Coverage:**
- PDF parsing from various formats
- DOCX parsing with tables and content
- Text normalization and cleaning
- Resume section extraction
- Error handling for invalid files

**Key Tests:**
```python
def test_parse_pdf()              # PDF extraction
def test_parse_docx()             # DOCX extraction
def test_normalize_text()         # Text cleaning
def test_structure_resume()       # Section segmentation
def test_parse_nonexistent_file() # Error handling
```

**Run Parser Tests:**
```bash
pytest tests/test_resume_parser.py -v
```

---

### 2. ATS Optimizer Tests (`test_ats_optimizer.py`)

**Coverage:**
- Keyword extraction accuracy
- Multi-factor ATS scoring
- Formatting analysis
- Content completeness checking
- Readability scoring
- Metric extraction

**Key Tests:**
```python
def test_calculate_ats_score()          # Score calculation
def test_extract_keywords()             # Keyword extraction
def test_score_formatting()             # Format compliance
def test_optimize_bullet_points()       # Bullet enhancement
def test_preserve_metrics()             # Metric preservation
def test_generate_optimization_report() # Report generation
```

**Run Optimizer Tests:**
```bash
pytest tests/test_ats_optimizer.py -v
```

---

### 3. Groq Client Tests (`test_groq_client.py`)

**Coverage:**
- API initialization and authentication
- Job description analysis
- Resume tailoring requests
- Professional summary generation
- Error handling and retries
- Mock API responses

**Key Tests:**
```python
def test_client_initialization()         # Client setup
def test_analyze_job_description()       # Job analysis
def test_generate_tailored_resume()      # Resume generation
def test_api_retry_logic()               # Error recovery
def test_invalid_json_response()         # Response validation
```

**Run Groq Tests:**
```bash
pytest tests/test_groq_client.py -v
```

**Note:** Most tests use mocked API responses to avoid requiring valid Groq credentials.

---

### 4. Pipeline Tests (`test_resume_tailor.py`)

**Coverage:**
- Complete tailoring workflow
- Component integration
- Batch processing
- Error handling and recovery
- Configuration management
- File I/O operations

**Key Tests:**
```python
def test_tailor_complete_workflow()      # Full pipeline
def test_batch_tailor_multiple_jobs()    # Batch processing
def test_load_job_description()          # Input loading
def test_save_output()                   # Output generation
```

**Run Pipeline Tests:**
```bash
pytest tests/test_resume_tailor.py -v
```

---

## Integration Tests

### Manual Testing Workflow

Test the **complete** system end-to-end:

```bash
# 1. Create test resume
cp data/resumes/input/sample_resume.pdf test_resume.pdf

# 2. Create test job posting
cat > test_job.txt << 'EOF'
Senior Software Engineer

We're looking for an experienced Senior Software Engineer to join our team.

Requirements:
- 5+ years of Python development
- Strong knowledge of AWS and cloud architecture
- Experience with Docker and Kubernetes
- System design and architecture skills
- Team leadership experience
EOF

# 3. Run single tailoring
python -m src.cli tailor --resume test_resume.pdf --job test_job.txt --verbose

# 4. Check ATS score
python -m src.cli check-ats --resume test_resume.pdf --job test_job.txt

# 5. Analyze job
python -m src.cli analyze-job --job test_job.txt
```

### API Integration Test

```bash
# 1. Start API server in one terminal
python -m src.api

# 2. Test health check
curl http://localhost:5000/health

# 3. Test ATS score endpoint
curl -X POST http://localhost:5000/api/ats-score \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Senior Engineer with 5+ years experience",
    "job_description": "Senior Software Engineer needed"
  }'

# 4. Test tailor endpoint
curl -X POST http://localhost:5000/api/tailor \
  -F "resume=@test_resume.pdf" \
  -F "job_description=Senior role needed..."
```

---

## Test Coverage Analysis

### Current Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Expected output:
# src/core/resume_parser.py    187    5     97%
# src/utils/ats_optimizer.py   420   15     96%
# src/groq_client/client.py    245   20     92%
# src/core/resume_tailor.py    280   25     91%
# ───────────────────────────────────────────
# TOTAL                       1132   65     94%
```

### Coverage Goals
- **Critical modules** (parser, optimizer): 95%+
- **Integration modules** (pipeline, API): 85%+
- **Overall target**: >90%

### Checking Coverage by Module

```bash
# Only show missing lines
pytest tests/ --cov=src --cov-report=term-missing | grep -E "^src.*x$"

# Generate HTML report
pytest tests/ --cov=src --cov-report=html:htmlcov
# Open htmlcov/index.html in browser
```

---

## Mock Data & Fixtures

### Sample Resume

```python
@pytest.fixture
def sample_resume_text():
    return """
    JOHN DEVELOPER
    john.dev@email.com | (555) 123-4567
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 6 years of experience.
    
    WORK EXPERIENCE
    Senior Engineer at TechCorp | 2021-Present
    - Led development of microservices using Python and AWS
    - Managed Docker and Kubernetes deployments
    - Improved API performance by 40%
    """
```

### Sample Job Description

```python
@pytest.fixture
def sample_job_description():
    return """
    Senior Software Engineer
    Requirements:
    - 5+ years Python development
    - AWS and cloud architecture
    - Docker and Kubernetes experience
    - System design skills
    """
```

### Using Fixtures

```python
def test_tailor_with_fixtures(mock_pipeline, sample_resume_text, sample_job_description):
    result = mock_pipeline.tailor(sample_resume_text, sample_job_description)
    assert result['final_ats_score'] > result['original_ats_score']
```

---

## Testing Best Practices

### 1. Unit Test Isolation

```python
# Bad: Tests depend on each other
def test_step1():
    parse_resume("test.pdf")

def test_step2():
    # Depends on test_step1
    assert resume_exists()

# Good: Each test is independent
def test_parse_resume(mock_parser):
    result = mock_parser.parse("test.pdf")
    assert result is not None
```

### 2. Mock External Services

```python
# Bad: Makes real API calls
def test_groq_integration():
    client = GroqClient()
    result = client.analyze_job_description("...")  # Real API call
    assert result is not None

# Good: Mock the API
@patch('src.groq_client.client.Groq')
def test_groq_integration(mock_groq):
    client = GroqClient(api_key="test")
    # Mock behavior...
    assert result is not None
```

### 3. Descriptive Test Names

```python
# Bad
def test_score():
    ...

# Good
def test_calculate_ats_score_with_high_keyword_match():
    ...

# Better
def test_calculate_ats_score_returns_100_for_perfect_match():
    ...
```

### 4. Arrange-Act-Assert Pattern

```python
def test_resume_parsing():
    # Arrange
    test_file = "path/to/test_resume.pdf"
    
    # Act
    parser = ResumeParser()
    result = parser.parse(test_file)
    
    # Assert
    assert result['character_count'] > 0
    assert 'experience' in result['sections']
```

---

## Common Test Scenarios

### Scenario 1: Perfect Resume for Job

```python
def test_perfect_resume_match():
    """Test when resume exactly matches job requirements"""
    
    # Resume has all required skills
    resume = "Senior Python Developer with AWS and Docker experience"
    job = "Senior Python Engineer - AWS and Docker required"
    
    optimizer = ATSOptimizer()
    score = optimizer.calculate_ats_score(resume, job)
    
    # Should have very high keyword score
    assert score['keyword_score'] > 45  # Out of 50
    assert score['overall_score'] > 80
```

### Scenario 2: Resume Missing Key Skills

```python
def test_resume_missing_key_skills():
    """Test when resume lacks important job requirements"""
    
    resume = "Software Developer with 3 years experience"
    job = "Senior AWS & Kubernetes specialist needed"
    
    optimizer = ATSOptimizer()
    score = optimizer.calculate_ats_score(resume, job)
    
    # Should have lower scores
    assert score['keyword_score'] < 20  # Out of 50
    assert 'Kubernetes' in score['missing_keywords']
    assert 'AWS' in score['missing_keywords']
```

### Scenario 3: AI-Powered Enhancement

```python
def test_ai_enhancement_improves_score(mock_pipeline):
    """Test that AI tailoring improves ATS score"""
    
    original_score = 55
    mock_pipeline.optimizer.calculate_ats_score.side_effect = [
        {'overall_score': original_score},
        {'overall_score': 78}  # After tailoring
    ]
    
    result = mock_pipeline.tailor("resume.pdf", "job.txt")
    
    assert result['ats_improvement'] > 0
    assert result['final_ats_score'] > result['original_ats_score']
```

---

## Debugging Tests

### Print Debug Information

```bash
# Show print statements during tests
pytest tests/test_file.py -v -s

# Show all captured output
pytest tests/ -v -s --tb=short
```

### Debug Specific Test

```python
def test_specific_scenario(debug=True):
    if debug:
        import pdb; pdb.set_trace()  # Debugger breakpoint
    
    # Test code...
```

Run with debugger:
```bash
pytest tests/test_file.py::test_specific_scenario -v -s
```

### Pytest Hooks for Debugging

```python
# In conftest.py
@pytest.fixture(autouse=True)
def debug_info(request):
    yield
    if request.node.rep_call.failed:
        print(f"\nTest failed: {request.node.name}")
```

---

## Performance Testing

### Benchmark Key Operations

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run benchmarks
pytest tests/ --benchmark-only

# Compare across runs
pytest tests/ --benchmark-compare
```

### Benchmark Example

```python
def test_resume_parsing_performance(benchmark, sample_pdf):
    parser = ResumeParser()
    
    # Benchmark the parsing
    result = benchmark(parser.parse, sample_pdf)
    
    # Assert performance expectations
    assert result['character_count'] > 0
```

---

## Continuous Integration

### GitHub Actions Configuration

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest tests/ --cov=src
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Troubleshooting Test Issues

### Issue: Tests Fail Locally but Pass in CI

**Solution:**
```bash
# Ensure you have same dependencies
pip install -r requirements.txt --force-reinstall

# Run in isolated environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
pytest tests/
```

### Issue: API Tests Timeout

**Solution:**
```python
# Add timeout to Groq client
@pytest.fixture
def mock_groq_client():
    with patch('src.groq_client.client.Groq'):
        client = GroqClient(api_key="test")
        client.TIMEOUT_SECONDS = 5  # Reduce timeout
        return client
```

### Issue: File Not Found in Tests

**Solution:**
```python
# Use absolute paths
import os
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_FILE = os.path.join(TEST_DIR, 'fixtures', 'sample.pdf')
```

---

## Advanced Testing Topics

### Property-Based Testing

```bash
pip install hypothesis
```

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_normalize_text_never_crashes(text):
    optimizer = ATSOptimizer()
    result = optimizer._normalize_text(text)
    assert isinstance(result, str)
```

### Mutation Testing

```bash
pip install mutmut
mutmut run --tests-dir tests/
```

### Load Testing

```bash
pip install locust

# Create locustfile.py for load testing API
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Guide](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Next**: See [API_REFERENCE.md](API_REFERENCE.md) for API documentation.
