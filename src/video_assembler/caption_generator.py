"""
Caption Generator

Creates styled captions/subtitles for viral reels.
"""

from typing import List, Dict
from pathlib import Path
import re


class CaptionGenerator:
    """Generate and style captions for video overlay."""

    def __init__(
        self,
        font_size: int = 70,
        font_color: str = "white",
        border_width: int = 3,
        position: str = "center"  # 'top', 'center', 'bottom'
    ):
        """
        Initialize caption generator.

        Args:
            font_size: Font size in pixels
            font_color: Font color
            border_width: Border/outline width
            position: Caption position on screen
        """
        self.font_size = font_size
        self.font_color = font_color
        self.border_width = border_width
        self.position = position

    def generate_captions_from_script(self, script: Dict, timings: Dict) -> List[Dict]:
        """
        Generate caption data from script with timing.

        Args:
            script: Script dict with hook and scenes
            timings: Timing dict with start/end times

        Returns:
            List of caption dicts with text, start, end, style
        """
        captions = []

        # Hook caption
        hook_caption = {
            'text': self._format_caption_text(script['hook'].get('text_overlay', script['hook']['text'])),
            'start': timings['hook']['start'],
            'end': timings['hook']['end'],
            'style': 'hook'  # Special styling for hook
        }
        captions.append(hook_caption)

        # Scene captions
        for i, scene in enumerate(script['scenes']):
            caption = {
                'text': self._format_caption_text(scene.get('text_overlay', scene['narration'])),
                'start': timings['scenes'][i]['start'],
                'end': timings['scenes'][i]['end'],
                'style': 'normal'
            }
            captions.append(caption)

        return captions

    def _format_caption_text(self, text: str, max_length: int = 50) -> str:
        """Format caption text for maximum readability."""
        # Uppercase for impact (common in viral content)
        text = text.upper()

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length-3] + "..."

        # Break into lines if needed
        words = text.split()
        if len(words) > 6:
            # Break into 2 lines
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            text = f"{line1}\\N{line2}"

        return text

    def generate_ffmpeg_drawtext(self, captions: List[Dict]) -> List[str]:
        """
        Generate FFmpeg drawtext filter strings for captions.

        Args:
            captions: List of caption dicts

        Returns:
            List of FFmpeg filter strings
        """
        filters = []

        for caption in captions:
            filter_str = self._create_drawtext_filter(
                text=caption['text'],
                start=caption['start'],
                end=caption['end'],
                style=caption.get('style', 'normal')
            )
            filters.append(filter_str)

        return filters

    def _create_drawtext_filter(self, text: str, start: float, end: float, style: str = 'normal') -> str:
        """Create FFmpeg drawtext filter string."""
        # Font path (macOS system font)
        font_path = "/System/Library/Fonts/Supplemental/Impact.ttf"

        # Position based on setting
        if self.position == 'top':
            y_pos = "200"
        elif self.position == 'bottom':
            y_pos = "h-300"
        else:  # center
            y_pos = "(h-text_h)/2"

        # Styling for hook vs normal
        if style == 'hook':
            font_size = int(self.font_size * 1.3)  # Bigger for hook
            border_color = "yellow"
        else:
            font_size = self.font_size
            border_color = "black"

        # Escape special characters for FFmpeg
        text_escaped = text.replace("'", "\\'").replace(":", "\\:")

        filter_str = (
            f"drawtext=fontfile='{font_path}':"
            f"text='{text_escaped}':"
            f"fontsize={font_size}:"
            f"fontcolor={self.font_color}:"
            f"borderw={self.border_width}:"
            f"bordercolor={border_color}:"
            f"x=(w-text_w)/2:"
            f"y={y_pos}:"
            f"enable='between(t,{start},{end})'"
        )

        return filter_str

    def generate_srt_file(self, captions: List[Dict], output_path: Path):
        """
        Generate SRT subtitle file.

        Args:
            captions: List of caption dicts
            output_path: Path to save SRT file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for i, caption in enumerate(captions, 1):
                # SRT index
                f.write(f"{i}\n")

                # Timestamp
                start = self._format_srt_time(caption['start'])
                end = self._format_srt_time(caption['end'])
                f.write(f"{start} --> {end}\n")

                # Text (remove FFmpeg line breaks)
                text = caption['text'].replace('\\N', '\n')
                f.write(f"{text}\n")

                # Blank line
                f.write("\n")

        print(f"SRT file saved: {output_path}")

    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


if __name__ == "__main__":
    # Test caption generation
    generator = CaptionGenerator()

    test_script = {
        "hook": {
            "text": "This will blow your mind!",
            "text_overlay": "MIND BLOWN!"
        },
        "scenes": [
            {
                "narration": "AI can now read thoughts",
                "text_overlay": "AI READS THOUGHTS"
            }
        ]
    }

    test_timings = {
        "hook": {"start": 0.0, "end": 2.0},
        "scenes": [{"start": 2.0, "end": 6.0}]
    }

    captions = generator.generate_captions_from_script(test_script, test_timings)
    print("Generated captions:", captions)

    filters = generator.generate_ffmpeg_drawtext(captions)
    print("\nFFmpeg filters:", filters)
