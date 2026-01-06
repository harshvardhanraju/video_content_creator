"""
LLM-based Script Generator

Uses Llama 3.2 (3B) via MLX to generate viral-optimized reel scripts.
"""

import json
from typing import Dict, List
from pathlib import Path

try:
    from mlx_lm import load, generate
    HAS_MLX = True
except ImportError:
    HAS_MLX = False
    print("Warning: mlx_lm not installed. Install with: pip install mlx-lm")


class ScriptGenerator:
    """Generate viral-optimized scripts using LLM."""

    def __init__(self, model_name: str = "mlx-community/Llama-3.2-3B-Instruct-4bit"):
        """
        Initialize script generator.

        Args:
            model_name: HuggingFace model ID (MLX format)
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None

        if HAS_MLX:
            self._load_model()

    def _load_model(self):
        """Load the LLM model."""
        print(f"Loading model: {self.model_name}...")
        try:
            self.model, self.tokenizer = load(self.model_name)
            print("Model loaded successfully!")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Model will be downloaded on first use.")

    def generate_script(self, input_data: Dict) -> Dict:
        """
        Generate a viral-optimized script from input data.

        Args:
            input_data: Dict with title, key_points, context, target_length

        Returns:
            Dict with hook, scenes, and total_duration
        """
        if not HAS_MLX:
            return self._generate_mock_script(input_data)

        # Create prompt
        prompt = self._create_prompt(input_data)

        # Generate script
        try:
            response = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=1500,
                temp=0.7,
                top_p=0.9
            )

            # Parse response
            script = self._parse_response(response, input_data['target_length'])
            return script

        except Exception as e:
            print(f"Error generating script: {e}")
            return self._generate_mock_script(input_data)

    def _create_prompt(self, input_data: Dict) -> str:
        """Create the LLM prompt for script generation."""
        title = input_data['title']
        key_points = input_data.get('key_points', [])
        target_length = input_data['target_length']

        # Calculate scene count (3-5 sec per scene)
        num_scenes = max(5, min(8, target_length // 5))

        prompt = f"""Create a viral Instagram/YouTube Reel script about: "{title}"

Target duration: {target_length} seconds
Number of scenes: {num_scenes}

Key points to cover:
{chr(10).join(f"- {point}" for point in key_points[:6])}

Requirements:
1. Start with a STRONG HOOK (1-2 seconds) that grabs attention immediately
2. Break content into {num_scenes} fast-paced scenes
3. Each scene needs:
   - Punchy narration (max 10 words)
   - Visual description for image generation
   - Text overlay for captions
4. Use simple, conversational language
5. Create pattern interrupts every 3-5 seconds
6. End with a call-to-action or cliffhanger

Output format (JSON):
{{
    "hook": {{
        "text": "Attention-grabbing hook text",
        "duration": 2.0,
        "visual_prompt": "Description for image generation",
        "text_overlay": "Text to display"
    }},
    "scenes": [
        {{
            "narration": "Short, punchy narration",
            "duration": 5.0,
            "visual_prompt": "Detailed image description",
            "text_overlay": "Caption text"
        }}
    ]
}}

Generate the script now:"""

        return prompt

    def _parse_response(self, response: str, target_length: int) -> Dict:
        """Parse LLM response into structured script."""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                script = json.loads(json_str)

                # Calculate total duration
                total = script['hook']['duration']
                for scene in script['scenes']:
                    total += scene['duration']

                script['total_duration'] = total
                return script

        except Exception as e:
            print(f"Error parsing response: {e}")

        # Fallback to mock script
        return self._generate_mock_script({"title": "Content", "key_points": [], "target_length": target_length})

    def _generate_mock_script(self, input_data: Dict) -> Dict:
        """Generate a mock script for testing without LLM."""
        title = input_data.get('title', 'Amazing Topic')
        target_length = input_data.get('target_length', 45)
        key_points = input_data.get('key_points', [])

        # Create hook
        hook = {
            "text": f"Wait... did you know about {title}?",
            "duration": 2.0,
            "visual_prompt": f"Eye-catching visual related to {title}, vibrant colors, high contrast",
            "text_overlay": "WAIT!"
        }

        # Create scenes from key points
        scenes = []
        time_per_scene = max(4, (target_length - 2) // max(len(key_points), 5))

        for i, point in enumerate(key_points[:6]):
            scene = {
                "narration": point[:80] if len(point) > 80 else point,
                "duration": float(time_per_scene),
                "visual_prompt": f"Visual representation of: {point}, cinematic, vibrant",
                "text_overlay": point[:50]
            }
            scenes.append(scene)

        # Add final scene if needed
        if len(scenes) < 5:
            scenes.append({
                "narration": "Follow for more insights!",
                "duration": 3.0,
                "visual_prompt": "Call to action visual, engaging, colorful",
                "text_overlay": "FOLLOW FOR MORE!"
            })

        total_duration = hook['duration'] + sum(s['duration'] for s in scenes)

        return {
            "hook": hook,
            "scenes": scenes,
            "total_duration": total_duration
        }

    def save_script(self, script: Dict, output_path: Path):
        """Save script to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)

        print(f"Script saved to: {output_path}")


if __name__ == "__main__":
    # Test the generator
    generator = ScriptGenerator()

    test_input = {
        "title": "AI Transforming Healthcare",
        "key_points": [
            "AI can diagnose diseases faster than doctors",
            "Machine learning predicts patient outcomes",
            "Personalized treatment plans using AI"
        ],
        "context": "AI is revolutionizing healthcare...",
        "target_length": 45
    }

    script = generator.generate_script(test_input)
    print(json.dumps(script, indent=2))
