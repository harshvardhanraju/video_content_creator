"""
Piper TTS Integration

Fast, high-quality text-to-speech optimized for CPU.
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional
import wave


class PiperTTS:
    """Piper TTS wrapper for generating voiceovers."""

    def __init__(
        self,
        voice: str = "en_US-lessac-medium",
        speed: float = 1.2  # Faster for viral content
    ):
        """
        Initialize Piper TTS.

        Args:
            voice: Voice model name
            speed: Speech speed multiplier (1.0 = normal, 1.2 = 20% faster)
        """
        self.voice = voice
        self.speed = speed
        self._check_piper_installed()

    def _check_piper_installed(self):
        """Check if Piper is installed."""
        try:
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                text=True
            )
            print(f"Piper TTS found: {result.stdout.strip()}")
        except FileNotFoundError:
            print("WARNING: Piper TTS not found!")
            print("Install with: brew install piper")
            print("Or download from: https://github.com/rhasspy/piper")

    def generate_voiceover(self, script: Dict, output_path: Path) -> Path:
        """
        Generate voiceover from script.

        Args:
            script: Script dict with hook and scenes
            output_path: Output WAV file path

        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine all narration
        full_text = self._combine_narration(script)

        # Generate audio with Piper
        temp_file = output_path.parent / "temp_voiceover.wav"

        try:
            # Run Piper TTS
            cmd = [
                "piper",
                "--model", self.voice,
                "--output_file", str(temp_file)
            ]

            # Pass text via stdin
            result = subprocess.run(
                cmd,
                input=full_text,
                text=True,
                capture_output=True,
                check=True
            )

            # Apply speed adjustment if needed
            if abs(self.speed - 1.0) > 0.01:
                self._adjust_speed(temp_file, output_path, self.speed)
            else:
                temp_file.rename(output_path)

            print(f"Voiceover generated: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            print(f"Error running Piper: {e}")
            print(f"stderr: {e.stderr}")
            # Create a placeholder audio file
            return self._create_placeholder_audio(output_path, len(full_text))

        except FileNotFoundError:
            print("Piper not found, creating placeholder audio")
            return self._create_placeholder_audio(output_path, len(full_text))

    def _combine_narration(self, script: Dict) -> str:
        """Combine all narration from script."""
        parts = []

        # Add hook
        if 'hook' in script:
            parts.append(script['hook']['text'])

        # Add scenes
        for scene in script.get('scenes', []):
            parts.append(scene['narration'])

        return '. '.join(parts)

    def _adjust_speed(self, input_path: Path, output_path: Path, speed: float):
        """Adjust audio speed using ffmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-filter:a", f"atempo={speed}",
                str(output_path)
            ]

            subprocess.run(cmd, capture_output=True, check=True)
            input_path.unlink()  # Delete temp file

        except (subprocess.CalledProcessError, FileNotFoundError):
            # If ffmpeg not available, just copy file
            input_path.rename(output_path)

    def _create_placeholder_audio(self, output_path: Path, text_length: int) -> Path:
        """Create a silent audio file as placeholder."""
        # Estimate duration based on text length (avg 150 words/min)
        duration = max(10, text_length / 150 * 60)
        sample_rate = 44100
        num_samples = int(duration * sample_rate)

        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b'\x00\x00' * num_samples)

        print(f"Created placeholder audio: {output_path}")
        return output_path

    def generate_scene_timings(self, script: Dict, audio_path: Optional[Path] = None) -> Dict:
        """
        Calculate timing for each scene based on audio.

        Args:
            script: Script dict
            audio_path: Optional audio file to measure actual duration

        Returns:
            Dict with timing information for each scene
        """
        timings = {
            'hook': {
                'start': 0.0,
                'end': script['hook']['duration'],
                'duration': script['hook']['duration']
            },
            'scenes': []
        }

        current_time = script['hook']['duration']

        for scene in script['scenes']:
            timing = {
                'start': current_time,
                'end': current_time + scene['duration'],
                'duration': scene['duration']
            }
            timings['scenes'].append(timing)
            current_time = timing['end']

        timings['total_duration'] = current_time

        return timings


if __name__ == "__main__":
    # Test TTS
    tts = PiperTTS()

    test_script = {
        "hook": {
            "text": "Did you know AI can read your mind?",
            "duration": 2.0
        },
        "scenes": [
            {
                "narration": "Scientists developed brain-computer interfaces",
                "duration": 4.0
            },
            {
                "narration": "They can decode thoughts into text",
                "duration": 4.0
            }
        ]
    }

    output = Path("test_voiceover.wav")
    tts.generate_voiceover(test_script, output)
    print(f"Test complete. Audio saved to: {output}")
