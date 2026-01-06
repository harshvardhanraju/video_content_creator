"""
ReelForge Setup Script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="reelforge",
    version="0.1.0",
    description="Open-source viral reel generator for M4 Mac",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ReelForge Contributors",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "mlx>=0.19.0",
        "mlx-lm>=0.18.0",
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "diffusers>=0.25.0",
        "accelerate>=0.25.0",
        "safetensors>=0.4.0",
        "Pillow>=10.0.0",
        "moviepy>=1.0.3",
        "ffmpeg-python>=0.2.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "tqdm>=4.66.0",
        "click>=8.1.0",
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0",
        "PyPDF2>=3.0.0",
        "pdfplumber>=0.10.0",
        "markdown>=3.5.0",
        "beautifulsoup4>=4.12.0",
    ],
    entry_points={
        "console_scripts": [
            "reelforge=src.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="video reel instagram youtube ai llm stable-diffusion tts",
)
