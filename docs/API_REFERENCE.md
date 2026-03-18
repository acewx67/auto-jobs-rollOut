# API Reference

Complete documentation for CLI and REST API endpoints.

## Quick Reference

### CLI Commands
```bash
# Tailor single resume
python -m src.cli tailor --resume <file> --job <desc>

# Batch processing
python -m src.cli batch --resume <file> --jobs-directory <dir>

# Analyze job
python -m src.cli analyze-job --job <desc>

# Check ATS score
python -m src.cli check-ats --resume <file> --job <desc>
```

### REST API Endpoints
```
POST /api/tailor          - Tailor resume
POST /api/ats-score       - Calculate ATS score  
POST /api/analyze-job     - Analyze job description
GET  /api/status          - Service status
GET  /health              - Health check
```

---

## Command-Line Interface (CLI)

All commands are run via: `python -m src.cli [command] [options]`

### Global Options

```
-v, --verbose             Enable verbose logging (debug mode)
-h, --help                Show help message
```

### Command: `tailor`

Tailor a resume for a specific job.

**Usage:**
```bash
python -m src.cli tailor --resume RESUME --job JOB [options]
```

**Arguments:**
```
-r, --resume FILE       (Required) Path to resume file (.pdf, .docx)
-j, --job TEXT/FILE     (Required) Job description (text or file path)
-of, --output-format    (Optional) Output format: txt, json (default: txt)
```

**Examples:**
```bash
# Basic usage
python -m src.cli tailor --resume resume.pdf --job "Senior Python Engineer..."

# From job file
python -m src.cli tailor --resume resume.pdf --job job_posting.txt

# Verbose output
python -m src.cli tailor --resume resume.pdf --job job_posting.txt --verbose

# JSON output
python -m src.cli tailor --resume resume.pdf --job job_posting.txt -of json
```

**Output:**
```
============================================================
  Resume Tailoring
============================================================

📊 Overall ATS Score: 78/100
   Rating: 👍 Good

   Breakdown:
   - Keywords:    40.0/50
   - Formatting:  18.0/20
   - Content:     12.0/15
   - Readability: 8.0/15

📈 Improvement:     +23 points (+42%)
📁 Output saved to: data/resumes/output/resume_tailored_20260318_215130.txt
⏱️  Processing time: 12.3s

🔄 Key Changes Made:
   • Reordered experience to highlight backend focus
   • Integrated AWS and Docker terminology
   • Added quantified achievement metrics

✓ Keywords Found (4):
   • Python
   • AWS
   • Docker
   • Microservices

⚠️  Keywords Missing (2):
   • Kubernetes
   • Terraform

✨ Resume ready to submit!
```

---

### Command: `batch`

Process a resume against multiple job postings.

**Usage:**
```bash
python -m src.cli batch --resume RESUME --jobs-directory DIR [options]
```

**Arguments:**
```
-r, --resume FILE           (Required) Path to resume file
-jd, --jobs-directory DIR   (Required) Directory containing job files
-of, --output-format        (Optional) Output format (default: txt)
```

**Setup:**
```bash
# Create jobs directory
mkdir jobs_to_apply/

# Add job descriptions (one per file)
echo "Senior Backend Engineer..." > jobs_to_apply/job1.txt
echo "Tech Lead Position..." > jobs_to_apply/job2.txt
echo "Principal Architect..." > jobs_to_apply/job3.txt
```

**Example:**
```bash
python -m src.cli batch --resume resume.pdf --jobs-directory ./jobs_to_apply/
```

**Output:**
```
============================================================
  Batch Resume Tailoring
============================================================

Total jobs processed: 3
✅ Successful: 3
❌ Failed: 0

📈 Average ATS Improvement: +18 points

Detailed results for each job:
  • job1: 55 → 73 (+18)
  • job2: 55 → 81 (+26)
  • job3: 55 → 62 (+7)

✨ All tailored resumes ready!
```

---

### Command: `analyze-job`

Analyze a job description to extract requirements.

**Usage:**
```bash
python -m src.cli analyze-job --job JOB [options]
```

**Arguments:**
```
-j, --job-description TEXT/FILE  (Required) Job description
```

**Example:**
```bash
python -m src.cli analyze-job --job job_posting.txt
```

