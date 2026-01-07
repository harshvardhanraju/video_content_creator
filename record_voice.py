#!/usr/bin/env python3
"""
Simple Voice Recording Script

Records your voice for use with ReelForge voice cloning.
Minimum 6 seconds recommended, 10-15 seconds ideal.
"""

import sys
import wave
import time

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("ERROR: Required libraries not installed!")
    print("Install with: pip install sounddevice numpy scipy")
    sys.exit(1)


def record_voice(duration=15, sample_rate=44100, output_file="my_voice_sample.wav"):
    """
    Record voice from microphone.

    Args:
        duration: Recording duration in seconds (default: 15)
        sample_rate: Audio sample rate (default: 44100 Hz)
        output_file: Output filename (default: my_voice_sample.wav)
    """
    print("=" * 60)
    print("🎙️  ReelForge Voice Recording")
    print("=" * 60)
    print(f"\nRecording Duration: {duration} seconds")
    print(f"Sample Rate: {sample_rate} Hz")
    print(f"Output File: {output_file}")
    print("\n📝 Tips for best results:")
    print("  - Speak clearly and naturally")
    print("  - Keep consistent distance from microphone")
    print("  - Minimize background noise")
    print("  - Use varied sentences with natural intonation")
    print("  - Speak at your normal pace")

    input("\n✅ Press ENTER when ready to start recording...")

    print(f"\n🔴 Recording for {duration} seconds...")
    print("Start speaking NOW!\n")

    # Show countdown
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)

    print("   🎤 RECORDING!\n")

    # Record audio
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,  # Mono
        dtype=np.int16
    )

    # Wait for recording to complete with progress
    for i in range(duration):
        time.sleep(1)
        progress = int((i + 1) / duration * 40)
        bar = "█" * progress + "░" * (40 - progress)
        print(f"\r   [{bar}] {i + 1}/{duration}s", end="", flush=True)

    sd.wait()  # Wait until recording is finished

    print("\n\n✅ Recording complete!")

    # Save to WAV file
    print(f"💾 Saving to {output_file}...")

    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())

    print(f"✅ Voice sample saved to: {output_file}")
    print(f"📊 File size: {len(recording) * 2 / 1024:.1f} KB")

    # Play back recording
    playback = input("\n🔊 Play back recording? (y/n): ").strip().lower()
    if playback == 'y':
        print("🔊 Playing back...")
        sd.play(recording, sample_rate)
        sd.wait()
        print("✅ Playback complete!")

    print("\n" + "=" * 60)
    print("🎉 Voice recording complete!")
    print("=" * 60)
    print(f"\nTo use this voice sample with ReelForge:")
    print(f"  reelforge generate -i \"your text\" \\")
    print(f"    --voice-sample {output_file} \\")
    print(f"    --tts-language en \\")
    print(f"    -o my_reel.mp4")
    print("\n")


def main():
    """Main function with CLI options."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Record voice sample for ReelForge voice cloning"
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=15,
        help='Recording duration in seconds (default: 15)'
    )
    parser.add_argument(
        '-o', '--output',
        default='my_voice_sample.wav',
        help='Output filename (default: my_voice_sample.wav)'
    )
    parser.add_argument(
        '-r', '--sample-rate',
        type=int,
        default=44100,
        help='Audio sample rate in Hz (default: 44100)'
    )
    parser.add_argument(
        '-l', '--list-devices',
        action='store_true',
        help='List available audio devices and exit'
    )

    args = parser.parse_args()

    # List devices if requested
    if args.list_devices:
        print("Available audio input devices:")
        print(sd.query_devices())
        return

    # Record voice
    try:
        record_voice(
            duration=args.duration,
            sample_rate=args.sample_rate,
            output_file=args.output
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Recording cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error during recording: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
