"""
LaTeX resume generator module.

Converts tailored resume text into a professionally formatted LaTeX document
based on the Jake Ryan resume template. Supports PDF compilation if pdflatex
is available on the system.
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class LatexGeneratorError(Exception):
    """Custom exception for LaTeX generation errors"""
    pass


class LatexResumeGenerator:
    """
    Converts plain text resume to formatted LaTeX document.
    
    Features:
    - Parses resume sections (education, experience, skills, etc.)
    - Formats content into LaTeX structure
    - Generates ATS-friendly, professionally formatted resume
    - Optionally compiles to PDF using pdflatex
    """
    
    # Resume section patterns for parsing
    SECTION_PATTERNS = {
        'contact': r'^(contact|contact information)$',
        'summary': r'^(summary|professional summary|objective|profile)$',
        'experience': r'^(experience|work experience|employment|professional experience)$',
        'education': r'^(education|academic|degrees?)$',
        'skills': r'^(technical skills|skills|competencies|expertise)$',
        'projects': r'^(projects|portfolio)$',
        'certifications': r'^(certifications|licenses?|certificates?|awards?)$',
    }
    
    LATEX_TEMPLATE = r"""%-------------------------
% Resume in Latex
% Author : Jake Gutierrez
% Based off of: https://github.com/sb2nov/resume
% License : MIT
%------------------------

\documentclass[letterpaper,11pt]{{article}}

