#!/usr/bin/env python3
"""
Standalone Voice Cloning Script

Runs in a separate virtual environment with XTTS dependencies.
Called as a subprocess from the main application.
"""

import os
import sys
import argparse
from pathlib import Path


def clone_voice(text: str, voice_sample_path: str, output_path: str, language: str = "en"):
    """
    Clone voice using XTTS in isolated environment.

    Args:
        text: Text to synthesize
        voice_sample_path: Path to voice sample WAV file (6+ seconds)
        output_path: Path to save output WAV file
        language: Language code (default: en)
    """
    try:
        # Set environment variable to auto-accept TTS license
        os.environ['COQUI_TOS_AGREED'] = '1'

        # Import TTS (only works in this venv)
        from TTS.api import TTS

        print(f"Loading XTTS v2 model for language: {language}")

        # Initialize TTS with XTTS v2 model
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

        print(f"Cloning voice from: {voice_sample_path}")
        print(f"Generating speech: {text[:50]}...")

        # Generate speech with voice cloning
        tts.tts_to_file(
            text=text,
            speaker_wav=voice_sample_path,
            language=language,
            file_path=output_path
        )

        print(f"✓ Voice cloning successful: {output_path}")
        return 0

    except Exception as e:
        print(f"ERROR: Voice cloning failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(description="Voice cloning using XTTS")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--voice-sample", required=True, help="Path to voice sample WAV")
    parser.add_argument("--output", required=True, help="Output WAV path")
    parser.add_argument("--language", default="en", help="Language code (default: en)")

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.voice_sample).exists():
        print(f"ERROR: Voice sample not found: {args.voice_sample}", file=sys.stderr)
        return 1

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    # Clone voice
    return clone_voice(
        text=args.text,
        voice_sample_path=args.voice_sample,
        output_path=args.output,
        language=args.language
    )


if __name__ == "__main__":
    sys.exit(main())
