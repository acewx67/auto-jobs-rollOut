# Jobs Automaton

A powerful AI-driven automation pipeline for resume tailoring and intelligent job applications.

## Features

### Feature 1: Resume Tailoring (Current Focus)
- **Intelligent Resume Parsing**: Extracts text from PDF and DOCX resumes
- **ATS Optimization**: Comprehensive ATS score calculation and optimization
- **Groq-Powered Tailoring**: LLM-based resume customization for specific job descriptions
- **High ATS Scores**: Maintains formatting, keywords, and metrics for maximum compatibility
- **Detailed Optimization Reports**: Get insights on what was changed and why
- **Premium Web Interface**: A sleek, dark-themed UI for easy resume tailoring and LaTeX PDF generation.

### Feature 2: Auto Fetch & Apply (Planned)
- Automatic job posting fetching from multiple job boards
- Intelligent job matching
- Automatic resume tailoring and application submission

## Quick Start

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

```bash
# Clone repository
git clone https://github.com/yourusername/jobs-automaton.git
cd jobs-automaton

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Groq API
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start the Web Interface
python -m uvicorn src.api:app --host 0.0.0.0 --port 5000
```

Now open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

### CLI: Tailor Your Resume

```bash
python src/cli.py --resume path/to/resume.pdf --job job_description.txt --output tailored_resume.pdf
```

### Web Interface: Tailor via Browser

1. Run the FastAPI server: `python -m uvicorn src.api:app --port 5000`
2. Open `http://localhost:5000`
3. Upload your resume and paste the job description.
4. Click "Tailor My Resume" and download your professionally formatted LaTeX PDF.

### Programmatic Usage

```python
from src.core.resume_tailor import TailorPipeline

pipeline = TailorPipeline()
result = pipeline.tailor(resume_path, job_description, output_format="pdf")
print(f"ATS Score: {result['ats_score']}")
```

## Documentation

- [Setup Guide](docs/SETUP.md) - Installation and configuration
- [Architecture](docs/ARCHITECTURE.md) - System design and approach
- [Feature 1: Resume Tailoring](docs/FEATURE_1_RESUME_TAILORING.md) - Detailed feature documentation
- [API Reference](docs/API_REFERENCE.md) - CLI and API endpoints
- [Testing Guide](docs/TESTING.md) - How to test the pipeline
- [Todo & Roadmap](docs/TODO.md) - Tasks and planned features

## Technologies

- **Python 3.8+** - Backend implementation
- **Groq API** - AI-powered resume analysis and tailoring
- **pypdf** - PDF processing
- **python-docx** - DOCX processing
- **FastAPI / Uvicorn** - High-performance REST API and Web Server
- **Vanilla CSS / JS** - Premium, responsive web interface

## License

MIT License (see LICENSE file)

## Contributing

Contributions welcome! Please follow the setup guide and run tests before submitting PRs.
