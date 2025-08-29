#!/usr/bin/env python3
"""
Install and setup dependencies for German Legal Dataset preparation
"""

import subprocess
import sys
import os

def install_packages():
    """Install required Python packages"""
    packages = [
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "pdfplumber==0.10.3",
        "pandas==2.1.4",
        "datasets==2.16.1",
        "huggingface_hub==0.20.3",
        "tqdm==4.66.1",
        "langdetect==1.0.9",
        "pypdf==3.17.4",
        "spacy==3.7.2",
        "transformers==4.36.2",
        "torch==2.1.2",
        "numpy==1.24.4",
        "scikit-learn==1.3.2",
        "lxml==4.9.3"
    ]
    
    print("Installing Python packages...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")

def download_spacy_model():
    """Download German spaCy model"""
    try:
        print("Downloading German spaCy model...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "de_core_news_sm"])
        print("✓ German spaCy model downloaded")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download spaCy model: {e}")

def setup_huggingface():
    """Setup HuggingFace Hub"""
    try:
        print("Setting up HuggingFace Hub...")
        from huggingface_hub import login
        print("HuggingFace Hub setup complete (login manually if needed)")
        print("✓ HuggingFace Hub ready")
    except ImportError:
        print("✗ HuggingFace Hub not available")

if __name__ == "__main__":
    print("Setting up German Legal Dataset preparation environment...")
    install_packages()
    download_spacy_model()
    setup_huggingface()
    print("Setup complete!")