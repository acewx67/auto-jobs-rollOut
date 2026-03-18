# Jobs Automaton - Architecture & Design

## System Overview

Jobs Automaton is a modular AI-powered resume tailoring pipeline built with a clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                           │
│  ┌──────────────────┐   ┌──────────────────┐                │
│  │   CLI (cli.py)   │   │  API (api.py)    │                │
│  └──────────┬───────┘   └────────┬─────────┘                │
└─────────────┼───────────────────┼────────────────────────────┘
              │                   │
┌─────────────┼───────────────────┼────────────────────────────┐
│             ▼                   ▼                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Resume Tailoring Pipeline (resume_tailor.py)      │   │
│  │  - Orchestrates the entire workflow               │   │
│  │  - Coordinates all components                     │   │
│  │  - Manages error handling & logging               │   │
│  └────┬────────────────────┬───────────────┬──────────┘   │
│       │                    │               │               │
│       ▼                    ▼               ▼               │
│  ┌──────────────┐   ┌────────────────┐  ┌──────────────┐  │
│  │Resume Parser │   │ATS Optimizer   │  │Groq Client   │  │
│  │              │   │                │  │              │  │
│  │• PDF parsing │   │• Keyword       │  │• AI analysis │  │
│  │• DOCX parse  │   │  extraction    │  │• Rewriting   │  │
│  │• Text clean  │   │• Score calc    │  │• Optimization│  │
│  │• Struct seg  │   │• Format check  │  │• API calls   │  │
│  └──────────────┘   │• Metrics       │  └──────────────┘  │
│                     │  preservation  │                    │
│                     └────────────────┘                    │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           File I/O & Data Storage                   │  │
│  │  • data/resumes/input/ (original resumes)           │  │
│  │  • data/resumes/output/ (tailored resumes)          │  │
│  │  • data/job_posts/ (job descriptions)               │  │
│  │  • logs/ (application logs)                         │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘

