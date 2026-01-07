"""
Web Image Downloader

Downloads images directly from the web using search engines.
No API keys required - uses web scraping.
"""

from pathlib import Path
from typing import List, Dict
import requests
from PIL import Image
import io
import re
from urllib.parse import quote, urlparse
import time


class WebImageDownloader:
    """Download images directly from web search results."""

    def __init__(self):
        """Initialize web image downloader."""
        self.target_width = 1080
        self.target_height = 1920

        # User agent to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_images(self, script: Dict, output_dir: Path) -> List[Path]:
        """
        Fetch images for all scenes in script.

        Args:
            script: Script dict with hook and scenes
            output_dir: Directory to save images

        Returns:
            List of image file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []

        # Fetch hook image
        hook_query = self._extract_search_query(script['hook']['visual_prompt'])
        hook_path = output_dir / "scene_000_hook.png"
        self._fetch_single_image(hook_query, hook_path)
        image_paths.append(hook_path)

        # Fetch scene images
        for i, scene in enumerate(script['scenes'], 1):
            query = self._extract_search_query(scene['visual_prompt'])
            image_path = output_dir / f"scene_{i:03d}.png"
            self._fetch_single_image(query, image_path)
            image_paths.append(image_path)

        return image_paths

    def _extract_search_query(self, visual_prompt: str) -> str:
        """Extract key search terms from visual prompt."""
        # Remove enhancement words
        stop_words = [
            'vibrant colors', 'high contrast', 'professional photography',
            'trending on instagram', 'vertical composition', 'dramatic lighting',
            'sharp focus', '8k uhd', 'ultra detailed', 'photorealistic'
        ]

        query = visual_prompt.lower()
        for stop_word in stop_words:
            query = query.replace(stop_word, '')

        # Clean up and limit words
        query = ' '.join(query.split()[:5])
        return query.strip()

    def _fetch_single_image(self, query: str, output_path: Path):
        """Fetch a single image from web search."""
        print(f"Searching web for: {query}...")

        try:
            # Try to get image from Unsplash Source (no API key needed!)
            # Unsplash Source provides free random images based on keywords
            keywords = quote(query.replace(' ', ','))
            unsplash_url = f"https://source.unsplash.com/1080x1920/?{keywords}"

            response = requests.get(
                unsplash_url,
                headers=self.headers,
                timeout=30,
                allow_redirects=True
            )

            if response.status_code == 200 and len(response.content) > 1000:
                # Process and save the image
                self._download_and_process_image_from_content(
                    response.content,
                    output_path
                )
                print(f"✓ Downloaded from Unsplash: {query}")
                return
            else:
                print(f"Unsplash failed for: {query}, trying alternative...")

        except Exception as e:
            print(f"Error with Unsplash: {e}, trying alternative...")

        # Fallback: Try Picsum (Lorem Picsum - free placeholder images)
        try:
            # Get a random image in the right dimensions
            picsum_url = "https://picsum.photos/1080/1920"

            # Retry up to 3 times
            for attempt in range(3):
                try:
                    response = requests.get(
                        picsum_url,
                        headers=self.headers,
                        timeout=30,
                        allow_redirects=True
                    )
                    if response.status_code == 200:
                        break
                except requests.Timeout:
                    if attempt < 2:
                        print(f"Timeout, retrying... ({attempt + 1}/3)")
                        time.sleep(1)
                        continue
                    raise

            if response.status_code == 200:
                self._download_and_process_image_from_content(
                    response.content,
                    output_path
                )
                print(f"✓ Downloaded from Picsum: {query}")
                return

        except Exception as e:
            print(f"Error with Picsum: {e}, using placeholder...")

        # Last resort: Create a nice gradient placeholder
        self._create_gradient_placeholder(output_path, query)

    def _download_and_process_image_from_content(self, content: bytes, output_path: Path):
        """Process image from bytes content."""
        try:
            img = Image.open(io.BytesIO(content))

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background

            # Ensure correct dimensions (1080x1920)
            if img.size != (self.target_width, self.target_height):
                # Resize and crop to fit
                img_ratio = img.width / img.height
                target_ratio = self.target_width / self.target_height

                if img_ratio > target_ratio:
                    # Image is wider, scale by height
                    new_height = self.target_height
                    new_width = int(new_height * img_ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    left = (new_width - self.target_width) // 2
                    img = img.crop((left, 0, left + self.target_width, self.target_height))
                else:
                    # Image is taller, scale by width
                    new_width = self.target_width
                    new_height = int(new_width / img_ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    top = (new_height - self.target_height) // 2
                    img = img.crop((0, top, self.target_width, top + self.target_height))

            # Save
            img.save(output_path, "PNG", optimize=True, quality=95)

        except Exception as e:
            print(f"Error processing image: {e}")
            self._create_gradient_placeholder(output_path, str(output_path))

    def _create_gradient_placeholder(self, output_path: Path, text: str):
        """Create an attractive gradient placeholder image."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random

            # Random gradient colors for variety
            colors = [
                ('#667eea', '#764ba2'),  # Purple-Blue
                ('#f093fb', '#f5576c'),  # Pink
                ('#4facfe', '#00f2fe'),  # Blue
                ('#43e97b', '#38f9d7'),  # Green
                ('#fa709a', '#fee140'),  # Orange-Pink
            ]

            color1, color2 = random.choice(colors)

            # Convert hex to RGB
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            rgb1 = hex_to_rgb(color1)
            rgb2 = hex_to_rgb(color2)

            # Create gradient
            img = Image.new('RGB', (self.target_width, self.target_height))
            draw = ImageDraw.Draw(img)

            for y in range(self.target_height):
                # Interpolate between colors
                ratio = y / self.target_height
                r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
                g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
                b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)

                draw.line([(0, y), (self.target_width, y)], fill=(r, g, b))

            # Add subtle text overlay
            display_text = text[:60]
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 80)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                except:
                    font = ImageFont.load_default()

            # Word wrap
            words = display_text.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] < self.target_width - 200:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Draw centered text with shadow
            y_offset = (self.target_height - len(lines) * 100) // 2
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.target_width - text_width) // 2
                y = y_offset + i * 100

                # Shadow
                draw.text((x + 4, y + 4), line, fill=(0, 0, 0, 128), font=font)
                # Text
                draw.text((x, y), line, fill='white', font=font)

            # Save
            img.save(output_path, "PNG", quality=95)
            print(f"Created attractive placeholder: {output_path.name}")

        except Exception as e:
            print(f"Error creating placeholder: {e}")


if __name__ == "__main__":
    # Test web image downloader
    downloader = WebImageDownloader()

    test_script = {
        "hook": {
            "visual_prompt": "Futuristic technology cityscape"
        },
        "scenes": [
            {"visual_prompt": "Modern smartphone with apps"},
            {"visual_prompt": "AI robot in laboratory"}
        ]
    }

    output_dir = Path("test_web_images")
    images = downloader.fetch_images(test_script, output_dir)
    print(f"\nDownloaded {len(images)} images")
