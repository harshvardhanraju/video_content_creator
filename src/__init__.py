"""
ReelForge: Open-Source Viral Reel Generator

A complete pipeline for generating engaging Instagram/YouTube Reels
from text inputs, optimized for M4 Mac with 16GB RAM.
"""

__version__ = "0.1.0"
__author__ = "ReelForge Contributors"

from . import input_processor
from . import script_generator
from . import tts_generator
from . import image_generator
from . import video_assembler
from . import cli

__all__ = [
    "input_processor",
    "script_generator",
    "tts_generator",
    "image_generator",
    "video_assembler",
    "cli",
]
