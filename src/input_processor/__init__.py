"""
Input Processor Module

Handles various input formats (text, MD, PDF) and normalizes
them into a structured format for the script generator.
"""

from .text_parser import TextParser
from .pdf_parser import PDFParser

__all__ = ["TextParser", "PDFParser"]
