"""
Command-line interface for the resume tailoring pipeline.

Provides easy-to-use commands for:
- Single resume tailoring
- Batch tailoring
- Job description analysis
- ATS score calculation
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from src.core.resume_tailor import TailorPipeline, PipelineConfig, TailorPipelineError
from src.core.resume_parser import ResumeParser, ResumeParseError
from src.utils.ats_optimizer import ATSOptimizer
from src.groq_client.client import GroqClient, GroqClientError


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/tailoring.log')
        ]
    )


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_ats_score(score_dict: dict):
    """Pretty print ATS score breakdown"""
    score = score_dict['overall_score']
    print(f"📊 Overall ATS Score: {score}/100")
    
    if score >= 80:
        rating = "✅ Excellent"
    elif score >= 70:
        rating = "👍 Good"
    elif score >= 60:
        rating = "⚠️  Fair"
    else:
        rating = "❌ Low"
    
    print(f"   Rating: {rating}\n")
    print(f"   Breakdown:")
    print(f"   - Keywords:    {score_dict['keyword_score']:.1f}/50")
    print(f"   - Formatting:  {score_dict['format_score']:.1f}/20")
    print(f"   - Content:     {score_dict['content_score']:.1f}/15")
    print(f"   - Readability: {score_dict['readability_score']:.1f}/15")


def cmd_tailor(args):
    """Handle resume tailoring command"""
    print_section("Resume Tailoring")
    
    try:
        # Validate inputs
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume file not found: {args.resume}")
            return 1
        
        job_input = args.job
        if not Path(job_input).exists() and len(job_input) < 100:
            print(f"❌ Job description file not found and text seems too short: {job_input}")
            return 1
        
        # Initialize pipeline
        print("Initializing pipeline...")
        pipeline = TailorPipeline()
        
        # Run tailoring
        print(f"Processing resume: {resume_path.name}")
        print(f"Job description: {job_input if len(job_input) < 50 else 'provided'}")
        print()
        
        result = pipeline.tailor(
            str(resume_path),
            job_input,
            output_format=args.output_format
        )
        
        if not result['success']:
            print("❌ Tailoring failed")
            return 1
        
        # Display results
        print_section("Tailoring Complete ✅")
        
        print(f"📄 Original Resume: {result['original_ats_score']}/100")
        print(f"📄 Tailored Resume: {result['final_ats_score']}/100")
        print(f"📈 Improvement:     +{result['ats_improvement']} points ({result['ats_improvement_percentage']}%)")
        print()
        
        print("ATS Score Breakdown:")
        print_ats_score(result['report'])
        
        print(f"\n📁 Output saved to: {result['output_file']}")
        print(f"⏱️  Processing time: {result['processing_time_seconds']:.1f}s")
        
        if result['key_changes']:
            print(f"\n🔄 Key Changes Made:")
            for change in result['key_changes'][:5]:
                print(f"   • {change}")
        
        if result['matched_keywords']:
            print(f"\n✓ Keywords Found ({len(result['matched_keywords'])}):")
            for kw in result['matched_keywords'][:10]:
                print(f"   • {kw}")
        
        if result['missing_keywords']:
            print(f"\n⚠️  Keywords Missing ({len(result['missing_keywords'])}):")
            for kw in result['missing_keywords'][:5]:
                print(f"   • {kw}")
        
        print("\n✨ Resume ready to submit!")
        return 0
        
    except TailorPipelineError as e:
        print(f"❌ Pipeline error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def cmd_batch(args):
    """Handle batch tailoring command"""
    print_section("Batch Resume Tailoring")
    
    try:
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume file not found: {args.resume}")
            return 1
        
        jobs_dir = Path(args.jobs_directory)
        if not jobs_dir.exists():
            print(f"❌ Jobs directory not found: {args.jobs_directory}")
            return 1
        
        # Initialize pipeline
        print("Initializing pipeline...")
        pipeline = TailorPipeline()
        
        # Run batch tailoring
        print(f"Processing resume: {resume_path.name}")
        print(f"Jobs directory: {jobs_dir}\n")
        
        results = pipeline.batch_tailor(
            str(resume_path),
            str(jobs_dir),
            output_format=args.output_format
        )
        
        # Display results
        print_section("Batch Tailoring Complete ✅")
        
        print(f"Total jobs processed: {results['total_jobs']}")
        print(f"✅ Successful: {results['successful']}")
        print(f"❌ Failed: {results['failed']}")
        
        if results['successful'] > 0:
            print(f"\n📈 Average ATS Improvement: +{results['average_ats_improvement']} points")
        
        print(f"\nDetailed results for each job:")
        for job_name, result in results['tailored_resumes'].items():
            score_change = f"+{result['ats_improvement']}" if result['ats_improvement'] >= 0 else str(result['ats_improvement'])
            print(f"  • {job_name}: {result['original_ats_score']} → {result['final_ats_score']} ({score_change})")
        
        if results['errors']:
            print(f"\nErrors encountered:")
            for job_name, error in results['errors'].items():
                print(f"  • {job_name}: {error}")
        
        return 0
        
    except TailorPipelineError as e:
        print(f"❌ Pipeline error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def cmd_analyze_job(args):
    """Handle job analysis command"""
    print_section("Job Description Analysis")
    
    try:
        # Load job description
        job_input = args.job_description
        job_path = Path(job_input)
        
        if job_path.exists():
            job_description = job_path.read_text()
        else:
            job_description = job_input
        
        if not job_description.strip():
            print("❌ Job description is empty")
            return 1
        
        # Initialize Groq client
        print("Analyzing job description with AI...")
        groq_client = GroqClient()
        
        analysis = groq_client.analyze_job_description(job_description)
        
        # Display results
        print_section("Analysis Results ✅")
        
        if 'job_title' in analysis:
            print(f"📌 Job Title: {analysis['job_title']}\n")
        
        if 'required_skills' in analysis:
            print("🔧 Required Skills:")
            for skill in analysis['required_skills']:
                print(f"   • {skill}")
            print()
        
        if 'required_experience' in analysis:
            print("💼 Required Experience:")
            for exp in analysis['required_experience']:
                print(f"   • {exp}")
            print()
        
        if 'key_responsibilities' in analysis:
            print("📋 Key Responsibilities:")
            for resp in analysis['key_responsibilities']:
                print(f"   • {resp}")
            print()
        
        if 'keywords' in analysis:
            print("🔑 ATS Keywords (for resume matching):")
            for kw in analysis['keywords'][:15]:
                print(f"   • {kw}")
        
        return 0
        
    except GroqClientError as e:
        print(f"❌ API error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def cmd_check_ats(args):
    """Handle ATS score checking command"""
    print_section("ATS Score Check")
    
    try:
        resume_path = Path(args.resume)
        if not resume_path.exists():
            print(f"❌ Resume file not found: {args.resume}")
            return 1
        
        job_input = args.job_description
        job_path = Path(job_input)
        
        if job_path.exists():
            job_description = job_path.read_text()
        else:
            job_description = job_input
        
        if not job_description.strip():
            print("❌ Job description is empty")
            return 1
        
        # Parse resume
        print("Parsing resume...")
        parser = ResumeParser()
        parsed_resume = parser.parse(str(resume_path))
        
        # Calculate ATS score
        print("Calculating ATS score...")
        optimizer = ATSOptimizer()
        ats_score = optimizer.calculate_ats_score(
            parsed_resume['normalized_text'],
            job_description,
            parsed_resume['sections']
        )
        
        # Display results
        print_section("ATS Score Results ✅")
        
        print_ats_score(ats_score)
        
        print(f"✓ Keywords Matched: {len(ats_score['matched_keywords'])}")
        print(f"  Examples: {', '.join(ats_score['matched_keywords'][:5]) if ats_score['matched_keywords'] else 'None'}")
        
        print(f"\n⚠️  Keywords Missing: {len(ats_score['missing_keywords'])}")
        print(f"  Top suggestions: {', '.join(ats_score['missing_keywords'][:5]) if ats_score['missing_keywords'] else 'None'}")
        
        # Generate report
        report = optimizer.generate_optimization_report(ats_score, parsed_resume['normalized_text'], job_description)
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        return 0
        
    except ResumeParseError as e:
        print(f"❌ Resume parsing error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        prog='jobs-automaton',
        description='AI-powered resume tailoring and job automation pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tailor resume for a job
  python -m src.cli tailor --resume resume.pdf --job job_description.txt

  # Batch tailor for multiple jobs
  python -m src.cli batch --resume resume.pdf --jobs-directory ./jobs_dir

  # Analyze job description to extract keywords
  python -m src.cli analyze-job --job job_description.txt

  # Check ATS score of resume for specific job
  python -m src.cli check-ats --resume resume.pdf --job job_description.txt
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Tailor command
    tailor_parser = subparsers.add_parser('tailor', help='Tailor resume for a job')
    tailor_parser.add_argument('-r', '--resume', required=True, help='Path to resume file (PDF/DOCX)')
    tailor_parser.add_argument('-j', '--job', required=True, help='Job description file or text')
    tailor_parser.add_argument('-of', '--output-format', default='txt', choices=['txt', 'json'],
                              help='Output format (default: txt)')
    tailor_parser.set_defaults(func=cmd_tailor)
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch tailor resume for multiple jobs')
    batch_parser.add_argument('-r', '--resume', required=True, help='Path to resume file')
    batch_parser.add_argument('-jd', '--jobs-directory', required=True, help='Directory containing job files')
    batch_parser.add_argument('-of', '--output-format', default='txt', choices=['txt', 'json'],
                             help='Output format (default: txt)')
    batch_parser.set_defaults(func=cmd_batch)
    
    # Analyze job command
    analyze_parser = subparsers.add_parser('analyze-job', help='Analyze job description')
    analyze_parser.add_argument('-j', '--job-description', required=True, help='Job description file or text')
    analyze_parser.set_defaults(func=cmd_analyze_job)
    
    # Check ATS command
    check_ats_parser = subparsers.add_parser('check-ats', help='Check ATS score for resume')
    check_ats_parser.add_argument('-r', '--resume', required=True, help='Path to resume file')
    check_ats_parser.add_argument('-j', '--job-description', required=True, help='Job description file or text')
    check_ats_parser.set_defaults(func=cmd_check_ats)
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Initialize directories
    PipelineConfig.initialize_directories()
    
    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
