#!/usr/bin/env python3
"""
NeuTTS Subprocess Runner

Standalone script for running NeuTTS voice cloning in an isolated environment.
Called by neutts_voice_cloning.py when direct import fails.

Run this with venv_neutts/bin/python for correct dependencies.
"""

import argparse
import json
import sys
from pathlib import Path

# Add neutts to path
NEUTTS_PATH = Path(__file__).parent.parent.parent / "external" / "neutts"
if NEUTTS_PATH.exists():
    sys.path.insert(0, str(NEUTTS_PATH))


def main():
    parser = argparse.ArgumentParser(description='NeuTTS Voice Synthesis')
    parser.add_argument('--segments', type=str, required=True, help='Path to JSON file with text segments')
    parser.add_argument('--output', type=str, required=True, help='Output audio path')
    parser.add_argument('--model', type=str, default='nano', help='Model size: nano, micro, air')
    parser.add_argument('--voice-sample', type=str, help='Path to voice sample for cloning')
    parser.add_argument('--voice-text', type=str, default='', help='Transcription of voice sample')
    parser.add_argument('--device', type=str, default='cpu', help='Device: cpu or mps')

    args = parser.parse_args()

    try:
        from neutts import NeuTTS
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        sys.exit(1)

    # Load segments
    with open(args.segments, 'r') as f:
        segments = json.load(f)

    # Model repos
    model_repos = {
        "nano": "neuphonic/neutts-nano",
        "micro": "neuphonic/neutts-micro",
        "air": "neuphonic/neutts-air"
    }

    backbone_repo = model_repos.get(args.model, "neuphonic/neutts-nano")

    print(f"Loading NeuTTS ({args.model})...")

    # Initialize TTS
    tts = NeuTTS(
        backbone_repo=backbone_repo,
        backbone_device=args.device,
        codec_repo="neuphonic/neucodec",
        codec_device=args.device
    )

    # Find voice sample - use provided or default
    voice_sample = args.voice_sample
    voice_text = args.voice_text

    # Default voice sample path
    default_sample = NEUTTS_PATH / "samples" / "jo.wav"
    default_text_file = NEUTTS_PATH / "samples" / "jo.txt"

    if not voice_sample or not Path(voice_sample).exists():
        if default_sample.exists():
            voice_sample = str(default_sample)
            if default_text_file.exists():
                voice_text = default_text_file.read_text().strip()
            print(f"Using default voice sample: jo.wav")
        else:
            print("Error: No voice sample available", file=sys.stderr)
            sys.exit(1)

    # Encode reference voice
    print(f"Encoding reference voice: {voice_sample}")
    ref_codes = tts.encode_reference(voice_sample)
    ref_text = voice_text

    # Generate audio for each segment
    all_audio = []

    for i, text in enumerate(segments):
        print(f"Generating {i+1}/{len(segments)}: {text[:50]}...")

        try:
            audio = tts.infer(text, ref_codes, ref_text)
            all_audio.append(audio)

            # Add pause between segments
            pause = np.zeros(int(24000 * 0.3))
            all_audio.append(pause)

        except Exception as e:
            print(f"Error on segment {i+1}: {e}", file=sys.stderr)
            silence = np.zeros(int(24000 * 2))
            all_audio.append(silence)

    # Combine and save
    combined = np.concatenate(all_audio)
    sf.write(args.output, combined, 24000)
    print(f"Saved: {args.output}")
    print(f"Duration: {len(combined)/24000:.1f} seconds")


if __name__ == '__main__':
    main()
