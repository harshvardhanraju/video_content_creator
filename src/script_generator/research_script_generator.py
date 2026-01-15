"""
Research-Based Script Generator

Creates YouTube/Reel scripts based on real web research,
with source citations and image-aligned scenes.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import asdict

from .web_researcher import WebResearcher, ResearchResult

try:
    from mlx_lm import load, generate
    HAS_MLX = True
except ImportError:
    HAS_MLX = False


class ResearchScriptGenerator:
    """Generate research-based scripts for YouTube videos and Reels."""

    def __init__(self, model_name: str = "mlx-community/Llama-3.2-3B-Instruct-4bit"):
        """Initialize the script generator."""
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.researcher = WebResearcher()

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

    def generate_script(
        self,
        topic: str,
        target_length: int = 60,
        style: str = "informational",
        include_sources: bool = True
    ) -> Dict:
        """
        Generate a research-based script.

        Args:
            topic: The topic to create content about
            target_length: Target video length in seconds
            style: Content style (informational, explainer, news, reaction)
            include_sources: Whether to include source citations

        Returns:
            Dict with script, sources, and metadata
        """
        # Step 1: Research the topic
        print(f"\n📚 Starting research-based script generation...")
        research = self.researcher.research_topic(topic)

        # Step 2: Generate script from research
        print(f"✍️  Generating script from research...")
        script = self._generate_from_research(research, target_length, style)

        # Step 3: Add source information
        if include_sources:
            script['sources'] = [asdict(s) for s in research.sources]
            script['research_summary'] = research.summary
            script['category'] = research.category

        # Step 4: Add image keywords for each scene
        script = self._enhance_visual_prompts(script, research)

        print(f"✅ Script generated: {len(script['scenes'])} scenes, {script['total_duration']}s")
        return script

    def _generate_from_research(
        self,
        research: ResearchResult,
        target_length: int,
        style: str
    ) -> Dict:
        """Generate script using LLM with research context."""

        # Prepare facts for prompt
        facts_text = "\n".join([f"- {fact}" for fact in research.key_facts[:10]])

        # Prepare timeline if available
        timeline_text = ""
        if research.timeline:
            timeline_text = "\nTimeline:\n" + "\n".join([
                f"- {e['date']}: {e['description'][:100]}"
                for e in research.timeline[:5]
            ])

        # Calculate scene count
        num_scenes = max(5, min(10, target_length // 6))

        prompt = f"""You are creating a script for a YouTube video/Reel about: "{research.topic}"