External Services:
┌─────────────────────┐
│  Groq API           │
│  openai/gpt-oss-120b│
│  (Cloud)            │
└─────────────────────┘
```

## Component Design

### 1. Resume Parser (`src/core/resume_parser.py`)

**Responsibilities:**
- Extract text from PDF and DOCX formats
- Normalize and clean extracted text
- Parse resume into logical sections
- Handle encoding issues and special characters

**Key Methods:**
```python
parse(file_path)              # Main entry point
_parse_pdf(file_path)         # PDF extraction
_parse_docx(file_path)        # DOCX extraction
_normalize_text(text)         # Text cleaning
_structure_resume(text)       # Section segmentation
```

**Design Pattern:** Single Responsibility - Only handles parsing
**Error Handling:** Custom `ResumeParseError` for file/format issues

### 2. ATS Optimizer (`src/utils/ats_optimizer.py`)

**Responsibilities:**
- Extract keywords from job descriptions
- Calculate ATS compatibility scores (0-100)
- Analyze resume formatting for ATS systems
- Optimize bullet points with keyword suggestions
- Preserve important metrics

**Scoring Breakdown (100 points total):**
- **Keywords (50 pts):** Primary job requirements coverage
- **Format (20 pts):** ATS system compatibility
- **Content (15 pts):** Resume section completeness
- **Readability (15 pts):** Content clarity & structure

**Key Methods:**
```python
calculate_ats_score()         # Main scoring
extract_keywords()            # Keyword analysis
format_for_ats()              # Formatting optimization
preserve_metrics()            # Metric extraction
optimize_bullet_point()       # Bullet point enhancement
generate_optimization_report() # Comprehensive insights
```

**Why Modular ATS Scoring:**
- Provides multi-factor analysis (not just keyword matching)
- Gives actionable feedback for each category
- Enables gradual improvements
- Simulates real ATS system behavior

### 3. Groq AI Client (`src/groq_client/client.py`)

**Responsibilities:**
- Manage Groq API authentication
- Analyze job descriptions with AI
- Generate AI-tailored resumes
- Optimize professional summaries
- Handle API errors and retries

**Key Methods:**
```python
analyze_job_description()     # Extract job requirements
generate_tailored_resume()    # AI-powered rewriting
generate_professional_summary() # Summary generation
optimize_bullet_point()       # Content enhancement
_call_api()                   # Wrapper with retry logic
```

**System Prompt Design:**
The system prompt emphasizes:
- Factual accuracy (never fabricate)
- ATS optimization (keyword integration)
- Truthful representation (always defensible)
- Professional quality

**Retry Logic:**
- Exponential backoff: 1s, 2s, 4s
- Max 3 attempts before failure
- Timeout: 30 seconds per request

### 4. Resume Tailoring Pipeline (`src/core/resume_tailor.py`)

**Responsibilities:**
- Orchestrate complete tailoring workflow
- Coordinate parsing, ATS, and Groq components
- Generate output files
- Manage error states and recovery
- Support batch operations

**Workflow:**
```
1. Parse resume               (Resume Parser)
2. Load job description       (File I/O)
3. Calculate initial ATS      (ATS Optimizer)
4. Analyze job with AI        (Groq)
5. Generate tailored resume   (Groq)
6. Apply ATS formatting       (ATS Optimizer)
7. Calculate final ATS        (ATS Optimizer)
8. Generate report            (ATS Optimizer)
9. Save output                (File I/O)
10. Return results            (Dict)
```

**Key Methods:**
```python
tailor()                      # Main entry point for single job
batch_tailor()                # Process multiple jobs
_parse_resume()               # Step 1
_load_job_description()       # Step 2
_extract_tailored_text()      # Step 5 helper
_save_output()                # Step 9
```

### 5. CLI Interface (`src/cli.py`)

**Responsibilities:**
- Provide user-friendly command-line interface
- Parse and validate arguments
- Display formatted output with emojis
- Handle user errors gracefully

**Commands:**
```
tailor         - Single resume tailoring
batch          - Multiple job processing
analyze-job    - Job requirement extraction
check-ats      - ATS score calculation
```

### 6. REST API (`src/api.py`)

**Responsibilities:**
- Provide HTTP endpoints for all operations
- Handle file uploads for resumes
- Validate request/response formats
- Manage session state
- Support integration with external tools

**Endpoints:**
```
GET    /health          - Health check
GET    /api/status      - Service capabilities
POST   /api/tailor      - Tailor resume
POST   /api/ats-score   - Calculate ATS score
POST   /api/analyze-job - Analyze job posting
```

## Data Flow: Complete Tailoring Process

```
User Input:
  ├── Resume file (PDF/DOCX)
  └── Job description (text/file)
        │
        ▼
1. Resume Parsing
  ├─ Extract text from file
  ├─ Normalize & clean text
  └─ Segment into sections
        │
        ▼
2. Initial Assessment
  ├─ Calculate initial ATS score
  └─ Extract job keywords
        │
        ▼
3. AI Analysis
  ├─ Groq analyzes job posting
  ├─ Extracts requirements
  └─ Identifies key skills
        │
        ▼
4. AI Tailoring
  ├─ Groq generates tailored resume
  ├─ Reframes experiences
  ├─ Integrates keywords
  └─ Maintains truthfulness
        │
        ▼
5. Optimization
  ├─ Apply ATS formatting
  ├─ Verify metrics preserved
  └─ Calculate final ATS score
        │
        ▼
6. Output Generation
  ├─ Save tailored resume (TXT/JSON)
  ├─ Generate report
  └─ Calculate improvement metrics
        │
        ▼
Results:
  ├─ Tailored resume text
  ├─ ATS score improvement
  ├─ Key changes summary
  ├─ Matched/missing keywords
  └─ Optimization recommendations
