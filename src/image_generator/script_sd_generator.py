"""
Script-Aware Stable Diffusion Image Generator

Generates AI images specifically tailored to research-based scripts,
using narration context, topic category, and visual prompts together.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import random
from dataclasses import dataclass

try:
    import torch
    from diffusers import (
        StableDiffusionPipeline,
        StableDiffusionXLPipeline,
        DPMSolverMultistepScheduler,
        EulerAncestralDiscreteScheduler
    )
    from PIL import Image
    HAS_DIFFUSERS = True
except ImportError:
    HAS_DIFFUSERS = False
    print("Warning: diffusers not installed. Install with: pip install diffusers torch")


@dataclass
class StylePreset:
    """Style preset for different content categories."""
    positive_modifiers: List[str]
    negative_modifiers: List[str]
    guidance_scale: float
    num_steps: int


# Style presets based on content category
STYLE_PRESETS = {
    "politics": StylePreset(
        positive_modifiers=[
            "photojournalistic style",
            "news photography",
            "professional press photo",
            "high contrast",
            "dramatic lighting",
            "editorial photography"
        ],
        negative_modifiers=[
            "cartoon", "anime", "illustration", "painting",
            "low quality", "blurry", "watermark", "text overlay"
        ],
        guidance_scale=8.0,
        num_steps=30
    ),
    "military": StylePreset(
        positive_modifiers=[
            "documentary photography",
            "war photography style",
            "cinematic",
            "dramatic shadows",
            "high detail",
            "gritty realistic"
        ],
        negative_modifiers=[
            "cartoon", "anime", "cheerful", "bright colors",
            "low quality", "blurry", "watermark"
        ],
        guidance_scale=8.5,
        num_steps=30
    ),
    "technology": StylePreset(
        positive_modifiers=[
            "futuristic",
            "sleek modern design",
            "blue tech lighting",
            "professional product photography",
            "clean minimalist",
            "high tech aesthetic"
        ],
        negative_modifiers=[
            "vintage", "old", "rusty", "dirty",
            "low quality", "blurry", "watermark"
        ],
        guidance_scale=7.5,
        num_steps=28
    ),
    "economy": StylePreset(
        positive_modifiers=[
            "corporate photography",
            "business professional",
            "modern office aesthetic",
            "clean composition",
            "professional lighting",
            "stock photo quality"
        ],
        negative_modifiers=[
            "casual", "messy", "cartoon", "anime",
            "low quality", "blurry", "watermark"
        ],
        guidance_scale=7.5,
        num_steps=25
    ),
    "news": StylePreset(
        positive_modifiers=[
            "breaking news style",
            "photojournalism",
            "press photography",
            "urgent mood",
            "high contrast",
            "professional news photography"
        ],
        negative_modifiers=[
            "cartoon", "anime", "peaceful", "serene",
            "low quality", "blurry", "watermark", "text"
        ],
        guidance_scale=8.0,
        num_steps=28
    ),
    "default": StylePreset(
        positive_modifiers=[
            "professional photography",
            "high quality",
            "sharp focus",
            "good lighting",
            "detailed",
            "8k uhd"
        ],
        negative_modifiers=[
            "low quality", "blurry", "distorted",
            "ugly", "watermark", "text overlay"
        ],
        guidance_scale=7.5,
        num_steps=25
    )
}


class ScriptSDGenerator:
    """
    Generates AI images using Stable Diffusion based on script context.

    Features:
    - Uses narration + visual_prompt for context-aware generation
    - Applies category-specific style presets
    - Supports both SD 1.5 and SDXL models
    - Optimized for M4 Mac with MPS
    """

    def __init__(
        self,
        model_type: str = "sd15",  # "sd15" or "sdxl"
        device: str = "auto",
        use_refiner: bool = False
    ):
        """
        Initialize the script-aware SD generator.

        Args:
            model_type: "sd15" for SD 1.5, "sdxl" for SDXL (higher quality but slower)
            device: "auto", "mps", "cuda", or "cpu"
            use_refiner: Use SDXL refiner for higher quality (SDXL only)
        """
        self.model_type = model_type
        self.use_refiner = use_refiner and model_type == "sdxl"

        # Auto-detect device
        if device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device

        self.pipe = None
        self.refiner = None

        # Image dimensions for 9:16 aspect ratio
        if model_type == "sdxl":
            # SDXL native resolution
            self.width = 768
            self.height = 1344  # Close to 9:16
        else:
            # SD 1.5 resolution
            self.width = 576
            self.height = 1024

        # Final output resolution
        self.target_width = 1080
        self.target_height = 1920

        if HAS_DIFFUSERS:
            self._load_model()

    def _load_model(self):
        """Load the Stable Diffusion model."""
        print(f"Loading Stable Diffusion model ({self.model_type})...")

        try:
            if self.model_type == "sdxl":
                self._load_sdxl()
            else:
                self._load_sd15()

            print(f"Model loaded on {self.device}")

        except Exception as e:
            print(f"Error loading model: {e}")
            print("Will generate placeholder images instead")
            self.pipe = None

    def _load_sd15(self):
        """Load Stable Diffusion 1.5 model."""
        model_id = "runwayml/stable-diffusion-v1-5"

        # Use float32 on MPS to avoid NaN issues
        torch_dtype = torch.float32 if self.device == "mps" else torch.float16

        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            safety_checker=None
        )

        # Use DPM++ scheduler for faster, quality generation
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config
        )

        self.pipe = self.pipe.to(self.device)
        self.pipe.enable_attention_slicing()

        # Enable memory optimizations on MPS
        if self.device == "mps":
            self.pipe.enable_attention_slicing("max")

    def _load_sdxl(self):
        """Load Stable Diffusion XL model."""
        model_id = "stabilityai/stable-diffusion-xl-base-1.0"

        # SDXL requires float16
        torch_dtype = torch.float16 if self.device != "cpu" else torch.float32

        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            variant="fp16" if torch_dtype == torch.float16 else None
        )

        # Use Euler Ancestral for SDXL
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
            self.pipe.scheduler.config
        )

        self.pipe = self.pipe.to(self.device)

        # Memory optimizations
        if self.device == "mps":
            self.pipe.enable_attention_slicing("max")
        else:
            self.pipe.enable_model_cpu_offload()

    def generate_images(
        self,
        script: Dict,
        output_dir: Path,
        seed: Optional[int] = None
    ) -> List[Path]:
        """
        Generate images for all scenes in a research-based script.

        Args:
            script: Script dict with hook, scenes, category, research_summary
            output_dir: Directory to save images
            seed: Random seed for reproducibility

        Returns:
            List of image file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []

        # Get content category and style preset
        category = script.get('category', 'default').lower()
        style = STYLE_PRESETS.get(category, STYLE_PRESETS['default'])

        # Get research context for better prompts
        research_context = script.get('research_summary', '')

        print(f"Generating images for category: {category}")
        print(f"Using style preset with {style.num_steps} steps, guidance {style.guidance_scale}")

        # Combine hook and scenes
        scenes = []
        if 'hook' in script:
            scenes.append(script['hook'])
        scenes.extend(script.get('scenes', []))

        for i, scene in enumerate(scenes):
            # Build context-aware prompt
            prompt = self._build_prompt(scene, category, research_context, style)
            negative = ", ".join(style.negative_modifiers)

            image_path = output_dir / f"scene_{i:02d}.png"

            print(f"\nScene {i+1}/{len(scenes)}:")
            print(f"  Prompt: {prompt[:100]}...")

            success = self._generate_image(
                prompt=prompt,
                negative_prompt=negative,
                output_path=image_path,
                style=style,
                seed=seed + i if seed else None
            )

            if success:
                image_paths.append(image_path)
            else:
                # Create fallback
                fallback = self._create_fallback_image(output_dir, i, scene)
                image_paths.append(fallback)

        return image_paths

    def _build_prompt(
        self,
        scene: Dict,
        category: str,
        research_context: str,
        style: StylePreset
    ) -> str:
        """
        Build an optimized prompt from scene data and context.

        Combines:
        - Visual prompt from script
        - Narration context for subject matter
        - Category-specific style modifiers
        - Research context for accuracy
        """
        parts = []

        # Start with visual prompt
        visual_prompt = scene.get('visual_prompt', '')
        if visual_prompt:
            # Clean up generic placeholder words
            cleaned = visual_prompt.replace('Image of', '').replace('Image', '')
            cleaned = cleaned.strip().strip(',').strip()
            parts.append(cleaned)

        # Add context from narration
        narration = scene.get('narration', scene.get('text', ''))
        if narration:
            # Extract key subjects from narration
            subjects = self._extract_subjects(narration)
            if subjects:
                parts.append(subjects)

        # Add keywords if available
        keywords = scene.get('image_search_keywords', [])
        relevant_keywords = [k for k in keywords if k.lower() not in ['image', 'security']]
        if relevant_keywords:
            parts.append(", ".join(relevant_keywords[:3]))

        # Add style modifiers
        style_mods = ", ".join(style.positive_modifiers[:4])

        # Combine everything
        base_prompt = ", ".join(filter(None, parts))
        full_prompt = f"{base_prompt}, {style_mods}"

        # Add vertical composition hint
        full_prompt += ", vertical portrait composition, centered subject"

        return full_prompt

    def _extract_subjects(self, narration: str) -> str:
        """Extract key subjects from narration for prompt."""
        # Simple keyword extraction
        important_words = []

        # Look for proper nouns (capitalized words)
        words = narration.split()
        for word in words:
            clean = word.strip('.,!?"\':')
            if len(clean) > 2 and clean[0].isupper():
                if clean.lower() not in ['the', 'and', 'but', 'for', 'with']:
                    important_words.append(clean)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for w in important_words:
            if w.lower() not in seen:
                seen.add(w.lower())
                unique.append(w)

        return ", ".join(unique[:4])

    def _generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        output_path: Path,
        style: StylePreset,
        seed: Optional[int] = None
    ) -> bool:
        """Generate a single image."""
        if not HAS_DIFFUSERS or self.pipe is None:
            return False

        try:
            # Set up generator for reproducibility
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
            else:
                generator = torch.Generator(device=self.device).manual_seed(
                    random.randint(0, 2147483647)
                )

            print(f"  Generating at {self.width}x{self.height}...")

            with torch.inference_mode():
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=style.num_steps,
                    guidance_scale=style.guidance_scale,
                    width=self.width,
                    height=self.height,
                    generator=generator
                )

            image = result.images[0]

            # Upscale to target resolution
            print(f"  Upscaling to {self.target_width}x{self.target_height}...")
            image = image.resize(
                (self.target_width, self.target_height),
                Image.Resampling.LANCZOS
            )

            # Save
            image.save(output_path, "PNG", quality=95)
            print(f"  Saved: {output_path.name}")

            return True

        except Exception as e:
            print(f"  Error: {e}")
            return False

    def _create_fallback_image(
        self,
        output_dir: Path,
        index: int,
        scene: Dict
    ) -> Path:
        """Create a fallback gradient image with scene context."""
        from PIL import ImageDraw, ImageFont

        image = Image.new('RGB', (self.target_width, self.target_height))
        draw = ImageDraw.Draw(image)

        # Create gradient based on scene index for variety
        hue_offset = (index * 30) % 360
        for y in range(self.target_height):
            progress = y / self.target_height
            r = int(20 + progress * 40 + (hue_offset % 30))
            g = int(20 + progress * 30)
            b = int(40 + progress * 50)
            draw.line([(0, y), (self.target_width, y)], fill=(r, g, b))

        # Add subtle text overlay
        text_overlay = scene.get('text_overlay', '')
        if text_overlay:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                font = ImageFont.load_default()

            # Center text
            bbox = draw.textbbox((0, 0), text_overlay, font=font)
            text_w = bbox[2] - bbox[0]
            x = (self.target_width - text_w) // 2
            y = self.target_height // 2

            # Draw with shadow
            draw.text((x+2, y+2), text_overlay, fill=(0, 0, 0, 128), font=font)
            draw.text((x, y), text_overlay, fill=(255, 255, 255), font=font)

        output_path = output_dir / f"scene_{index:02d}.png"
        image.save(output_path, 'PNG')
        print(f"  Created fallback: {output_path.name}")

        return output_path