\usepackage{{latexsym}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage{{marvosym}}
\usepackage[usenames,dvipsnames]{{color}}
\usepackage{{verbatim}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[english]{{babel}}
\usepackage{{tabularx}}
\input{{glyphtounicode}}

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{{FiraSans}}
% \usepackage[sfdefault]{{roboto}}
% \usepackage[sfdefault]{{noto-sans}}
% \usepackage[default]{{sourcesanspro}}

% serif
% \usepackage{{CormorantGaramond}}
% \usepackage{{charter}}

\pagestyle{{fancy}}
\fancyhf{{}}
\fancyfoot{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

% Adjust margins
\addtolength{{\oddsidemargin}}{{-0.5in}}
\addtolength{{\evensidemargin}}{{-0.5in}}
\addtolength{{\textwidth}}{{1in}}
\addtolength{{\topmargin}}{{-.5in}}
\addtolength{{\textheight}}{{1.0in}}

\urlstyle{{same}}

\raggedbottom
\raggedright
\setlength{{\tabcolsep}}{{0in}}

% Sections formatting
\titleformat{{\section}}{{
  \vspace{{-4pt}}\scshape\raggedright\large
}}{{}}{{0em}}{{}}[\color{{black}}\titlerule \vspace{{-5pt}}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{{\resumeItem}}[1]{{
  \item\small{{
    {{#1 \vspace{{-2pt}}}}
  }}
}}

\newcommand{{\resumeSubheading}}[4]{{
  \vspace{{-2pt}}\item
    \begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}
      \textbf{{#1}} & #2 \\
      \textit{{\small#3}} & \textit{{\small #4}} \\
    \end{{tabular*}}\vspace{{-7pt}}
}}

\newcommand{{\resumeSubSubheading}}[2]{{
    \item
    \begin{{tabular*}}{{0.97\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
      \textit{{\small#1}} & \textit{{\small #2}} \\
    \end{{tabular*}}\vspace{{-7pt}}
}}

\newcommand{{\resumeProjectHeading}}[2]{{
    \item
    \begin{{tabular*}}{{0.97\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
      \small#1 & #2 \\
    \end{{tabular*}}\vspace{{-7pt}}
}}

\newcommand{{\resumeSubItem}}[1]{{\resumeItem{{#1}}\vspace{{-4pt}}}}

\renewcommand{{\labelitemii}}{{$\vcenter{{\hbox{{\tiny$\bullet$}}}}$}}

\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0.15in, label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-5pt}}}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{{document}}

{heading}

{sections}

\end{{document}}
"""
    
    def __init__(self):
        """Initialize the LaTeX generator"""
        self.logger = logging.getLogger(__name__)
        self._check_pdflatex_available()
    
    def _check_pdflatex_available(self) -> bool:
        """Check if pdflatex is available on the system"""
        try:
            result = subprocess.run(
                ['pdflatex', '--version'],
                capture_output=True,
                timeout=5
            )
            self.pdflatex_available = result.returncode == 0
            if self.pdflatex_available:
                self.logger.info("pdflatex found on system")
            else:
                self.logger.warning("pdflatex not found; will generate .tex file only")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.pdflatex_available = False
            self.logger.warning("pdflatex not available on system; will generate .tex file only")
        
        return self.pdflatex_available
    
    def generate_latex(self, resume_text: str) -> str:
        """
        Convert plain text resume to LaTeX.
        
        Args:
            resume_text (str): Plain text resume content (may contain markdown bold **text**)
            
        Returns:
            str: LaTeX document code
            
        Raises:
            LatexGeneratorError: If generation fails
        """
        try:
            # Parse resume sections FIRST (while still in markdown format)
            sections = self._parse_resume_sections(resume_text)
            
            # Extract name from resume text (usually first line)
            name = self._extract_name_from_text(resume_text)
            
            # Generate heading
            heading_latex = self._generate_heading(name, sections.get('contact', []))
            
            # Generate sections
            sections_latex = self._generate_sections(sections)
            
            # Fill template
            latex_doc = self.LATEX_TEMPLATE.format(
                heading=heading_latex,
                sections=sections_latex
            )
            
            return latex_doc
            
        except Exception as e:
            raise LatexGeneratorError(f"Failed to generate LaTeX: {str(e)}")
    
    def _extract_name_from_text(self, text: str) -> str:
        """
        Extract person's name from resume text (usually first line).
        
        Args:
            text (str): Resume text
            
        Returns:
            str: Extracted name or 'Your Name' if not found
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # First meaningful line is usually the name
        for line in lines[:5]:  # Check first 5 lines
            # Skip section headers and short lines
            if (not line.isupper() and 
                len(line) < 50 and
                not any(keyword in line.lower() for keyword in ['skill', 'experience', 'education', 'project', 'summary'])):
                # Check if it looks like a name (contains letters, not emails, no special chars)
                if not any(c in line for c in ['@', '+', '/', '\\']) and len(line.split()) <= 4:
                    # Strip markdown bold if present
                    name = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
                    return name
        
        return "Your Name"
    
    def _parse_resume_sections(self, text: str) -> Dict[str, List[str]]:
        """
        Parse resume text into sections.
        
        Args:
            text (str): Resume text
            
        Returns:
            Dict with section names as keys and content as values
        """
        sections = {
            'contact': [],
            'summary': [],
            'experience': [],
            'education': [],
            'skills': [],
            'projects': [],
            'certifications': [],
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Check if line is a section header
            # First, remove markdown formatting for pattern matching
            line_for_matching = re.sub(r'\*\*(.*?)\*\*', r'\1', line_stripped)
            
            section_found = False
            for section_key, pattern in self.SECTION_PATTERNS.items():
                if re.match(pattern, line_for_matching.lower()):
                    current_section = section_key
                    section_found = True
                    break
            
            # If not a header, add to current section
            if not section_found and current_section:
                sections[current_section].append(line_stripped)
        
        return sections
    
    def _generate_heading(self, name: str, contact_info: str) -> str:
        """
        Generate LaTeX heading section with contact information.
        
        Args:
            name (str): Person's full name
            contact_info (str or list): Contact information text
            
        Returns:
            str: LaTeX heading code
        """
        # Handle if contact_info is a list
        if isinstance(contact_info, list):
            contact_info = ' '.join(contact_info)
        
        # Extract contact details (phone, email, links)
        lines = [l.strip() for l in contact_info.split('\n') if l.strip()]
        
        phone = ""
        email = ""
        linkedin = ""
        github = ""
        
        for line in lines:
            if '@' in line:
                email = line
            elif 'linkedin' in line.lower():
                linkedin = line
            elif 'github' in line.lower():
                github = line
            elif any(c.isdigit() for c in line) and ('-' in line or '+' in line):
                phone = line
        
        heading = r"\begin{center}" + "\n"
        heading += f"    {{\\Huge \\textbf{{{self._escape_latex(name, preserve_markup=False)}}}}} \\\\ \\vspace{{1pt}}\n"
        
        # Build contact line
        contact_parts = []
        if phone:
            contact_parts.append(self._escape_latex(phone, preserve_markup=False))
        if email:
            email_clean = email.strip('<>')
            contact_parts.append(f"\\href{{mailto:{email_clean}}}{{\\underline{{{self._escape_latex(email_clean, preserve_markup=False)}}}}}")
        if linkedin:
            linkedin_clean = ' '.join(linkedin.split()[1:]) if ' ' in linkedin else linkedin
            contact_parts.append(f"\\href{{https://linkedin.com/in/{linkedin_clean}}}{{\\underline{{linkedin.com/in/{self._escape_latex(linkedin_clean, preserve_markup=False)}}}}}")
        if github:
            github_clean = ' '.join(github.split()[1:]) if ' ' in github else github
            contact_parts.append(f"\\href{{https://github.com/{github_clean}}}{{\\underline{{github.com/{self._escape_latex(github_clean, preserve_markup=False)}}}}}")
        
        if contact_parts:
            heading += "    \\small " + " $|$ ".join(contact_parts) + "\n"
        
        heading += r"\end{center}"
        
        return heading
    
    def _generate_sections(self, sections: Dict[str, List[str]]) -> str:
        """
        Generate LaTeX code for all resume sections.
        
        Args:
            sections (Dict): Parsed resume sections
            
        Returns:
            str: LaTeX sections code
        """
        latex_output = ""
        
        # Process sections in order of importance
        section_order = ['summary', 'experience', 'education', 'projects', 'skills', 'certifications']
        
        for section_name in section_order:
            if section_name not in sections or not sections[section_name]:
                continue
            
            section_content = sections[section_name]
            
            # Convert markdown bold to LaTeX bold in section content
            section_content = [self._convert_markdown_bold_to_latex(item) for item in section_content]
            
            # Generate section header
            header_name = section_name.upper()
            if section_name == 'experience':
                header_name = "EXPERIENCE"
            elif section_name == 'education':
                header_name = "EDUCATION"
            elif section_name == 'projects':
                header_name = "PROJECTS"
            elif section_name == 'skills':
                header_name = "TECHNICAL SKILLS"
            
            latex_output += f"\n%-----------{header_name.upper()}-----------\n"
            latex_output += f"\\section{{{header_name}}}\n"
            
            # Generate section content based on type
            if section_name == 'skills':
                latex_output += self._format_skills_section(section_content)
            elif section_name == 'summary':
                latex_output += self._format_summary_section(section_content)
            elif section_name in ['experience', 'education']:
                latex_output += self._format_list_section(section_content)
            else:
                latex_output += self._format_list_section(section_content)
        
        return latex_output
    
    def _format_skills_section(self, content: List[str]) -> str:
        """Format technical skills section"""
        latex = " \\begin{itemize}[leftmargin=0.15in, label={}]\n"
        latex += "    \\small{\\item{\n"
        
        skill_lines = []
        for line in content:
            if line.strip():
                skill_lines.append(self._escape_latex(line, preserve_markup=True))
        
        latex += " \\\\ ".join(skill_lines)
        
        latex += "\n    }}\n \\end{itemize}\n"
        return latex
    
    def _format_summary_section(self, content: List[str]) -> str:
        """Format summary/objective section"""
        latex = "  \\resumeSubHeadingListStart\n"
        
        for line in content:
            if line.strip():
                latex += f"    \\resumeItem{{{self._escape_latex(line, preserve_markup=True)}}}\n"
        
        latex += "  \\resumeSubHeadingListEnd\n"
        return latex
    
    def _format_list_section(self, content: List[str]) -> str:
        """Format list-based section (experience, education, projects)"""
        latex = "  \\resumeSubHeadingListStart\n"
        
        current_item = []
        current_subitems = []
        
        for line in content:
            if not line.strip():
                continue
            
            # Check if line starts with bullet (sub-item)
            if line.strip().startswith('•') or line.strip().startswith('-'):
                # This is a sub-item - add to current subitems
                sub_content = line.strip()[1:].strip()
                current_subitems.append(sub_content)
            else:
                # Main item line
                # If we have sub-items, finalize previous item first
                if current_item and current_subitems:
                    latex += self._format_list_item_with_subitems(current_item, current_subitems)
                    current_item = []
                    current_subitems = []
                elif current_item and current_subitems:
                    latex += self._format_list_item(current_item)
                    current_item = []
                
                current_item.append(line)
        
        # Process any remaining items
        if current_item:
            if current_subitems:
                latex += self._format_list_item_with_subitems(current_item, current_subitems)
            else:
                # For items without subitems, wrap content into subitems based on structure
                latex += self._format_experience_item(current_item)
        
        latex += "  \\resumeSubHeadingListEnd\n"
        return latex
    
    def _format_experience_item(self, item_lines: List[str]) -> str:
        """
        Format experience item by parsing structure and adding bullet points.
        
        Handles lines that contain company/title info and description lines.
        """
        if not item_lines:
            return ""
        
        text = ' '.join([l.strip() for l in item_lines])
        lines = text.split('  ')
        
        # First line usually contains title/company/dates
        first_line = lines[0] if lines else text
        
        latex = ""
        
        # If multiple lines exist, treat first as heading and rest as subitems
        if len(lines) > 1:
            # Parse first line to extract title, company, location, dates
            parts = first_line.split(' - ')
            if len(parts) >= 2:
                title = parts[0].strip()
                rest = ' - '.join(parts[1:])
                latex += f"    \\resumeSubheading{{{self._escape_latex(title, preserve_markup=True)}}}{{}}{{}}{{\\small {self._escape_latex(rest, preserve_markup=True)}}}\n"
            else:
                latex += f"    \\resumeItem{{{self._escape_latex(first_line, preserve_markup=True)}}}\n"
            
            # Add remaining lines as bullet points
            for line in lines[1:]:
                if line.strip():
                    latex += f"      \\resumeItem{{{self._escape_latex(line.strip(), preserve_markup=True)}}}\n"
        else:
            # Single line - just add as item
            latex += f"    \\resumeItem{{{self._escape_latex(text, preserve_markup=True)}}}\n"
        
        return latex
    
    def _format_list_item_with_subitems(self, main_lines: List[str], subitems: List[str]) -> str:
        """Format a list item with sub-items"""
        if not main_lines:
            return ""
        
        content = ' '.join([l.strip() for l in main_lines])
        latex = f"    \\resumeSubheading{{}}{{}}{{}}{{\\small {self._escape_latex(content, preserve_markup=True)}}}\n"
        
        for subitem in subitems:
            latex += f"      \\resumeItem{{{self._escape_latex(subitem, preserve_markup=True)}}}\n"
        
        return latex
    
    def _format_list_item(self, item_lines: List[str]) -> str:
        """Format a single list item"""
        if not item_lines:
            return ""
        
        # Try to parse structured format (title | company | details | date)
        content = ' '.join([l.strip() for l in item_lines])
        
        # Look for pipe-separated format
        if '|' in content:
            parts = [p.strip() for p in content.split('|')]
            
            if len(parts) >= 4:
                title, company, details, date = parts[0], parts[1], parts[2], parts[3]
                latex = f"    \\resumeSubheading{{{self._escape_latex(title, preserve_markup=True)}}}{{{self._escape_latex(date, preserve_markup=True)}}}{{{self._escape_latex(details, preserve_markup=True)}}}{{{self._escape_latex(company, preserve_markup=True)}}}\n"
            elif len(parts) >= 3:
                title, company, date = parts[0], parts[1], parts[2]
                latex = f"    \\resumeSubheading{{{self._escape_latex(title, preserve_markup=True)}}}{{{self._escape_latex(date, preserve_markup=True)}}}{{{self._escape_latex(company, preserve_markup=True)}}}{{}} \n"
            else:
                latex = f"    \\resumeItem{{{self._escape_latex(content, preserve_markup=True)}}}\n"
        else:
            latex = f"    \\resumeItem{{{self._escape_latex(content, preserve_markup=True)}}}\n"
        
        return latex
    
    @staticmethod
    @staticmethod
    def _escape_latex(text: str, preserve_markup: bool = True) -> str:
        """
        Escape special LaTeX characters in text while optionally preserving LaTeX markup.
        
        Args:
            text (str): Text to escape (may contain LaTeX commands like \textbf{})
            preserve_markup (bool): If True, preserves LaTeX commands like \textbf{}
            
        Returns:
            str: LaTeX-safe text with markup preserved
        """
        # If preserving markup, temporarily replace LaTeX commands with placeholders
        latex_commands = []
        processed_text = text
        
        if preserve_markup:
            # Find and temporarily replace LaTeX markup like \textbf{...}
            # Pattern: backslash + command name + braced content
            pattern = r'\\textbf\{[^}]*\}|\\textit\{[^}]*\}|\\texttt\{[^}]*\}|\\textmd\{[^}]*\}|\\textrm\{[^}]*\}|\\underline\{[^}]*\}'
            
            placeholders = []
            def replace_command(match):
                latex_commands.append(match.group(0))
                # Use a placeholder with only alphanumeric that won't be escaped
                placeholder = f"XLATEXCMDX{len(latex_commands)-1}XENDX"
                placeholders.append(placeholder)
                return placeholder
            
            processed_text = re.sub(pattern, replace_command, processed_text)
        
        # Order matters: escape backslash first
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
            ('*', r'\*'),
        ]
        
        for old, new in replacements:
            processed_text = processed_text.replace(old, new)
        
        # Restore LaTeX commands if they were preserved
        if preserve_markup:
            for i, cmd in enumerate(latex_commands):
                placeholder = f"XLATEXCMDX{i}XENDX"
                processed_text = processed_text.replace(placeholder, cmd)
        
        return processed_text
    
    @staticmethod
    def _convert_markdown_bold_to_latex(text: str) -> str:
        """
        Convert markdown bold (**text**) to LaTeX bold (\textbf{text}).
        
        Args:
            text (str): Text containing markdown bold formatting
            
        Returns:
            str: Text with markdown bold converted to LaTeX bold
        """
        # Replace **text** with \textbf{text}
        pattern = r'\*\*(.+?)\*\*'
        converted = re.sub(pattern, r'\\textbf{\1}', text)
        return converted
    
    def save_to_file(self, latex_content: str, output_path: Path) -> Path:
        """
        Save LaTeX content to .tex file.
        
        Args:
            latex_content (str): LaTeX document code
            output_path (Path): Path to save .tex file
            
        Returns:
            Path: Path to saved .tex file
        """
        tex_path = output_path.with_suffix('.tex')
        tex_path.write_text(latex_content, encoding='utf-8')
        self.logger.info(f"LaTeX file saved to: {tex_path}")
        
        return tex_path
    
    def compile_to_pdf(self, tex_path: Path, output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Compile LaTeX to PDF using pdflatex.
        
        Args:
            tex_path (Path): Path to .tex file
            output_dir (Optional[Path]): Directory for PDF output (default: same as .tex)
            
        Returns:
            Optional[Path]: Path to generated PDF, or None if compilation failed
        """
        if not self.pdflatex_available:
            self.logger.warning("pdflatex not available, skipping PDF compilation")
            return None
        
        if output_dir is None:
            output_dir = tex_path.parent
        
        try:
            self.logger.info(f"Compiling LaTeX to PDF: {tex_path.name}")
            
            # Run pdflatex
            result = subprocess.run(
                [
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory', str(output_dir),
                    str(tex_path)
                ],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.warning(f"pdflatex returned non-zero exit code: {result.returncode}")
                self.logger.debug(f"pdflatex stderr: {result.stderr}")
                return None
            
            # Find generated PDF
            pdf_path = output_dir / f"{tex_path.stem}.pdf"
            if not pdf_path.exists():
                pdf_path = output_dir / (tex_path.stem + '.pdf')
            
            if pdf_path.exists():
                self.logger.info(f"PDF generated successfully: {pdf_path}")
                
                # Clean up auxiliary files
                self._cleanup_latex_artifacts(output_dir, tex_path.stem)
                
                return pdf_path
            else:
                self.logger.warning(f"PDF file not found after compilation in {output_dir}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("pdflatex compilation timed out")
            return None
        except Exception as e:
            self.logger.error(f"Failed to compile LaTeX to PDF: {str(e)}")
            return None
    
    @staticmethod
    def _cleanup_latex_artifacts(output_dir: Path, stem: str) -> None:
        """
        Clean up temporary LaTeX compilation artifacts.
        
        Args:
            output_dir (Path): Directory containing artifacts
            stem (str): Base filename without extension
        """
        artifacts = ['.aux', '.log', '.out', '.fls', '.fdb_latexmk']
        
        for artifact in artifacts:
            artifact_path = output_dir / (stem + artifact)
            try:
                if artifact_path.exists():
                    artifact_path.unlink()
            except Exception as e:
                logger.debug(f"Could not remove artifact {artifact_path}: {e}")
