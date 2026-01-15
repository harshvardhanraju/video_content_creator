"""
Smart Image Fetcher with Semantic Matching

Searches multiple free stock photo APIs and uses CLIP
for semantic similarity to find the best matching images.
"""

import os
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
from io import BytesIO
import time

# CLIP imports (will be loaded on demand)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

CLIP_MODEL = None
CLIP_PROCESSOR = None


@dataclass
class ImageCandidate:
    """Represents a candidate image from search."""
    url: str
    source: str  # pexels, unsplash, pixabay, openverse
    title: str
    width: int
    height: int
    thumbnail_url: Optional[str] = None
    similarity_score: float = 0.0


class SmartImageFetcher:
    """
    Fetches images from multiple APIs and ranks them by semantic similarity.
    """

    def __init__(
        self,
        pexels_api_key: Optional[str] = None,
        use_clip: bool = True,
        candidates_per_source: int = 5
    ):
        """
        Initialize the smart image fetcher.

        Args:
            pexels_api_key: Optional Pexels API key (enables higher quality results)
            use_clip: Whether to use CLIP for semantic matching
            candidates_per_source: Number of candidates to fetch from each source
        """
        self.pexels_api_key = pexels_api_key or os.getenv('PEXELS_API_KEY')
        self.use_clip = use_clip and HAS_TORCH
        self.candidates_per_source = candidates_per_source

        # Target dimensions for vertical video
        self.target_width = 1080
        self.target_height = 1920

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SmartImageFetcher/1.0'
        })

        # Load CLIP model if needed
        if self.use_clip:
            self._load_clip_model()

    def _load_clip_model(self):
        """Load CLIP model for semantic matching."""
        global CLIP_MODEL, CLIP_PROCESSOR

        if CLIP_MODEL is not None:
            return

        try:
            from transformers import CLIPProcessor, CLIPModel

            print("Loading CLIP model for semantic image matching...")
            model_name = "openai/clip-vit-base-patch32"

            CLIP_PROCESSOR = CLIPProcessor.from_pretrained(model_name)
            CLIP_MODEL = CLIPModel.from_pretrained(model_name)

            # Move to GPU if available
            if torch.cuda.is_available():
                CLIP_MODEL = CLIP_MODEL.cuda()
            elif torch.backends.mps.is_available():
                CLIP_MODEL = CLIP_MODEL.to("mps")

            CLIP_MODEL.eval()
            print("CLIP model loaded successfully!")

        except Exception as e:
            print(f"Warning: Could not load CLIP model: {e}")
            print("Falling back to keyword-based matching only.")
            self.use_clip = False

    def fetch_images(self, script: Dict, output_dir: Path) -> List[Path]:
        """
        Fetch semantically matched images for each scene.

        Args:
            script: Script dict with hook and scenes
            output_dir: Directory to save images

        Returns:
            List of paths to downloaded images
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        scenes = [script.get('hook', {})] + script.get('scenes', [])

        for i, scene in enumerate(scenes):
            # Extract search context
            narration = scene.get('narration', scene.get('text', ''))
            visual_prompt = scene.get('visual_prompt', '')
            keywords = scene.get('image_search_keywords', [])

            # Build search query
            search_query = self._build_search_query(narration, visual_prompt, keywords)

            print(f"Scene {i+1}: Searching for '{search_query[:50]}...'")

            # Get candidate images from multiple sources
            candidates = self._search_all_sources(search_query)

            if not candidates:
                print(f"  No candidates found, using fallback...")
                fallback_path = self._create_fallback_image(output_dir, i)
                image_paths.append(fallback_path)
                continue

            # Rank candidates by semantic similarity
            if self.use_clip and narration:
                candidates = self._rank_by_similarity(candidates, narration)
                best = candidates[0]
                print(f"  Best match: {best.source} (score: {best.similarity_score:.3f})")
            else:
                best = candidates[0]
                print(f"  Selected: {best.source}")

            # Download best candidate
            image_path = output_dir / f"scene_{i:02d}.png"
            success = self._download_and_process(best, image_path)

            if success:
                image_paths.append(image_path)
            else:
                # Try next best candidates
                for candidate in candidates[1:4]:
                    if self._download_and_process(candidate, image_path):
                        image_paths.append(image_path)
                        break
                else:
                    fallback_path = self._create_fallback_image(output_dir, i)
                    image_paths.append(fallback_path)

        return image_paths

    def _build_search_query(
        self,
        narration: str,
        visual_prompt: str,
        keywords: List[str]
    ) -> str:
        """Build an optimized search query from scene data."""
        # Extract key terms from narration
        narration_words = [w for w in narration.split() if len(w) > 3][:5]

        # Use keywords if available
        if keywords:
            query_parts = keywords[:3]
        else:
            query_parts = narration_words[:3]

        # Add visual context
        if visual_prompt:
            visual_words = [w for w in visual_prompt.split() if len(w) > 3][:2]
            query_parts.extend(visual_words)

        # Deduplicate and join
        seen = set()
        unique_parts = []
        for part in query_parts:
            part_lower = part.lower().strip('.,!?')
            if part_lower not in seen and len(part_lower) > 2:
                seen.add(part_lower)
                unique_parts.append(part)

        return ' '.join(unique_parts[:5])

    def _search_all_sources(self, query: str) -> List[ImageCandidate]:
        """Search all available image sources."""
        candidates = []

        # Search each source
        sources = [
            ('unsplash', self._search_unsplash),
            ('pexels', self._search_pexels),
            ('pixabay', self._search_pixabay),
            ('picsum', self._search_picsum),  # Fallback for variety
        ]

        for source_name, search_func in sources:
            try:
                results = search_func(query)
                candidates.extend(results)
                if results:
                    print(f"    {source_name}: {len(results)} candidates")
            except Exception as e:
                print(f"    {source_name}: failed ({e})")

        # If no candidates found, ensure we have picsum fallback
        if not candidates:
            print("    No results from APIs, using picsum fallback...")
            candidates = self._search_picsum(query)

        return candidates

    def _search_unsplash(self, query: str) -> List[ImageCandidate]:
        """Search Unsplash for images using source.unsplash.com."""
        candidates = []

        try:
            # Use source.unsplash.com which doesn't require API key
            # Generate multiple candidate URLs with different seeds
            import random

            keywords = query.replace(' ', ',')[:50]

            for i in range(self.candidates_per_source):
                # Use random seed for variety
                seed = random.randint(1, 10000)
                url = f"https://source.unsplash.com/1080x1920/?{keywords}&sig={seed}"

                candidates.append(ImageCandidate(
                    url=url,
                    source='unsplash',
                    title=query[:100],
                    width=1080,
                    height=1920,
                    thumbnail_url=url.replace('1080x1920', '200x350')
                ))

        except Exception as e:
            pass

        return candidates

    def _search_pexels(self, query: str) -> List[ImageCandidate]:
        """Search Pexels for images."""
        candidates = []

        if not self.pexels_api_key:
            return candidates

        try:
            headers = {'Authorization': self.pexels_api_key}
            search_url = "https://api.pexels.com/v1/search"
            params = {
                'query': query,
                'per_page': self.candidates_per_source,
                'orientation': 'portrait'
            }

            response = self.session.get(
                search_url,
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                for photo in data.get('photos', []):
                    src = photo.get('src', {})
                    candidates.append(ImageCandidate(
                        url=src.get('large2x', src.get('large', '')),
                        source='pexels',
                        title=photo.get('alt', '')[:100] or query,
                        width=photo.get('width', 1080),
                        height=photo.get('height', 1920),
                        thumbnail_url=src.get('tiny')
                    ))

        except Exception as e:
            pass

        return candidates

    def _search_pixabay(self, query: str) -> List[ImageCandidate]:
        """Search Pixabay for images (requires API key)."""
        candidates = []

        api_key = os.getenv('PIXABAY_API_KEY')
        if not api_key:
            return candidates

        try:
            search_url = "https://pixabay.com/api/"
            params = {
                'key': api_key,
                'q': query,
                'per_page': self.candidates_per_source,
                'orientation': 'vertical',
                'image_type': 'photo',
                'safesearch': 'true'
            }

            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for hit in data.get('hits', []):
                    candidates.append(ImageCandidate(
                        url=hit.get('largeImageURL', ''),
                        source='pixabay',
                        title=hit.get('tags', '')[:100] or query,
                        width=hit.get('imageWidth', 1080),
                        height=hit.get('imageHeight', 1920),
                        thumbnail_url=hit.get('previewURL')
                    ))

        except Exception as e:
            pass

        return candidates

    def _search_picsum(self, query: str) -> List[ImageCandidate]:
        """Get random high-quality images from Picsum (fallback)."""
        candidates = []

        try:
            import random

            for i in range(self.candidates_per_source):
                # Picsum provides random images by ID
                image_id = random.randint(1, 1000)
                url = f"https://picsum.photos/id/{image_id}/1080/1920"

                candidates.append(ImageCandidate(
                    url=url,
                    source='picsum',
                    title=query[:100],
                    width=1080,
                    height=1920,
                    thumbnail_url=f"https://picsum.photos/id/{image_id}/200/350"
                ))

        except Exception as e:
            pass

        return candidates

    def _rank_by_similarity(
        self,
        candidates: List[ImageCandidate],
        text: str
    ) -> List[ImageCandidate]:
        """Rank candidates by CLIP semantic similarity to text."""
        global CLIP_MODEL, CLIP_PROCESSOR

        if not CLIP_MODEL or not candidates:
            return candidates

        try:
            # Encode text
            text_inputs = CLIP_PROCESSOR(
                text=[text],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77
            )

            # Move to device
            device = next(CLIP_MODEL.parameters()).device
            text_inputs = {k: v.to(device) for k, v in text_inputs.items()}

            with torch.no_grad():
                text_features = CLIP_MODEL.get_text_features(**text_inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Score each candidate
            for candidate in candidates:
                try:
                    score = self._compute_image_similarity(
                        candidate,
                        text_features,
                        device
                    )
                    candidate.similarity_score = score
                except Exception:
                    candidate.similarity_score = 0.0

            # Sort by similarity (highest first)
            candidates.sort(key=lambda x: x.similarity_score, reverse=True)

        except Exception as e:
            print(f"    Warning: CLIP ranking failed: {e}")

        return candidates

    def _compute_image_similarity(
        self,
        candidate: ImageCandidate,
        text_features: torch.Tensor,
        device
    ) -> float:
        """Compute CLIP similarity score for an image candidate."""
        global CLIP_MODEL, CLIP_PROCESSOR

        # Download thumbnail or small version
        image_url = candidate.thumbnail_url or candidate.url

        try:
            response = self.session.get(image_url, timeout=5)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content)).convert('RGB')

            # Process image
            image_inputs = CLIP_PROCESSOR(
                images=image,
                return_tensors="pt"
            )
            image_inputs = {k: v.to(device) for k, v in image_inputs.items()}

            with torch.no_grad():
                image_features = CLIP_MODEL.get_image_features(**image_inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Compute cosine similarity
            similarity = (text_features @ image_features.T).item()
            return similarity

        except Exception:
            return 0.0

    def _download_and_process(
        self,
        candidate: ImageCandidate,
        output_path: Path
    ) -> bool:
        """Download and process image to target dimensions."""
        try:
            response = self.session.get(candidate.url, timeout=30)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content)).convert('RGB')

            # Crop to 9:16 aspect ratio
            processed = self._crop_to_aspect(image)

            # Resize to target dimensions
            processed = processed.resize(
                (self.target_width, self.target_height),
                Image.Resampling.LANCZOS
            )

            processed.save(output_path, 'PNG', quality=95)
            return True

        except Exception as e:
            return False

    def _crop_to_aspect(self, image: Image.Image) -> Image.Image:
        """Crop image to 9:16 aspect ratio (vertical video)."""
        width, height = image.size
        target_ratio = 9 / 16  # 0.5625

        current_ratio = width / height

        if current_ratio > target_ratio:
            # Image is too wide, crop sides
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            image = image.crop((left, 0, left + new_width, height))
        else:
            # Image is too tall, crop top/bottom
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            image = image.crop((0, top, width, top + new_height))

        return image

    def _create_fallback_image(self, output_dir: Path, index: int) -> Path:
        """Create a fallback gradient image."""
        from PIL import ImageDraw

        image = Image.new('RGB', (self.target_width, self.target_height))
        draw = ImageDraw.Draw(image)

        # Create gradient
        for y in range(self.target_height):
            r = int(30 + (y / self.target_height) * 50)
            g = int(30 + (y / self.target_height) * 30)
            b = int(60 + (y / self.target_height) * 40)
            draw.line([(0, y), (self.target_width, y)], fill=(r, g, b))

        output_path = output_dir / f"scene_{index:02d}.png"
        image.save(output_path, 'PNG')

        return output_path


if __name__ == "__main__":
    # Test the smart image fetcher
    fetcher = SmartImageFetcher(use_clip=True)

    test_script = {
        "hook": {
            "text": "Breaking news about Trump and Venezuela",
            "visual_prompt": "news broadcast, president, politics",
            "image_search_keywords": ["Trump", "Venezuela", "president"]
        },
        "scenes": [
            {
                "narration": "President Trump announces military operation",
                "visual_prompt": "military operation, government",
                "image_search_keywords": ["military", "president", "announcement"]
            },
            {
                "narration": "Venezuelan president Maduro captured",
                "visual_prompt": "Venezuela, capture, news",
                "image_search_keywords": ["Venezuela", "news", "politics"]
            }
        ]
    }

    output_dir = Path("test_smart_images")
    paths = fetcher.fetch_images(test_script, output_dir)

    print(f"\nDownloaded {len(paths)} images:")
    for p in paths:
        print(f"  - {p}")
