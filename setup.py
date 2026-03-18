from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jobs-automaton",
    version="0.1.0",
    author="Your Name",
    description="Resume tailoring and job automation pipeline using AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jobs-automaton",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "groq==0.4.1",
        "pypdf==4.0.1",
        "python-docx==0.8.11",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "flask==3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "black==23.12.1",
            "flake8==6.1.0",
        ],
    },
)
