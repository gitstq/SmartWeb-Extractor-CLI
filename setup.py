#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartWeb-Extractor-CLI Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="smartweb-extractor-cli",
    version="1.0.0",
    author="SmartWeb Team",
    author_email="hello@smartweb.dev",
    description="🧠 AI-Powered Intelligent Web Content Structured Extraction Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/SmartWeb-Extractor-CLI",
    py_modules=["smartweb_extractor"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: Chinese (Traditional)",
    ],
    keywords=[
        "web-scraping",
        "content-extraction",
        "html-parser",
        "data-extraction",
        "cli-tool",
        "ai-powered",
        "structured-data",
        "zero-dependency",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "smartweb-extractor=smartweb_extractor:main",
            "swe=smartweb_extractor:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/gitstq/SmartWeb-Extractor-CLI/issues",
        "Source": "https://github.com/gitstq/SmartWeb-Extractor-CLI",
        "Documentation": "https://github.com/gitstq/SmartWeb-Extractor-CLI#readme",
    },
)