**Output:**
```
============================================================
  Analysis Results ✅
============================================================

📌 Job Title: Senior Software Engineer

🔧 Required Skills:
   • Python
   • AWS
   • Docker
   • Kubernetes
   • System Design

💼 Required Experience:
   • 5+ years of backend development
   • Leadership of technical teams
   • Microservices architecture experience

📋 Key Responsibilities:
   • Design and implement scalable systems
   • Lead technical discussions and code reviews
   • Mentor junior developers

🔑 ATS Keywords (for resume matching):
   • Python
   • AWS
   • Docker
   • Kubernetes
   • Microservices
   • Leadership
   • System Design
   • Backend Development
   • Scalability
   • Code Review
   • Team Leadership
```

---

### Command: `check-ats`

Calculate ATS score for a resume against a job.

**Usage:**
```bash
python -m src.cli check-ats --resume RESUME --job JOB
```

**Arguments:**
```
-r, --resume FILE               (Required) Resume file path
-j, --job-description TEXT/FILE (Required) Job description
```

**Example:**
```bash
python -m src.cli check-ats --resume resume.pdf --job job_posting.txt
```

**Output:**
```
============================================================
  ATS Score Results ✅
============================================================

📊 Overall ATS Score: 65/100
   Rating: ⚠️  Fair

   Breakdown:
   - Keywords:    32.0/50
   - Formatting:  15.0/20
   - Content:     10.0/15
   - Readability: 8.0/15

✓ Keywords Matched: 8
  Examples: Python, AWS, Docker, Backend, Development, Team, Leadership, Code

⚠️  Keywords Missing: 5
  Top suggestions: Kubernetes, Microservices, System Design, Scaling, DevOps

💡 Recommendations:
  ⚠️  Low keyword match: Add missing technical skills
  ✓ Good ATS compatibility - Ready to apply
```

---

## REST API

Base URL: `http://localhost:5000`

### Authentication

Current version uses no authentication. Production deployments should add:
- API key validation
- Rate limiting
- Request signing

### Response Format

All responses are JSON:

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message here"
}
```

---

### Endpoint: `GET /health`

Health check endpoint.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "jobs-automaton-api",
  "version": "0.1.0"
}
```

---

### Endpoint: `GET /api/status`

Get API status and capabilities.

**Request:**
```bash
curl http://localhost:5000/api/status
```

**Response:**
```json
{
  "service": "jobs-automaton",
  "version": "0.1.0",
  "status": "operational",
  "capabilities": [
    "Resume tailoring",
    "ATS scoring",
    "Job analysis",
    "Batch processing"
  ],
  "endpoints": {
    "/health": "Health check",
    "/api/tailor": "Tailor resume (POST)",
    "/api/ats-score": "Calculate ATS score (POST)",
    "/api/analyze-job": "Analyze job description (POST)",
    "/api/status": "API status"
  }
}
```

---

### Endpoint: `POST /api/tailor`

Tailor a resume for a specific job.

**Request:**
```bash
curl -X POST http://localhost:5000/api/tailor \
  -F "resume=@resume.pdf" \
  -F "job_description=Senior Python Engineer, 5+ years experience..."
```

**Parameters:**
- `resume` (file, required): Resume file (.pdf, .docx)
- `job_description` (text, required): Job description
- `output_format` (text, optional): "txt" or "json" (default: "txt")

**Response:**
```json
{
  "success": true,
  "original_ats_score": 55,
  "final_ats_score": 78,
  "ats_improvement": 23,
  "ats_improvement_percentage": 41.8,
  "key_changes": [
    "Reordered experience to highlight backend focus",
    "Integrated AWS and Docker terminology",
    "Added quantified achievement metrics"
  ],
  "matched_keywords": ["Python", "AWS", "Docker", "Backend"],
  "missing_keywords": ["Kubernetes", "CI/CD"],
  "metrics_preserved": ["5+ years", "$500M", "40% improvement"],
  "output_file": "/path/to/tailored_resume.txt",
  "processing_time_seconds": 12.3,
  "report": {
    "score": 78,
    "breakdown": {
      "keywords": 40.0,
      "format": 18.0,
      "content": 12.0,
      "readability": 8.0
    }
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Resume file is required"
}
```

---

### Endpoint: `POST /api/ats-score`

Calculate ATS score without generating new resume.

**Request:**
```bash
curl -X POST http://localhost:5000/api/ats-score \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Developer\nExperience: Senior Backend Engineer...",
    "job_description": "We are hiring a Senior Python Engineer..."
  }'
```

