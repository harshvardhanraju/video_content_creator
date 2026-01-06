"""
PDF Parser

Extracts text and key information from research papers and PDFs.
"""

from pathlib import Path
from typing import Dict, List
import re

try:
    import PyPDF2
    import pdfplumber
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False


class PDFParser:
    """Parse PDF documents (research papers) into structured data."""

    def __init__(self):
        if not HAS_PDF_SUPPORT:
            raise ImportError(
                "PDF support requires PyPDF2 and pdfplumber. "
                "Install with: pip install PyPDF2 pdfplumber"
            )

    def parse(self, pdf_path: Path, target_length: int = 45) -> Dict:
        """
        Parse a PDF file and extract key information.

        Args:
            pdf_path: Path to PDF file
            target_length: Target duration in seconds

        Returns:
            Dict with title, key_points, context, target_length
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Extract text using pdfplumber (better formatting)
        text = self._extract_text(pdf_path)

        # Extract title from first page
        title = self._extract_title(text)

        # Extract key points (abstract, conclusions, etc.)
        key_points = self._extract_key_points(text)

        return {
            "title": title,
            "key_points": key_points,
            "context": text[:2000],  # First 2000 chars as context
            "target_length": target_length
        }

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract all text from PDF."""
        text_parts = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:10]:  # First 10 pages only
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return '\n\n'.join(text_parts)

    def _extract_title(self, text: str) -> str:
        """Extract paper title from text."""
        # Title is usually in the first few lines
        lines = text.split('\n')[:20]

        # Look for title-like patterns
        for line in lines:
            line = line.strip()
            # Skip common header items
            if any(skip in line.lower() for skip in ['arxiv', 'preprint', 'abstract', 'doi']):
                continue
            # Title is usually longer and not all caps
            if len(line) > 20 and not line.isupper():
                return line[:150]  # Max 150 chars

        # Fallback: first substantial line
        for line in lines:
            if len(line.strip()) > 20:
                return line.strip()[:150]

        return "Research Paper"

    def _extract_key_points(self, text: str, max_points: int = 8) -> List[str]:
        """Extract key points from paper (abstract, conclusions, etc.)."""
        key_points = []

        # Find abstract
        abstract = self._extract_section(text, 'abstract')
        if abstract:
            # Split abstract into sentences
            sentences = re.split(r'[.!?]+', abstract)
            key_points.extend([s.strip() for s in sentences if len(s.strip()) > 30][:4])

        # Find conclusions/summary
        conclusions = self._extract_section(text, 'conclusion|summary')
        if conclusions:
            sentences = re.split(r'[.!?]+', conclusions)
            key_points.extend([s.strip() for s in sentences if len(s.strip()) > 30][:4])

        # If not enough points, extract from introduction
        if len(key_points) < 4:
            intro = self._extract_section(text, 'introduction')
            if intro:
                sentences = re.split(r'[.!?]+', intro)
                key_points.extend([s.strip() for s in sentences if len(s.strip()) > 30][:4])

        return key_points[:max_points]

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a specific section from the paper."""
        # Case-insensitive section search
        pattern = rf'\b({section_name})\b(.+?)(?=\b(introduction|methods|results|references|acknowledgments)\b|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(2).strip()[:1000]  # Max 1000 chars per section

        return ""


if __name__ == "__main__":
    # Test the parser (requires a PDF file)
    parser = PDFParser()
    print("PDF parser initialized successfully")