```

## Design Principles

### 1. Modular Architecture
- Each component has a single responsibility
- Components are independently testable
- Easy to replace/upgrade individual parts
- Clear interfaces between components

### 2. Separation of Concerns
- **Parsing**: Resume file → Text extraction
- **Analysis**: Text → Metrics & Keywords
- **Tailoring**: Resume + Job → AI rewriting
- **Optimization**: Content → ATS-friendly format
- **Presentation**: Data → User interface

### 3. Error Handling
- Custom exception classes per module
- Graceful degradation where possible
- Clear error messages
- Logging at each step

### 4. Testing
- Unit tests for each component
- Mock external services (especially Groq API)
- Integration tests for workflows
- Test coverage targets >80%

### 5. Extensibility
- Add new resume formats: Extend `ResumeParser`
- Add new job sources: Extend `TailorPipeline`
- Add new output formats: Extend `_save_output()`
- Add new ATS rules: Extend `ATSOptimizer`

## Performance Considerations

### Processing Time Breakdown
- **Resume parsing**: <500ms
- **Initial ATS scoring**: ~200ms
- **Groq API calls**: 5-15 seconds (includes network latency)
- **ATS optimization**: ~300ms
- **Total typical**: 6-20 seconds per resume

### Optimization Opportunities
1. **Caching**: Cache job analysis results for duplicate postings
2. **Parallel processing**: Run multiple tailorings concurrently
3. **Model optimization**: Fine-tune Groq model parameters
4. **Batch operations**: Process groups efficiently

## Scalability

### Batch Processing
```python
# Process 100 jobs against same resume
result = pipeline.batch_tailor(resume, jobs_directory)
```
- Reuses resume parsing
- Sequential job analysis (respects rate limits)
- Aggregated results and statistics

### API Deployment
- Stateless design (each request independent)
- Can run multiple instances behind load balancer
- File uploads served from shared storage
- Database logging (future enhancement)

## Future Architecture Changes

### Feature 2: Auto Job Fetching
- Add `JobFetcher` component for LinkedIn/Indeed scraping
- Add job filtering based on keyword matching
- Cache fetched jobs for batch operations

### Feature 3: Auto Application
- Add `ApplicationHandler` for form-filling
- Add credential management
- Track application history

### Enhancements
- Add database layer for audit trail
- Add webhook support for external integrations
- Add fine-tuned AI models
- Add user authentication and multi-tenancy

## Technology Stack Justification

### Python
- Rich data processing libraries
- Strong async capabilities
- Easy integration testing
- Wide industry adoption

### Groq API
- Fast inference (3x faster than typical LLMs)
- Reasonable pricing for development
- Open source model (openai/gpt-oss-120b)
- Easy to switch providers if needed

### Flask
- Lightweight for simple APIs
- Easy to test
- Good documentation
- Can scale with async workers

### pypdf + python-docx
- Industry standard libraries
- Well-maintained
- Reliable file parsing
- Handle edge cases well

## Security Considerations

1. **API Key Management**
   - Store in `.env` (never in code)
   - Use environment variables in production
   - Rotate keys regularly

2. **File Handling**
   - Validate file types (extension + magic bytes)
   - Scan for malicious content (optional)
   - Store in isolated directories
   - Clean up temporary files

3. **API Access**
   - Rate limiting (future enhancement)
   - Authentication tokens (future enhancement)
   - HTTPS in production
   - CORS configuration

4. **Data Privacy**
   - Don't log sensitive resume content
   - Encrypted storage (future enhancement)
   - User consent for data processing
   - Compliance with GDPR/CCPA

## Monitoring & Logging

### Log Levels
- **DEBUG**: Detailed processing steps
- **INFO**: Component initialization and major events
- **WARNING**: Recoverable issues
- **ERROR**: Unrecoverable errors

### Metrics to Track
- API response times
- ATS score distributions
- Groq API usage and costs
- Error rates by component
- Resume processing volumes

## Testing Strategy

### Unit Tests
- Component isolation with mocks
- Edge case coverage
- Error condition testing

### Integration Tests
- Component interaction workflows
- End-to-end resume tailoring
- Batch operations

### Performance Tests
- Benchmark processing times
- API response SLAs
- Memory usage profiles

---

**Next**: See [FEATURE_1_RESUME_TAILORING.md](FEATURE_1_RESUME_TAILORING.md) for feature-specific details.