**Parameters:**
- `resume_text` (string, required): Resume content
- `job_description` (string, required): Job description

**Response:**
```json
{
  "success": true,
  "overall_score": 65,
  "keyword_score": 32.0,
  "format_score": 15.0,
  "content_score": 10.0,
  "readability_score": 8.0,
  "matched_keywords": ["Python", "Backend", "AWS"],
  "missing_keywords": ["Kubernetes", "Docker"],
  "report": {
    "score": 65,
    "breakdown": { ... },
    "recommendations": [
      "⚠️  Low keyword match: Add missing technical skills"
    ]
  }
}
```

---

### Endpoint: `POST /api/analyze-job`

Analyze a job description to extract requirements.

**Request:**
```bash
curl -X POST http://localhost:5000/api/analyze-job \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Software Engineer - 5+ years..."
  }'
```

**Parameters:**
- `job_description` (string, required): Job posting text

**Response:**
```json
{
  "success": true,
  "job_title": "Senior Software Engineer",
  "required_skills": [
    "Python",
    "AWS",
    "Docker",
    "Kubernetes",
    "System Design"
  ],
  "required_experience": [
    "5+ years of backend development",
    "Experience leading technical teams"
  ],
  "key_responsibilities": [
    "Design and implement scalable systems",
    "Lead code reviews and architectural discussions",
    "Mentor junior developers"
  ],
  "nice_to_have": [
    "Open source contributions",
    "Conference speaking experience",
    "Startup experience"
  ],
  "culture_indicators": [
    "Collaborative mindset",
    "Self-motivated",
    "Leadership skills"
  ],
  "keywords": [
    "Python",
    "AWS",
    "Docker",
    "Kubernetes",
    "Leadership",
    ...
  ]
}
```

---

## Python SDK (Programmatic Usage)

### Basic Usage

```python
from src.core.resume_tailor import TailorPipeline

# Initialize pipeline
pipeline = TailorPipeline(groq_api_key="your-key-here")

# Tailor resume
result = pipeline.tailor(
    resume_path="path/to/resume.pdf",
    job_description="Senior Python Engineer...",
    output_format="txt"
)

# Access results
print(f"Original: {result['original_ats_score']}")
print(f"Tailored: {result['final_ats_score']}")
print(f"Improvement: +{result['ats_improvement']} ({result['ats_improvement_percentage']}%)")
```

### Advanced: Batch Processing

```python
# Process multiple jobs
results = pipeline.batch_tailor(
    "resume.pdf",
    "jobs_directory/",
    output_format="json"
)

print(f"Processed: {results['total_jobs']}")
print(f"Success: {results['successful']}")
print(f"Failed: {results['failed']}")

for job_name, result in results['tailored_resumes'].items():
    print(f"{job_name}: {result['original_ats_score']} → {result['final_ats_score']}")
```

### Advanced: Direct Component Usage

```python
from src.core.resume_parser import ResumeParser
from src.utils.ats_optimizer import ATSOptimizer
from src.groq_client.client import GroqClient

# Parse resume
parser = ResumeParser()
parsed = parser.parse("resume.pdf")

# Analyze job
groq = GroqClient()
analysis = groq.analyze_job_description("job posting text")

# Calculate score
optimizer = ATSOptimizer()
score = optimizer.calculate_ats_score(
    parsed['normalized_text'],
    "job description",
    parsed['sections']
)

print(f"ATS Score: {score['overall_score']}/100")
```

---

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "success": false,
  "error": "Resume file is required"
}
```

**422 Unprocessable Entity**
```json
{
  "success": false,
  "error": "Tailoring failed: Invalid API response"
}
```

**503 Service Unavailable**
```json
{
  "success": false,
  "error": "API error: Groq service temporarily unavailable"
}
```

---

## Rate Limiting

Current implementation has no rate limiting. Recommended limits:
- CLI: Unlimited (local use)
- API: 100 requests/minute per IP
- Groq API: Free tier ~30 requests/minute

---

## Migration Guide: v0.1.0 to Future Versions

### v0.2.0 (Planned)
- Database backend for audit trail
- User authentication
- Resume version history
- Job board integration

### v0.3.0 (Planned)
- Auto job fetching (LinkedIn, Indeed)
- Auto application submission
- Cover letter generation
- Interview preparation

---

**Next**: See [TESTING.md](TESTING.md) for testing guidelines.
