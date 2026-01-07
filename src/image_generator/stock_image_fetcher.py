"""
Stock Image Fetcher

Fetches relevant stock images from online sources (Pexels, Unsplash, Pixabay).
Much faster and better quality than diffusion models.
"""

from pathlib import Path
from typing import List, Dict, Optional
import requests
from PIL import Image
import io
import os


class StockImageFetcher:
    """Fetch stock images from free APIs."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize stock image fetcher.

        Args:
            api_key: Pexels API key (get free at https://www.pexels.com/api/)
                    If not provided, will try to read from PEXELS_API_KEY env var
        """
        self.api_key = api_key or os.getenv('PEXELS_API_KEY')
        self.pexels_base_url = "https://api.pexels.com/v1/search"

        # Image dimensions for 9:16 aspect ratio
        self.target_width = 1080
        self.target_height = 1920

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
        self._fetch_single_image(hook_query, hook_path, is_hook=True)
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
        # Remove enhancement words that don't help with stock image search
        stop_words = [
            'vibrant colors', 'high contrast', 'professional photography',
            'trending on instagram', 'vertical composition', 'dramatic lighting',
            'sharp focus', '8k uhd', 'ultra detailed', 'photorealistic'
        ]

        query = visual_prompt.lower()
        for stop_word in stop_words:
            query = query.replace(stop_word, '')

        # Clean up and take first few important words
        query = ' '.join(query.split()[:5])  # Limit to 5 words
        return query.strip()

    def _fetch_single_image(self, query: str, output_path: Path, is_hook: bool = False):
        """Fetch a single image from Pexels."""
        try:
            print(f"Fetching image: {query}...")

            if not self.api_key:
                print("WARNING: No Pexels API key found. Using placeholder.")
                print("Get a free key at: https://www.pexels.com/api/")
                self._create_placeholder_image(output_path, query)
                return

            # Search Pexels for vertical/portrait orientation images
            headers = {"Authorization": self.api_key}
            params = {
                "query": query,
                "orientation": "portrait",  # Vertical images
                "per_page": 15,  # Get multiple options
                "size": "large"
            }

            response = requests.get(
                self.pexels_base_url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('photos') and len(data['photos']) > 0:
                    # Pick a random photo from results for variety
                    import random
                    photo_index = 0 if is_hook else random.randint(0, min(14, len(data['photos']) - 1))
                    photo = data['photos'][photo_index]

                    # Download the portrait/large2x image
                    image_url = photo['src'].get('large2x') or photo['src'].get('large')
                    self._download_and_process_image(image_url, output_path)
                    print(f"✓ Fetched: {query}")
                else:
                    print(f"No images found for: {query}, using placeholder")
                    self._create_placeholder_image(output_path, query)
            else:
                print(f"API error ({response.status_code}), using placeholder")
                self._create_placeholder_image(output_path, query)

        except Exception as e:
            print(f"Error fetching image: {e}")
            self._create_placeholder_image(output_path, query)

    def _download_and_process_image(self, url: str, output_path: Path):
        """Download and process image to correct size."""
        try:
            # Download image
            response = requests.get(url, timeout=15)
            img = Image.open(io.BytesIO(response.content))

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background

            # Resize to 1080x1920 (9:16) maintaining aspect ratio and cropping
            img_ratio = img.width / img.height
            target_ratio = self.target_width / self.target_height

            if img_ratio > target_ratio:
                # Image is wider, crop width
                new_height = self.target_height
                new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Center crop
                left = (new_width - self.target_width) // 2
                img = img.crop((left, 0, left + self.target_width, self.target_height))
            else:
                # Image is taller, crop height
                new_width = self.target_width
                new_height = int(new_width / img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Center crop
                top = (new_height - self.target_height) // 2
                img = img.crop((0, top, self.target_width, top + self.target_height))

            # Save
            img.save(output_path, "PNG", optimize=True, quality=95)

        except Exception as e:
            print(f"Error processing image: {e}")
            self._create_placeholder_image(output_path, url)

    def _create_placeholder_image(self, output_path: Path, text: str):
        """Create a placeholder image with gradient and text."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create gradient image
            img = Image.new('RGB', (self.target_width, self.target_height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)

            # Add gradient effect
            for y in range(self.target_height):
                color_val = int(26 + (y / self.target_height) * 100)
                draw.line(
                    [(0, y), (self.target_width, y)],
                    fill=(color_val, color_val, color_val + 40)
                )

            # Add text (query summary)
            display_text = text[:80]
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
            except:
                font = ImageFont.load_default()

            # Center text with word wrap
            words = display_text.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] < self.target_width - 100:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Draw centered lines
            y_offset = (self.target_height - len(lines) * 60) // 2
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.target_width - text_width) // 2
                y = y_offset + i * 60
                draw.text((x, y), line, fill='white', font=font)

            # Save
            img.save(output_path, "PNG")
            print(f"Created placeholder: {output_path.name}")

        except Exception as e:
            print(f"Error creating placeholder: {e}")


if __name__ == "__main__":
    # Test stock image fetcher
    fetcher = StockImageFetcher()

    test_script = {
        "hook": {
            "visual_prompt": "Morning sunrise over city skyline, golden hour"
        },
        "scenes": [
            {"visual_prompt": "Person checking smartphone weather app"},
            {"visual_prompt": "Blue sky with white fluffy clouds"}
        ]
    }

    output_dir = Path("test_stock_images")
    images = fetcher.fetch_images(test_script, output_dir)
    print(f"\\nFetched {len(images)} images")
