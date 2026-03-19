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
  \vspace{{2pt}}\item
    \begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}
      \textbf{{#1}} & \\
      \textit{{\small #3, #2}} & \textit{{\small #4}} \\
    \end{{tabular*}}\vspace{{-5pt}}
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
    
    def generate_pdf(self, resume_text: str, output_path: str, name: str = None, metadata: Dict = None) -> str:
        """
        Generate a PDF resume from tailored text.
        
        Args:
            resume_text (str): The tailored resume text
            output_path (str): Path to save the PDF (without extension)
            name (str, optional): Candidate name to ensure is correctly populated
            
        Returns:
            str: Path to the generated PDF
            
        Raises:
            LatexGeneratorError: If generation fails
        """
        if not self.pdflatex_available:
            raise LatexGeneratorError("pdflatex is not available. Cannot generate PDF.")

        latex_code = self.generate_latex(resume_text, name=name, metadata=metadata)
        
        output_dir = Path(output_path).parent
        output_filename = Path(output_path).name
        
        tex_file_path = output_dir / f"{output_filename}.tex"
        pdf_file_path = output_dir / f"{output_filename}.pdf"
        
        try:
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(latex_code)
            
            # Compile LaTeX to PDF
            # Run pdflatex twice to ensure all cross-references are resolved
            for _ in range(2):
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(output_dir), str(tex_file_path)],
                    check=True,
                    capture_output=True,
                    timeout=30
                )
            
            self.logger.info(f"PDF generated successfully at {pdf_file_path}")
            return str(pdf_file_path)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"pdflatex compilation failed: {e.stderr.decode()}")
            raise LatexGeneratorError(f"pdflatex compilation failed: {e.stderr.decode()}")
        except FileNotFoundError:
            raise LatexGeneratorError("pdflatex command not found. Is LaTeX installed and in your PATH?")
        except Exception as e:
            raise LatexGeneratorError(f"An error occurred during PDF generation: {str(e)}")
        finally:
            # Clean up auxiliary files
            for ext in ['.aux', '.log', '.out', '.fls', '.fdb_latexmk']:
                temp_file = output_dir / f"{output_filename}{ext}"
                if temp_file.exists():
                    temp_file.unlink()
            # Keep .tex file for debugging if needed
            # if tex_file_path.exists():
            #     tex_file_path.unlink()

    def generate_latex(self, resume_text: str, name: str = None, metadata: Dict = None) -> str:
        """
        Convert plain text resume to LaTeX.
        
        Args:
            resume_text (str): Plain text resume content (may contain markdown bold **text**)
            name (str, optional): Candidate name to use for the heading.
            metadata (Dict, optional): Structured metadata (email, phone, linkedin, github)
            
        Returns:
            str: LaTeX document code
            
        Raises:
            LatexGeneratorError: If generation fails
        """
        try:
            # Parse resume sections FIRST (while still in markdown format)
            sections = self._parse_resume_sections(resume_text)
            
            # Determine the name to use
            if name:
                name_to_use = name
            else:
                # Extract name from resume text (usually first line)
                name_to_use = self._extract_name_from_text(resume_text)
            
            # Use metadata for contact info if provided, otherwise extract from text
            contact_info = []
            if metadata:
                for field in ['phone', 'email', 'linkedin', 'github']:
                    if metadata.get(field):
                        contact_info.append(metadata[field])
            
            if not contact_info:
                contact_info = sections.get('contact', [])
                if not contact_info:
                    contact_info = self._extract_contact_from_header(resume_text)
            
            # Generate heading
            heading_latex = self._generate_heading(name_to_use, contact_info)
            
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
    
    def _extract_contact_from_header(self, text: str) -> str:
        """
        Extract contact information from the first few lines of resume.
        
        Looks for phone, email, github, linkedin in the initial lines before
        the first section header.
        
        Args:
            text (str): Resume text
            
        Returns:
            str: Contact information line (may be empty)
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Check lines 2-5 for contact info (after name, title, etc.)
        for line in lines[1:6]:
            # Look for lines containing contact markers like @ (email), + or - (phone),
            # or keywords like github, linkedin
            has_contact_marker = (
                '@' in line or
                ('+' in line and any(c.isdigit() for c in line)) or
                'github' in line.lower() or
                'linkedin' in line.lower()
            )
            
            if has_contact_marker:
                return line
        
        return ""

    def generate_from_structure(self, data: Dict[str, any]) -> str:
        """
        Generate LaTeX from a rich structured JSON data.
        
        Args:
            data (Dict): Structured resume data (as returned by GroqClient.parse_resume)
            
        Returns:
            str: LaTeX document code
        """
        try:
            # 1. Generate Heading
            heading_latex = self._generate_structured_heading(data)
            
            # 2. Generate Sections
            sections_latex = ""
            
            # Summary
            if data.get('summary'):
                sections_latex += "\n%-----------SUMMARY-----------\n"
                sections_latex += "\\section{SUMMARY}\n"
                sections_latex += "  \\resumeSubHeadingListStart\n"
                sections_latex += f"    \\resumeItem{{{self._escape_latex(data['summary'], preserve_markup=True)}}}\n"
                sections_latex += "  \\resumeSubHeadingListEnd\n"
            
            # Technical Skills
            if data.get('skills'):
                sections_latex += "\n%-----------TECHNICAL SKILLS-----------\n"
                sections_latex += "\\section{TECHNICAL SKILLS}\n"
                sections_latex += self._format_structured_skills(data['skills'])
            
            # Experience
            if data.get('experience'):
                sections_latex += "\n%-----------EXPERIENCE-----------\n"
                sections_latex += "\\section{EXPERIENCE}\n"
                sections_latex += self._format_structured_experience(data['experience'])
            
            # Projects
            if data.get('projects'):
                sections_latex += "\n%-----------PROJECTS-----------\n"
                sections_latex += "\\section{PROJECTS}\n"
                sections_latex += self._format_structured_projects(data['projects'])
            
            # Education
            if data.get('education'):
                sections_latex += "\n%-----------EDUCATION-----------\n"
                sections_latex += "\\section{EDUCATION}\n"
                sections_latex += self._format_structured_education(data['education'])
            
            # 3. Fill template
            latex_doc = self.LATEX_TEMPLATE.format(
                heading=heading_latex,
                sections=sections_latex
            )
            
            return latex_doc
            
        except Exception as e:
            self.logger.error(f"Error generating LaTeX from structure: {e}")
            raise LatexGeneratorError(f"Failed to generate structured LaTeX: {str(e)}")

    def _generate_structured_heading(self, data: Dict) -> str:
        """Generate heading from structured contact/socials data"""
        name = data.get('name', 'Your Name')
        contact = data.get('contact', {})
        socials = data.get('socials', {})
        
        email = contact.get('email', '')
        phone = contact.get('phone', '')
        location = contact.get('location', '')
        
        linkedin = socials.get('linkedin', '')
        github = socials.get('github', '')
        portfolio = socials.get('portfolio', '')
        
        heading = r"\begin{center}" + "\n"
        heading += f"    {{\\Huge \\textbf{{{self._escape_latex(name, preserve_markup=False)}}}}} \\\\ \\vspace{{1pt}}\n"
        
        contact_parts = []
        if phone: contact_parts.append(self._escape_latex(phone, preserve_markup=False))
        if email: 
            e = email.strip('<>').strip()
            contact_parts.append(f"\\href{{mailto:{e}}}{{\\underline{{{self._escape_latex(e, preserve_markup=False)}}}}}")
        if linkedin:
            l = linkedin.split('/')[-1] if '/' in linkedin else linkedin
            contact_parts.append(f"\\href{{https://linkedin.com/in/{l}}}{{\\underline{{linkedin.com/in/{self._escape_latex(l, preserve_markup=False)}}}}}")
        if github:
            g = github.split('/')[-1] if '/' in github else github
            contact_parts.append(f"\\href{{https://github.com/{g}}}{{\\underline{{github.com/{self._escape_latex(g, preserve_markup=False)}}}}}")
        
        if contact_parts:
            heading += "    \\small " + " $|$ ".join(contact_parts) + "\n"
        
        heading += r"\end{center}"
        return heading

    def _format_structured_experience(self, experience: List[Dict]) -> str:
        """Format experience section from structured list"""
        latex = "  \\resumeSubHeadingListStart\n"
        for entry in experience:
            company = entry.get('company', '')
            role = entry.get('role', '')
            location = entry.get('location', '')
            dates = entry.get('dates', '')
            achievements = entry.get('achievements', [])
            
            # Format subheading (Role directly below company, as requested)
            # Param 1: Company, Param 2: Location, Param 3: Role, Param 4: Dates
            # But the requirement was "directly below", so we put Role (3) below Company (1)
            latex += f"    \\resumeSubheading{{{self._escape_latex(company, preserve_markup=True)}}}{{{self._escape_latex(location, preserve_markup=True)}}}{{{self._escape_latex(role, preserve_markup=True)}}}{{{self._escape_latex(dates, preserve_markup=True)}}}\n"
            
            latex += "      \\resumeItemListStart\n"
            for ach in achievements:
                if ach.strip():
                    latex += f"        \\resumeItem{{{self._escape_latex(ach, preserve_markup=True)}}}\n"
            latex += "      \\resumeItemListEnd\n"
            latex += "    \\vspace{5pt}\n"
            
        latex += "  \\resumeSubHeadingListEnd\n"
        return latex

    def _format_structured_education(self, education: List[Dict]) -> str:
        """Format education section from structured list"""
        latex = "  \\resumeSubHeadingListStart\n"
        for entry in education:
            school = entry.get('school', '')
            degree = entry.get('degree', '')
            location = entry.get('location', '')
            dates = entry.get('dates', '')
            details = entry.get('details', '')
            
            latex += f"    \\resumeSubheading{{{self._escape_latex(school, preserve_markup=True)}}}{{{self._escape_latex(location, preserve_markup=True)}}}{{{self._escape_latex(degree, preserve_markup=True)}}}{{{self._escape_latex(dates, preserve_markup=True)}}}\n"
            if details:
                latex += "      \\resumeItemListStart\n"
                latex += f"        \\resumeItem{{{self._escape_latex(details, preserve_markup=True)}}}\n"
                latex += "      \\resumeItemListEnd\n"
            latex += "    \\vspace{5pt}\n"
            
        latex += "  \\resumeSubHeadingListEnd\n"
        return latex

    def _format_structured_projects(self, projects: List[Dict]) -> str:
        """Format projects section from structured list"""
        latex = "  \\resumeSubHeadingListStart\n"
        for project in projects:
            title = project.get('title', '')
            tech = project.get('tech_stack', '')
            description = project.get('description', [])
            
            if title:
                header = f"\\textbf{{{self._escape_latex(title, preserve_markup=True)}}}"
                if tech:
                    header += f" $|$ \\emph{{{self._escape_latex(tech, preserve_markup=True)}}}"
                
                latex += f"    \\resumeProjectHeading{{{header}}}{{}}\n"
                latex += "      \\resumeItemListStart\n"
                for desc in description:
                    if desc.strip():
                        latex += f"        \\resumeItem{{{self._escape_latex(desc, preserve_markup=True)}}}\n"
                latex += "      \\resumeItemListEnd\n"
                latex += "    \\vspace{5pt}\n"
                
        latex += "  \\resumeSubHeadingListEnd\n"
        return latex

    def _format_structured_skills(self, skills: Dict) -> str:
        """Format technical skills from structured dictionary"""
        latex = " \\begin{itemize}[leftmargin=0.15in, label={}]\n"
        latex += "    \\small{\\item{\n"
        
        skill_lines = []
        # Sort categories to keep order consistent
        for category in sorted(skills.keys()):
            items = skills[category]
            if items:
                skill_line = f"\\textbf{{{self._escape_latex(category, preserve_markup=True)}}}: "
                if isinstance(items, list):
                    skill_line += ", ".join([self._escape_latex(i, preserve_markup=True) for i in items])
                else:
                    skill_line += self._escape_latex(str(items), preserve_markup=True)
                skill_lines.append(skill_line)
        
        latex += " \\\\ ".join(skill_lines)
        latex += "\n    }}\n \\end{itemize}\n"
        return latex
    
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
            
            # Skip empty lines and unwanted text
            if not line_stripped or "resume built with resuminator" in line_stripped.lower():
                continue
            
            # Check if line is a section header (including markdown headers)
            # Remove markdown formatting for pattern matching
            line_for_matching = line_stripped.strip('*').strip('#').strip('-').strip()
            
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
        
        phone = ""
        email = ""
        linkedin = ""
        github = ""
        
        # Split by pipe first (for pipe-separated formats), then by newline
        contact_parts_raw = []
        if '|' in contact_info:
            contact_parts_raw = [p.strip() for p in contact_info.split('|')]
        else:
            contact_parts_raw = [l.strip() for l in contact_info.split('\n') if l.strip()]
        
        # Parse each part to identify what it is
        for part in contact_parts_raw:
            part_lower = part.lower().strip()
            if not part_lower:
                continue
                
            if '@' in part:
                # Email address
                email = part
            elif 'linkedin' in part_lower or (('/in/' in part_lower or 'linkedin.com' in part_lower) and not github):
                # LinkedIn - may be "LinkedIn: username" or "linkedin.com/in/username" or just "username"
                if ':' in part:
                    linkedin = part.split(':', 1)[1].strip()
                elif '/in/' in part:
                    linkedin = part.split('/in/', 1)[1].strip('/').split('?')[0]
                else:
                    linkedin = part
            elif 'github' in part_lower or (('github.com' in part_lower or 'github' in part_lower) and not linkedin):
                # GitHub - may be "GitHub: username" or "github.com/username" or just "username"
                if ':' in part:
                    github = part.split(':', 1)[1].strip()
                elif 'github.com/' in part:
                    github = part.split('github.com/', 1)[1].strip('/').split('?')[0]
                else:
                    github = part
            elif any(c.isdigit() for c in part) and ('+' in part or '-' in part or part[0].isdigit()):
                # Phone number
                phone = part
        
        # Heuristic: swap if they look obviously wrong (e.g. github handle in linkedin)
        if linkedin and github:
            github_indicators = ['git', 'repo', 'code', 'commit', 'dev', 'acewx']
            linkedin_indicators = ['link', 'profile', 'connect', 'in/']
            
            # If linkedin handle has github indicators AND github handle DOES NOT
            if any(k in linkedin.lower() for k in github_indicators):
                if not any(k in github.lower() for k in github_indicators):
                    linkedin, github = github, linkedin
            # Or vice versa
            elif any(k in github.lower() for k in linkedin_indicators):
                if not any(k in linkedin.lower() for k in linkedin_indicators):
                    linkedin, github = github, linkedin
        
        heading = r"\begin{center}" + "\n"
        heading += f"    {{\\Huge \\textbf{{{self._escape_latex(name, preserve_markup=False)}}}}} \\\\ \\vspace{{1pt}}\n"
        
        # Build contact line
        contact_display_parts = []
        if phone:
            contact_display_parts.append(self._escape_latex(phone, preserve_markup=False))
        if email:
            email_clean = email.strip('<>').strip()
            contact_display_parts.append(f"\\href{{mailto:{email_clean}}}{{\\underline{{{self._escape_latex(email_clean, preserve_markup=False)}}}}}")
        if linkedin:
            linkedin_clean = linkedin.strip()
            contact_display_parts.append(f"\\href{{https://linkedin.com/in/{linkedin_clean}}}{{\\underline{{linkedin.com/in/{self._escape_latex(linkedin_clean, preserve_markup=False)}}}}}")
        if github:
            github_clean = github.strip()
            contact_display_parts.append(f"\\href{{https://github.com/{github_clean}}}{{\\underline{{github.com/{self._escape_latex(github_clean, preserve_markup=False)}}}}}")
        
        if contact_display_parts:
            heading += "    \\small " + " $|$ ".join(contact_display_parts) + "\n"
        
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
                # Guardrail: Add empty section with a placeholder or skip
                # For core sections, we might want to avoid empty environments
                continue
            
            section_content = sections[section_name]
            
            # Convert markdown bold to LaTeX bold in section content
            if isinstance(section_content, list):
                section_content = [self._convert_markdown_bold_to_latex(item) for item in section_content]
            else:
                section_content = self._convert_markdown_bold_to_latex(section_content)
            
            # If after normalization it's still empty, skip entirely
            if not any(item.strip() for item in section_content):
                continue
            
            # Map internal section name to display header
            header_map = {
                'summary': "SUMMARY",
                'experience': "EXPERIENCE",
                'education': "EDUCATION",
                'projects': "PROJECTS",
                'skills': "TECHNICAL SKILLS",
                'certifications': "CERTIFICATIONS"
            }
            header_name = header_map.get(section_name, section_name.upper())
            
            # Create section content
            section_latex = ""
            if section_name == 'skills':
                section_latex = self._format_skills_section(section_content)
            elif section_name == 'summary':
                section_latex = self._format_summary_section(section_content)
            else:
                section_latex = self._format_list_section(section_content)
            
            # ONLY add the section if it has content (prevents empty environment error)
            if section_latex.strip():
                latex_output += f"\n%-----------{header_name}-----------\n"
                latex_output += f"\\section{{{header_name}}}\n"
                latex_output += section_latex
        
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
                
                # Filter out placeholder bullets like "--" or empty ones
                if sub_content and sub_content.strip('-').strip('*').strip():
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
        # Process any remaining items
        if current_item:
            if current_subitems:
                latex += self._format_list_item_with_subitems(current_item, current_subitems)
            else:
                # For items without subitems, wrap content into subitems based on structure
                latex += self._format_experience_item(current_item)
        
        # Add spacing between entries if there are multiple entries
        if latex and not latex.endswith("\\vspace{5pt}\n"):
            latex += "  \\vspace{5pt}\n"
            
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
                # Put the rest (role/location/dates) on the left side (parameter 3)
                latex += f"    \\resumeSubheading{{{self._escape_latex(title, preserve_markup=True)}}}{{}}{{\\small {self._escape_latex(rest, preserve_markup=True)}}}{{}}\n"
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
        
        # Try to parse title/rest in content
        parts = content.split(' - ', 1)
        if len(parts) == 2:
            title, rest = parts[0].strip(), parts[1].strip()
            latex = f"    \\resumeSubheading{{{self._escape_latex(title, preserve_markup=True)}}}{{}}{{}}{{\\small {self._escape_latex(rest, preserve_markup=True)}}}\n"
        else:
            latex = f"    \\resumeSubheading{{}}{{}}{{}}{{\\small {self._escape_latex(content, preserve_markup=True)}}}\n"
        
        for subitem in subitems:
            latex += f"      \\resumeItem{{{LatexResumeGenerator._escape_latex(subitem, preserve_markup=True)}}}\n"
        
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
    def _escape_latex(text: str, preserve_markup: bool = True) -> str:
        """
        Escape special LaTeX characters in text while optionally preserving LaTeX markup.
        
        Args:
            text (str): Text to escape (may contain LaTeX commands like \textbf{})
            preserve_markup (bool): If True, preserves LaTeX commands like \textbf{}
            
        Returns:
            str: LaTeX-safe text with markup preserved
        """
        if text is None:
            return ""
        # If preserving markup, temporarily replace LaTeX commands with placeholders
        latex_commands = []
        processed_text = text
        
        if preserve_markup:
            # Find and temporarily replace LaTeX markup like \textbf{...}
            # Pattern: backslash + command name + braced content
            pattern = r'\\(textbf|textit|texttt|textmd|textrm|underline)\{([^}]*)\}'
            
            placeholders = []
            def replace_command(match):
                command = match.group(1)
                inner_text = match.group(2)
                # Recursively escape the inner text
                escaped_inner = LatexResumeGenerator._escape_latex(inner_text, preserve_markup=False)
                full_cmd = f"\\{command}{{{escaped_inner}}}"
                latex_commands.append(full_cmd)
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