def generate_for_script(script_path: str, output_dir: str, model_type: str = "sd15"):
    """
    Utility function to generate images for a script file.

    Args:
        script_path: Path to script.json
        output_dir: Directory to save images
        model_type: "sd15" or "sdxl"
    """
    import json

    with open(script_path, 'r') as f:
        script = json.load(f)

    generator = ScriptSDGenerator(model_type=model_type)
    paths = generator.generate_images(script, Path(output_dir))

    print(f"\nGenerated {len(paths)} images:")
    for p in paths:
        print(f"  - {p}")

    return paths


if __name__ == "__main__":
    # Test with a sample script
    test_script = {
        "category": "military",
        "research_summary": "US military operation in Venezuela",
        "hook": {
            "text": "Breaking: US captures Venezuelan President",
            "visual_prompt": "military operation, dramatic news scene",
            "text_overlay": "BREAKING NEWS",
            "image_search_keywords": ["military", "Venezuela", "news"]
        },
        "scenes": [
            {
                "narration": "President Trump announces capture of Maduro",
                "visual_prompt": "presidential announcement, podium, flags",
                "text_overlay": "Trump announces strike",
                "image_search_keywords": ["Trump", "president", "announcement"]
            },
            {
                "narration": "US forces conducted operation in Caracas",
                "visual_prompt": "military forces, night operation, city",
                "text_overlay": "Operation in Venezuela",
                "image_search_keywords": ["military", "operation", "forces"]
            }
        ]
    }

    output_dir = Path("test_sd_images")
    generator = ScriptSDGenerator(model_type="sd15")

    paths = generator.generate_images(test_script, output_dir)
    print(f"\nGenerated {len(paths)} images")