RESEARCHED FACTS (use these, don't make up information):
{facts_text}
{timeline_text}

Topic Category: {research.category}
Style: {style} YouTube video
Target Duration: {target_length} seconds
Number of Scenes: {num_scenes}

IMPORTANT RULES:
1. ONLY use facts from the research above - do NOT make up information
2. Start with a HOOK that creates curiosity (2-3 seconds)
3. Each scene must have a clear VISUAL DESCRIPTION for stock images
4. Keep narration punchy and engaging - this is for YouTube/TikTok, not a lecture
5. Each scene's visual_prompt should describe a real, searchable stock image
6. Include relevant numbers, dates, and names from the research
7. End with engagement (question, call-to-action, or cliffhanger)

Output ONLY valid JSON in this exact format:
{{
    "hook": {{
        "text": "Attention-grabbing opening line using a key fact",
        "duration": 3.0,
        "visual_prompt": "Description of opening image (specific, searchable)",
        "text_overlay": "Key words to display"
    }},
    "scenes": [
        {{
            "narration": "Factual narration from research (max 20 words)",
            "duration": 5.0,
            "visual_prompt": "Specific stock image description (person, place, or concept)",
            "text_overlay": "Key caption text",
            "fact_source": "Brief note on which fact this relates to"
        }}
    ]
}}

Generate the script now (JSON only, no other text):"""

        if HAS_MLX and self.model:
            try:
                response = generate(
                    self.model,
                    self.tokenizer,
                    prompt=prompt,
                    max_tokens=2000,
                )
                script = self._parse_response(response, target_length, research)
                return script
            except Exception as e:
                print(f"LLM generation failed: {e}")

        # Fallback: Generate script directly from research
        return self._generate_structured_script(research, target_length, style)

    def _parse_response(
        self,
        response: str,
        target_length: int,
        research: ResearchResult
    ) -> Dict:
        """Parse LLM response into structured script."""
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                script = json.loads(json_str)

                # Validate and fix structure
                if 'hook' not in script:
                    script['hook'] = self._create_hook(research)

                if 'scenes' not in script or len(script['scenes']) < 3:
                    script['scenes'] = self._create_scenes(research, target_length)

                # Calculate total duration
                total = float(script['hook'].get('duration', 3.0))
                for scene in script['scenes']:
                    scene['duration'] = float(scene.get('duration', 5.0))
                    total += scene['duration']

                script['hook']['duration'] = float(script['hook'].get('duration', 3.0))
                script['total_duration'] = total

                return script

        except Exception as e:
            print(f"Error parsing response: {e}")

        # Fallback to structured generation
        return self._generate_structured_script(research, target_length, "informational")

    def _generate_structured_script(
        self,
        research: ResearchResult,
        target_length: int,
        style: str
    ) -> Dict:
        """Generate script directly from research without LLM."""
        hook = self._create_hook(research)
        scenes = self._create_scenes(research, target_length)

        total_duration = hook['duration'] + sum(s['duration'] for s in scenes)

        return {
            "hook": hook,
            "scenes": scenes,
            "total_duration": total_duration,
            "topic": research.topic,
            "category": research.category
        }

    def _create_hook(self, research: ResearchResult) -> Dict:
        """Create an attention-grabbing hook."""
        # Use most impactful fact
        if research.key_facts:
            # Find fact with numbers or strong words
            best_fact = research.key_facts[0]
            for fact in research.key_facts[:5]:
                if any(x in fact for x in ['%', '$', 'million', 'billion', 'first', 'breaking']):
                    best_fact = fact
                    break

            # Create hook from fact
            hook_text = self._make_hook_engaging(best_fact, research.topic)
        else:
            hook_text = f"What's really happening with {research.topic}?"

        # Get visual keyword
        visual = research.image_keywords[0] if research.image_keywords else research.topic

        return {
            "text": hook_text,
            "duration": 3.0,
            "visual_prompt": f"Breaking news style, {visual}, dramatic lighting, news graphic",
            "text_overlay": hook_text[:30].upper()
        }

    def _make_hook_engaging(self, fact: str, topic: str) -> str:
        """Convert a fact into an engaging hook."""
        # Extract key elements
        if len(fact) > 100:
            fact = fact[:97] + "..."

        # Add engagement patterns
        hooks = [
            f"Breaking: {fact[:60]}",
            f"You won't believe this about {topic.split()[0]}...",
            f"This changes everything: {fact[:50]}",
            fact if len(fact) < 60 else fact[:57] + "..."
        ]

        # Return shortest engaging option
        return min(hooks, key=len)

    def _create_scenes(self, research: ResearchResult, target_length: int) -> List[Dict]:
        """Create scenes from research facts."""
        scenes = []
        num_scenes = max(5, min(10, target_length // 6))
        time_per_scene = (target_length - 3) / num_scenes  # -3 for hook

        # Use key facts for scenes
        facts_to_use = research.key_facts[:num_scenes - 1]  # Leave room for CTA

        for i, fact in enumerate(facts_to_use):
            # Clean up fact for narration
            narration = self._fact_to_narration(fact)

            # Generate visual prompt
            visual = self._fact_to_visual(fact, research)

            # Create text overlay
            overlay = self._create_overlay(fact)

            scene = {
                "narration": narration,
                "duration": float(time_per_scene),
                "visual_prompt": visual,
                "text_overlay": overlay,
                "fact_source": f"Research fact #{i+1}"
            }
            scenes.append(scene)

        # Add call-to-action scene
        cta_scene = {
            "narration": f"Follow for more updates on {research.topic.split()[0]}!",
            "duration": 3.0,
            "visual_prompt": "Social media engagement, follow button, notification bell, colorful",
            "text_overlay": "FOLLOW FOR MORE!",
            "fact_source": "Call to action"
        }
        scenes.append(cta_scene)

        return scenes

    def _fact_to_narration(self, fact: str) -> str:
        """Convert a fact to short narration."""
        # Remove source attributions
        fact = fact.split(' according to')[0]
        fact = fact.split(' reported')[0]
        fact = fact.split(' said ')[0]

        # Shorten if needed
        if len(fact) > 100:
            # Find natural break point
            for punct in ['.', ',', ';', '-']:
                if punct in fact[:80]:
                    idx = fact[:80].rfind(punct)
                    if idx > 40:
                        fact = fact[:idx]
                        break
            else:
                fact = fact[:97] + "..."

        return fact.strip()

    def _fact_to_visual(self, fact: str, research: ResearchResult) -> str:
        """Generate visual prompt from fact."""
        # Extract key entities
        import re

        # Find proper nouns
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', fact)

        # Category-based visual suggestions
        category_visuals = {
            'politics': 'government building, official setting, press conference',
            'economy': 'financial charts, money, business meeting',
            'military': 'military personnel, defense equipment, security',
            'human_rights': 'people gathering, protest, community',
            'international': 'world map, diplomatic meeting, flags',
            'technology': 'modern technology, digital interface, innovation'
        }

        base_visual = category_visuals.get(research.category, 'news broadcast, professional')

        # Combine with entities
        if proper_nouns:
            entity = proper_nouns[0]
            return f"{entity} related imagery, {base_visual}, high quality photo"
        else:
            # Use topic keywords
            if research.image_keywords:
                return f"{research.image_keywords[0]}, {base_visual}, professional photo"
            return f"{base_visual}, news style, high quality"

    def _create_overlay(self, fact: str) -> str:
        """Create text overlay from fact."""
        # Extract key numbers or phrases
        import re

        # Find percentages
        percentages = re.findall(r'\d+%', fact)
        if percentages:
            return percentages[0]

        # Find money amounts
        money = re.findall(r'\$[\d,]+(?:\s*(?:million|billion))?', fact, re.I)
        if money:
            return money[0]

        # Find years
        years = re.findall(r'\b20\d{2}\b', fact)
        if years:
            return years[0]

        # Use first few words
        words = fact.split()[:4]
        return ' '.join(words).upper()

    def _enhance_visual_prompts(self, script: Dict, research: ResearchResult) -> Dict:
        """Enhance visual prompts with searchable keywords."""
        # Add image search keywords to each scene
        image_keywords = research.image_keywords

        for i, scene in enumerate(script.get('scenes', [])):
            # Add specific searchable terms
            current_prompt = scene.get('visual_prompt', '')

            # Add relevant keywords from research
            if i < len(image_keywords):
                keyword = image_keywords[i % len(image_keywords)]
                if keyword.lower() not in current_prompt.lower():
                    scene['visual_prompt'] = f"{keyword}, {current_prompt}"

            # Add image search keywords
            scene['image_search_keywords'] = self._extract_search_terms(
                scene.get('visual_prompt', ''),
                research
            )

        # Do same for hook
        if 'hook' in script:
            script['hook']['image_search_keywords'] = self._extract_search_terms(
                script['hook'].get('visual_prompt', ''),
                research
            )

        return script

    def _extract_search_terms(self, visual_prompt: str, research: ResearchResult) -> List[str]:
        """Extract search-friendly terms from visual prompt."""
        terms = []

        # Add from visual prompt
        words = visual_prompt.replace(',', ' ').split()
        terms.extend([w for w in words if len(w) > 3 and w[0].isupper()])

        # Add from research keywords
        terms.extend(research.image_keywords[:3])

        # Add category-specific terms
        category_terms = {
            'politics': ['government', 'politics', 'official'],
            'economy': ['finance', 'business', 'economy'],
            'military': ['military', 'defense', 'security'],
            'international': ['diplomacy', 'international', 'world']
        }
        terms.extend(category_terms.get(research.category, ['news']))

        return list(set(terms))[:5]

    def save_script(self, script: Dict, output_path: Path):
        """Save script to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)

        print(f"Script saved to: {output_path}")

        # Also save sources separately
        if 'sources' in script:
            sources_path = output_path.parent / "sources.json"
            with open(sources_path, 'w', encoding='utf-8') as f:
                json.dump(script['sources'], f, indent=2, ensure_ascii=False)
            print(f"Sources saved to: {sources_path}")


if __name__ == "__main__":
    # Test the generator
    generator = ResearchScriptGenerator()

    script = generator.generate_script(
        topic="Trump Venezuela president",
        target_length=60,
        style="informational"
    )

    print("\n" + "="*60)
    print("GENERATED SCRIPT")
    print("="*60)
    print(f"Category: {script.get('category', 'N/A')}")
    print(f"Duration: {script.get('total_duration', 0)}s")
    print(f"\nHook: {script['hook']['text']}")
    print(f"\nScenes ({len(script['scenes'])}):")
    for i, scene in enumerate(script['scenes'], 1):
        print(f"\n  Scene {i}:")
        print(f"    Narration: {scene['narration'][:80]}...")
        print(f"    Visual: {scene['visual_prompt'][:60]}...")
        print(f"    Overlay: {scene['text_overlay']}")

    if 'sources' in script:
        print(f"\nSources ({len(script['sources'])}):")
        for s in script['sources'][:5]:
            print(f"  - {s['title'][:50]}... ({s['domain']})")
