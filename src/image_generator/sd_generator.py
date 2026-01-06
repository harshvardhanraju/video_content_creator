"""
Stable Diffusion Image Generator

Generates scene images optimized for vertical (9:16) reels.
"""

from pathlib import Path
from typing import List, Dict
import random

try:
    import torch
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    from PIL import Image
    HAS_DIFFUSERS = True
except ImportError:
    HAS_DIFFUSERS = False
    print("Warning: diffusers not installed. Install with: pip install diffusers torch")


class ImageGenerator:
    """Generate images using Stable Diffusion."""

    def __init__(
        self,
        model_id: str = "runwayml/stable-diffusion-v1-5",
        device: str = "mps"  # Use Metal Performance Shaders on Mac
    ):
        """
        Initialize image generator.

        Args:
            model_id: HuggingFace model ID
            device: Device to run on (mps, cpu, cuda)
        """
        self.model_id = model_id
        self.device = device
        self.pipe = None

        # Image dimensions for 9:16 aspect ratio
        self.width = 576  # Divisible by 64
        self.height = 1024  # 9:16 ratio, divisible by 64

        if HAS_DIFFUSERS:
            self._load_model()

    def _load_model(self):
        """Load Stable Diffusion model."""
        print(f"Loading Stable Diffusion model: {self.model_id}...")

        try:
            # Load with optimizations for Mac
            self.pipe = StableDiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                safety_checker=None  # Disable for speed
            )

            # Use faster scheduler
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipe.scheduler.config
            )

            # Move to device
            if self.device == "mps":
                try:
                    self.pipe = self.pipe.to("mps")
                    print("Using Metal Performance Shaders (MPS)")
                except Exception as e:
                    print(f"MPS not available: {e}, falling back to CPU")
                    self.device = "cpu"
                    self.pipe = self.pipe.to("cpu")
            else:
                self.pipe = self.pipe.to(self.device)

            # Enable memory optimizations
            self.pipe.enable_attention_slicing()

            print("Model loaded successfully!")

        except Exception as e:
            print(f"Error loading model: {e}")
            print("Will generate placeholder images instead")
            self.pipe = None

    def generate_images(self, script: Dict, output_dir: Path) -> List[Path]:
        """
        Generate images for all scenes in script.

        Args:
            script: Script dict with hook and scenes
            output_dir: Directory to save images

        Returns:
            List of image file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []

        # Generate hook image
        hook_prompt = self._enhance_prompt(script['hook']['visual_prompt'])
        hook_path = output_dir / "scene_000_hook.png"
        self._generate_single_image(hook_prompt, hook_path)
        image_paths.append(hook_path)

        # Generate scene images
        for i, scene in enumerate(script['scenes'], 1):
            prompt = self._enhance_prompt(scene['visual_prompt'])
            image_path = output_dir / f"scene_{i:03d}.png"
            self._generate_single_image(prompt, image_path)
            image_paths.append(image_path)

        return image_paths

    def _enhance_prompt(self, base_prompt: str) -> str:
        """Enhance prompt for viral social media content."""
        enhancements = [
            "vibrant colors",
            "high contrast",
            "professional photography",
            "trending on instagram",
            "vertical composition",
            "dramatic lighting",
            "sharp focus",
            "8k uhd"
        ]

        # Add negative prompts internally
        enhanced = f"{base_prompt}, {', '.join(enhancements)}"
        return enhanced

    def _generate_single_image(self, prompt: str, output_path: Path):
        """Generate a single image."""
        if not HAS_DIFFUSERS or self.pipe is None:
            return self._create_placeholder_image(output_path, prompt)

        try:
            print(f"Generating: {output_path.name}...")

            # Generate image
            with torch.inference_mode():
                result = self.pipe(
                    prompt=prompt,
                    negative_prompt="blurry, low quality, distorted, ugly, bad anatomy, watermark",
                    num_inference_steps=25,  # Balance quality vs speed
                    guidance_scale=7.5,
                    width=self.width,
                    height=self.height,
                    generator=torch.Generator(device=self.device).manual_seed(random.randint(0, 1000000))
                )

            image = result.images[0]

            # Resize to final resolution (1080x1920)
            image = image.resize((1080, 1920), Image.Resampling.LANCZOS)

            # Save
            image.save(output_path, "PNG", optimize=True)
            print(f"Saved: {output_path}")

        except Exception as e:
            print(f"Error generating image: {e}")
            self._create_placeholder_image(output_path, prompt)

    def _create_placeholder_image(self, output_path: Path, prompt: str):
        """Create a placeholder image with gradient and text."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create gradient image
            img = Image.new('RGB', (1080, 1920), color='#1a1a2e')
            draw = ImageDraw.Draw(img)

            # Add gradient effect
            for y in range(1920):
                color_val = int(26 + (y / 1920) * 100)
                draw.line([(0, y), (1080, y)], fill=(color_val, color_val, color_val + 40))

            # Add text (prompt summary)
            text = prompt[:100]
            try:
                # Try to use a nice font
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            except:
                font = ImageFont.load_default()

            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (1080 - text_width) // 2
            y = (1920 - text_height) // 2

            draw.text((x, y), text, fill='white', font=font)

            # Save
            img.save(output_path, "PNG")
            print(f"Created placeholder: {output_path}")

        except Exception as e:
            print(f"Error creating placeholder: {e}")


if __name__ == "__main__":
    # Test image generation
    generator = ImageGenerator()

    test_script = {
        "hook": {
            "visual_prompt": "Futuristic AI brain, glowing circuits, cyberpunk style"
        },
        "scenes": [
            {
                "visual_prompt": "Scientists in modern laboratory with brain scans"
            },
            {
                "visual_prompt": "Person wearing brain-computer interface headset"
            }
        ]
    }

    output_dir = Path("test_images")
    images = generator.generate_images(test_script, output_dir)
    print(f"Generated {len(images)} images")
