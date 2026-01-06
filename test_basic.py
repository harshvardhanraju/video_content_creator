#!/usr/bin/env python3
"""
Basic test of core components without heavy dependencies
"""

import sys
from pathlib import Path

# Test 1: Input Processor
print("=" * 60)
print("TEST 1: Input Processor")
print("=" * 60)

try:
    from src.input_processor.text_parser import TextParser

    parser = TextParser()

    # Test with simple text
    test_input = "AI is revolutionizing healthcare through better diagnosis and treatment."
    result = parser.parse(test_input, target_length=30)

    print("✅ TextParser working!")
    print(f"   Title: {result['title']}")
    print(f"   Key points: {len(result['key_points'])}")
    print(f"   Target length: {result['target_length']}s")

    # Test with markdown file
    md_file = Path("examples/sample_topic.md")
    if md_file.exists():
        result_md = parser.parse(md_file, target_length=45)
        print(f"✅ Markdown parsing working!")
        print(f"   Title: {result_md['title']}")
        print(f"   Key points: {len(result_md['key_points'])}")

except Exception as e:
    print(f"❌ Input Processor failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Script Generator (Mock Mode)
print("\n" + "=" * 60)
print("TEST 2: Script Generator (Mock Mode)")
print("=" * 60)

try:
    from src.script_generator.llm_generator import ScriptGenerator

    # This will use mock mode since MLX isn't installed
    script_gen = ScriptGenerator()

    test_input = {
        "title": "AI Transforming Healthcare",
        "key_points": [
            "AI diagnoses diseases faster",
            "Machine learning predicts outcomes",
            "Personalized treatment plans"
        ],
        "context": "AI is revolutionizing healthcare...",
        "target_length": 30
    }

    script = script_gen.generate_script(test_input)

    print("✅ Script Generator working (mock mode)!")
    print(f"   Hook text: {script['hook']['text'][:50]}...")
    print(f"   Number of scenes: {len(script['scenes'])}")
    print(f"   Total duration: {script['total_duration']:.1f}s")

    # Save script
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    script_path = output_dir / "test_script.json"
    script_gen.save_script(script, script_path)
    print(f"   Script saved: {script_path}")

except Exception as e:
    print(f"❌ Script Generator failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Caption Generator
print("\n" + "=" * 60)
print("TEST 3: Caption Generator")
print("=" * 60)

try:
    from src.video_assembler.caption_generator import CaptionGenerator

    caption_gen = CaptionGenerator()

    # Generate timings based on actual script
    test_timings = {
        "hook": {"start": 0.0, "end": script['hook']['duration']},
        "scenes": []
    }

    current_time = script['hook']['duration']
    for scene in script['scenes']:
        test_timings['scenes'].append({
            "start": current_time,
            "end": current_time + scene['duration']
        })
        current_time += scene['duration']

    captions = caption_gen.generate_captions_from_script(script, test_timings)

    print("✅ Caption Generator working!")
    print(f"   Generated {len(captions)} captions")
    for i, cap in enumerate(captions[:2]):
        print(f"   Caption {i+1}: {cap['text'][:30]}...")

    # Save SRT file
    srt_path = output_dir / "test_captions.srt"
    caption_gen.generate_srt_file(captions, srt_path)
    print(f"   SRT saved: {srt_path}")

except Exception as e:
    print(f"❌ Caption Generator failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL BASIC TESTS PASSED!")
print("=" * 60)
print("\nCore components are working correctly.")
print("Next steps:")
print("  1. Install FFmpeg: For video assembly")
print("  2. Install Piper TTS: For voiceovers")
print("  3. Install MLX & torch: For AI generation")
print("\nFor now, the pipeline will use fallback/mock generation.")
