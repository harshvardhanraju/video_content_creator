"""
Text Parser

Processes text inputs, markdown files, and topics into structured data.
"""

import re
from pathlib import Path
from typing import Dict, List, Union
import markdown
from bs4 import BeautifulSoup


class TextParser:
    """Parse and normalize text inputs for reel generation."""

    def __init__(self):
        self.md_parser = markdown.Markdown()

    def parse(self, input_data: Union[str, Path], target_length: int = 45) -> Dict:
        """
        Parse input and return structured data.

        Args:
            input_data: Text string, file path, or topic
            target_length: Target duration in seconds

        Returns:
            Dict with title, key_points, context, target_length
        """
        if isinstance(input_data, Path) or (isinstance(input_data, str) and Path(input_data).exists()):
            return self._parse_file(Path(input_data), target_length)
        else:
            return self._parse_text(str(input_data), target_length)

    def _parse_file(self, file_path: Path, target_length: int) -> Dict:
        """Parse a markdown or text file."""
        content = file_path.read_text(encoding='utf-8')

        if file_path.suffix.lower() in ['.md', '.markdown']:
            return self._parse_markdown(content, target_length)
        else:
            return self._parse_text(content, target_length)

    def _parse_markdown(self, content: str, target_length: int) -> Dict:
        """Parse markdown content."""
        # Convert markdown to HTML then extract text
        html = self.md_parser.convert(content)
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title (first h1 or h2)
        title_tag = soup.find(['h1', 'h2'])
        title = title_tag.get_text() if title_tag else self._extract_title_from_text(content)

        # Extract key points (list items, headers)
        key_points = []

        # Get list items
        for li in soup.find_all('li'):
            key_points.append(li.get_text().strip())

        # Get headers (h2, h3) as key points if no lists
        if not key_points:
            for header in soup.find_all(['h2', 'h3']):
                key_points.append(header.get_text().strip())

        # Get plain text as context
        text = soup.get_text()

        return {
            "title": title,
            "key_points": key_points[:8],  # Limit to 8 key points
            "context": text,
            "target_length": target_length
        }

    def _parse_text(self, text: str, target_length: int) -> Dict:
        """Parse plain text input."""
        # Try to extract title from first line
        lines = text.strip().split('\n')
        title = self._extract_title_from_text(text)

        # Extract key points (sentences or paragraphs)
        key_points = self._extract_key_points(text)

        return {
            "title": title,
            "key_points": key_points,
            "context": text,
            "target_length": target_length
        }

    def _extract_title_from_text(self, text: str) -> str:
        """Extract or generate title from text."""
        lines = text.strip().split('\n')

        # First non-empty line as title
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Clean up and limit length
                title = re.sub(r'^[#\-*]+\s*', '', line)
                return title[:100]  # Max 100 chars

        # If no good title, use first few words
        words = text.split()[:8]
        return ' '.join(words)

    def _extract_key_points(self, text: str, max_points: int = 8) -> List[str]:
        """Extract key points from text."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        # Clean and filter
        key_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 20:  # Meaningful sentences
                key_points.append(sentence)
                if len(key_points) >= max_points:
                    break

        # If not enough sentences, split into paragraphs
        if len(key_points) < 3:
            paragraphs = text.split('\n\n')
            key_points = [p.strip() for p in paragraphs if p.strip()][:max_points]

        return key_points


if __name__ == "__main__":
    # Test the parser
    parser = TextParser()

    # Test with simple text
    result = parser.parse("AI is revolutionizing healthcare through better diagnosis and treatment.")
    print("Text parsing result:", result)
