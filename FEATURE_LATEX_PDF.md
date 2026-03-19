# LaTeX PDF Resume Output Feature

## Overview

A new output format has been added to the resume tailoring pipeline that generates professionally formatted LaTeX documents. This feature allows users to generate ATS-friendly resumes using the Jake Ryan LaTeX template while leveraging your AI-powered tailoring engine.

## Usage

### Basic Command

```bash
python -m src.cli tailor --resume resume-genai.pdf --job jd.txt --output-format latex-pdf
```

### Command Parameters

- `--resume` (required): Path to input resume file (PDF or DOCX)
- `--job` (required): Job description file or text
- `--output-format` (required): Set to `latex-pdf` to generate LaTeX format

### Supported Output Formats

The CLI now supports four output formats:
- `txt` - Plain text resume
- `json` - JSON format with metadata
- `docx` - Microsoft Word format
- `latex-pdf` - LaTeX source (.tex file) with optional PDF compilation

## Features

### 1. Resume Structure Parsing
The LaTeX generator automatically:
- Extracts resume sections (contact, summary, experience, education, skills, projects, certifications)
- Preserves hierarchical structure and formatting
- Maps plain text content to LaTeX commands

### 2. ATS-Optimized Formatting
- Uses Jake Ryan's proven LaTeX resume template
- Maintains ATS compatibility (pdfgentounicode enabled)
- Professional margins and spacing
- Clean, scannable layout

### 3. LaTeX Escaping
- Automatically escapes special LaTeX characters
- Handles complex content safely
- Supports Unicode to LaTeX conversion

### 4. PDF Compilation (Optional)
- If `pdflatex` is available on the system, automatically compiles to PDF
- Falls back to .tex file if `pdflatex` is not available
- Cleans up temporary LaTeX compilation artifacts

### 5. Web Integration
- Seamlessly integrated into the Premium Web Interface
- Direct download link provided after tailoring process

## Output Files

When using `latex-pdf` format:

```
data/resumes/output/
├── resume-genai_tailored_20260318_230836.tex    # LaTeX source file
└── resume-genai_tailored_20260318_230836.pdf    # PDF (if pdflatex available)
```

## Implementation Details

### New Files

1. **`src/utils/latex_generator.py`**
   - `LatexResumeGenerator` class
   - Converts plain text resumes to LaTeX
   - Handles section parsing and formatting
   - Manages PDF compilation
   - Includes LaTeX character escaping utilities

### Modified Files

1. **`src/cli.py`**
   - Added `latex-pdf` to output format choices for `tailor` command
   - Added `latex-pdf` to output format choices for `batch` command
   - Updated help text to document new format

2. **`src/core/resume_tailor.py`**
   - Imported `LatexResumeGenerator` and `LatexGeneratorError`
   - Updated `_save_output()` method to handle `latex-pdf` format
   - Added `_save_as_latex_pdf()` method with fallback error handling
   - Added `latex-pdf` to `PipelineConfig.SUPPORTED_FORMATS`

## Technical Architecture

### Section Mapping

Resume sections are mapped from plain text to LaTeX as follows:

| Plain Text Section | LaTeX Command | Purpose |
|---|---|---|
| Headings | `\section{NAME}` | Major sections |
| Contact Info | `\begin{center}...\end{center}` | Heading with name and contact |
| Subsections | `\resumeSubheading{...}` | Job/education entries |
| Bullet Points | `\resumeItem{...}` | Individual accomplishments |
| Skills | `itemize` + `\textbf{}` | Categorized skill lists |

### LaTeX Template

The generator uses the Jake Ryan resume template with:
- Customizable font options (commented in template)
- Non-standard margins optimized for ATS
- Professional section formatting with horizontal rules
- Full PDF generation support

## System Requirements

### Required
- Python 3.7+
- Dependencies: groq, pypdf, python-docx, python-dotenv, etc. (see requirements.txt)

### Optional
- `pdflatex` - For automatic PDF generation
  - On Ubuntu/Debian: `sudo apt-get install texlive-latex-base`
  - On macOS: `brew install basictex`
  - On Windows: Download from https://miktex.org/

## Workflow

1. **Parse Resume**: Extract text from PDF/DOCX
2. **Tailor Content**: Use AI to match job description
3. **Generate LaTeX**: Convert tailored text to LaTeX format
4. **Compile (Optional)**: Convert .tex to PDF if pdflatex available
5. **Output**: Save both .tex file and PDF (if compiled)

## Error Handling

The system gracefully handles various error scenarios:

| Error | Behavior |
|---|---|
| Invalid LaTeX content | Log error, save as .txt fallback |
| pdflatex not available | Skip PDF compilation, save .tex file |
| LaTeX compilation fails | Log warning, keep .tex file |
| File write errors | Attempt alternative extension, fallback to .txt |

## Example Output

When you run the command:
```bash
python -m src.cli tailor --resume resume-genai.pdf --job jd.txt --output-format latex-pdf
```

You'll see:
```
============================================================
  Resume Tailoring
============================================================

Processing resume: resume-genai.pdf
Job description: jd.txt

[... tailoring process ...]

============================================================
  Tailoring Complete ✅
============================================================

📄 Original Resume: 55/100
📄 Tailored Resume: 46/100

📁 Output saved to: data/resumes/output/resume-genai_tailored_20260318_230836
⏱️  Processing time: 8.3s
```

The output file can be compiled to PDF using:
```bash
pdflatex -interaction=nonstopmode resume-genai_tailored_20260318_230836.tex
```

## Testing

The feature has been tested with:
- Real resume files (PDF format)
- Job descriptions from text files
- Various resume section combinations
- LaTeX special character handling
- Error conditions and fallbacks

## Batch Tailoring

The batch tailoring feature also supports LaTeX PDF output:

```bash
python -m src.cli batch --resume resume.pdf --jobs-directory ./job_posts --output-format latex-pdf
```

This generates a separate LaTeX resume for each job description in the directory.

## Future Enhancements

Potential improvements for future versions:

1. **Template Customization**
   - Support for different LaTeX templates
   - User-defined margin settings
   - Custom color schemes

2. **Advanced Formatting**
   - Support for multi-column layouts
   - Custom section ordering
   - Advanced styling options

3. **Metadata Preservation**
   - Embedding ATS scores in PDF metadata
   - Including tailoring details in LaTeX comments
   - PDF properties (title, author, keywords)

4. **Performance**
   - Parallel PDF compilation for batch jobs
   - Caching of compiled templates
   - Asynchronous PDF generation

## Troubleshooting

### pdflatex not found
If you get a warning that pdflatex is not available:
- Install TeXLive or equivalent LaTeX distribution for your OS
- Edit the .tex file manually and compile with your preferred tool
- Use online LaTeX compilers (Overleaf, etc.) if needed

### LaTeX compilation errors
- Check the generated .tex file for syntax issues
- Verify special characters are properly escaped
- Check LaTeX package documentation for syntax errors

### File permission errors
- Ensure output directory (data/resumes/output/) has write permissions
- Check disk space availability
- Verify user has access to output directory

## Support

For issues or feature requests related to the LaTeX PDF output format, please check:
1. The `docs/FEATURE_1_RESUME_TAILORING.md` for general tailoring documentation
2. Error logs in `logs/` directory
3. Generated .tex files for LaTeX-specific debugging
