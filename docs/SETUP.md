# Jobs Automaton - Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Groq API key (free tier available at https://console.groq.com)
- 500MB available disk space

## Installation & Setup

### Step 1: Clone and Navigate to Repository

```bash
git clone https://github.com/yourusername/jobs-automaton.git
cd jobs-automaton
```

### Step 2: Create Virtual Environment

Create an isolated Python environment to avoid dependency conflicts:

```bash
# Using venv (built-in)
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- `groq` - Groq API client
- `pypdf` - PDF parsing
- `python-docx` - DOCX parsing
- `python-dotenv` - Environment variable management
- `requests` - HTTP client
- `python-multipart` - Middleware for form/file processing
- `fastapi` - High-performance web framework
- `uvicorn` - ASGI server for FastAPI
- `pytest` - Testing framework
- `black`, `flake8` - Code quality tools

### Step 4: Configure Groq API Key

1. Get your API key:
   - Visit https://console.groq.com
   - Sign up for free tier
   - Navigate to API keys
   - Create/copy your API key

2. Configure locally:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

   ⚠️ **Security:** Never commit `.env` to git. It's in `.gitignore` by default.

### Step 5: Verify Installation

```bash
# Test imports
python -c "from src.core.resume_parser import ResumeParser; print('✓ Package imports working')"

# Test Groq connection (requires valid API key)
python -c "from src.groq_client.client import GroqClient; client = GroqClient(); print('✓ Groq client initialized')"
```

## First Use: Quick Start

### Option A: Using CLI (Recommended for beginners)

```bash
# Single resume tailoring
python -m src.cli tailor \
  --resume path/to/your_resume.pdf \
  --job "job_description.txt or job posting text" \
  --output-format txt

# Output:
# - Shows ATS scores (before/after)
# - Displays key changes and matched keywords
# - Saves tailored resume to data/resumes/output/
```

### Option B: Using Python API

```python
from src.core.resume_tailor import TailorPipeline

pipeline = TailorPipeline()
result = pipeline.tailor(
    resume_path="path/to/resume.pdf",
    job_description="Senior Python Engineer - 5+ years experience...",
    output_format="txt"
)

print(f"ATS Score: {result['original_ats_score']} → {result['final_ats_score']}")
print(f"Tailored resume saved to: {result['output_file']}")
```

### Option C: Using Web Interface (Recommended)

1. Start the FastAPI server:
   ```bash
   python -m uvicorn src.api:app --host 0.0.0.0 --port 5000
   ```

2. Open your browser and navigate to:
   [http://localhost:5000](http://localhost:5000)

3. Upload your resume, paste the job description, and get your tailored resume!

### Option D: Using REST API via cURL

```bash
# Start API server (as shown above)

# Test ATS score endpoint
curl -X POST http://localhost:5000/api/ats-score \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Your resume content here...",
    "job_description": "Job posting here..."
  }'
```

## Directory Structure

```
jobs-automaton/
├── src/                        # Source code
│   ├── core/                   # Core logic
│   │   ├── resume_parser.py   # Resume file parsing
│   │   └── resume_tailor.py   # Main tailoring pipeline
│   ├── groq_client/
│   │   └── client.py          # Groq API integration
│   ├── utils/
│   │   └── ats_optimizer.py   # ATS scoring & optimization
│   ├── cli.py                 # Command-line interface
│   └── api.py                 # REST API
├── tests/                      # Unit tests
├── data/
│   ├── resumes/
│   │   ├── input/            # Store your resumes here
│   │   └── output/           # Tailored resumes saved here
│   ├── job_posts/            # Store job descriptions here
│   └── reports/              # Optimization reports
├── docs/                       # Documentation
├── logs/                       # Application logs
├── requirements.txt           # Python dependencies
├── setup.py                   # Package configuration
├── .env.example               # Environment template
└── README.md                  # Project overview
```

## Configuration

### Environment Variables

Edit `.env` to customize behavior:

```bash
# Required
GROQ_API_KEY=your_api_key_here

# Optional settings
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
DEBUG=False                 # Set to True for development

# Feature toggles (future use)
ENABLE_AUTO_FETCH=False
ENABLE_AUTO_APPLY=False
```

### CLI Configuration

The CLI auto-creates required directories:
- `data/resumes/input/` - Store source resumes
- `data/resumes/output/` - Tailored resumes saved here
- `data/job_posts/` - Store job descriptions
- `logs/` - Application logs

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ats_optimizer.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only specific test
pytest tests/test_resume_parser.py::TestResumeParser::test_parser_initialization -v
```

## Troubleshooting

### Issue: "GROQ_API_KEY not found"

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check API key is set correctly
echo $GROQ_API_KEY

# If not set:
cp .env.example .env
# Edit .env with your key and run:
source .env
```

### Issue: "ModuleNotFoundError: No module named 'groq'"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or reinstall specific package
pip install groq==0.4.1
```

### Issue: "Could not import pypdf"

**Solution:**
```bash
# Note: Package name in Python is 'pypdf'
pip install pypdf==4.0.1
```

### Issue: "Permission denied" on Unix/Mac

**Solution:**
```bash
# Make CLI executable
chmod +x src/cli.py

# Or run with python explicitly
python -m src.cli tailor --help
```

### Issue: "API rate limit exceeded"

**Solution:**
- Free Groq tier has rate limits
- Wait a few minutes before retrying
- Check Groq console for current quota: https://console.groq.com
- Consider upgrading plan for higher limits

## Production Deployment

### Using Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV GROQ_API_KEY=$GROQ_API_KEY

EXPOSE 5000

CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "5000"]
```

Build and run:
```bash
docker build -t jobs-automaton .
docker run -e GROQ_API_KEY=your_key -p 5000:5000 jobs-automaton
```

### Using systemd (Linux)

Create `/etc/systemd/system/jobs-automaton.service`:

```ini
[Unit]
Description=Jobs Automaton Resume Tailoring Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/jobs-automaton
Environment="GROQ_API_KEY=your_key_here"
ExecStart=/opt/jobs-automaton/venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 5000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl start jobs-automaton
sudo systemctl enable jobs-automaton
```

## Development Setup

For contributors wanting to enhance the codebase:

```bash
# Install development dependencies
pip install -r requirements.txt

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking (future enhancement)
mypy src/
```

## Next Steps

1. **Read** [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design
2. **Learn** [FEATURE_1_RESUME_TAILORING.md](FEATURE_1_RESUME_TAILORING.md) for feature details
3. **Explore** [API_REFERENCE.md](API_REFERENCE.md) for endpoint documentation
4. **Check** [TODO.md](TODO.md) for planned features and roadmap

## Support

- 📖 See [ARCHITECTURE.md](ARCHITECTURE.md) for design questions
- 🐛 Found a bug? Please report in GitHub issues
- 💡 Feature request? See [TODO.md](TODO.md)
- 📝 Need help? Check the examples in [API_REFERENCE.md](API_REFERENCE.md)

## License

MIT License - See LICENSE file for details
