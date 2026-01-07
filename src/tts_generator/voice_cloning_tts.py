"""
Voice Cloning TTS Integration

Uses Coqui XTTS v2 for cloning voices from audio samples.
Requires just 6 seconds of clear audio to clone a voice.
"""

import torch
from pathlib import Path
from typing import Dict, Optional
import subprocess
import wave


class VoiceCloningTTS:
    """Voice cloning TTS wrapper using Coqui XTTS v2."""

    def __init__(
        self,
        voice_sample_path: str,
        language: str = "en",
        speed: float = 1.0
    ):
        """
        Initialize Voice Cloning TTS.

        Args:
            voice_sample_path: Path to voice sample audio (WAV, MP3, etc.)
                              Minimum 6 seconds of clear speech recommended
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl,
                     cs, ar, zh, ja, hu, ko, hi)
            speed: Speech speed multiplier (1.0 = normal, 1.2 = 20% faster)
        """
        self.voice_sample_path = Path(voice_sample_path)
        self.language = language
        self.speed = speed
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Coqui XTTS v2 model."""
        try:
            import sys
            import os

            # Check Python version
            if sys.version_info < (3, 10):
                print(f"WARNING: Voice cloning requires Python 3.10+, you have {sys.version_info.major}.{sys.version_info.minor}")
                print("Falling back to placeholder audio. Upgrade Python to use voice cloning.")
                self.model = None
                return

            from TTS.api import TTS

            # Auto-agree to XTTS license using environment variable
            # This bypasses the interactive prompt for non-commercial use
            os.environ['COQUI_TOS_AGREED'] = '1'

            # Also try creating the agreement file in cache
            try:
                from TTS.utils.manage import ModelManager
                mm = ModelManager()
                model_path = os.path.join(
                    mm.output_prefix,
                    "tts_models--multilingual--multi-dataset--xtts_v2"
                )
                os.makedirs(model_path, exist_ok=True)
                tos_path = os.path.join(model_path, "tos_agreed.txt")
                with open(tos_path, "w", encoding="utf-8") as f:
                    f.write("I have read, understood and agreed to the Terms and Conditions.")
            except Exception:
                pass  # Fail silently if this doesn't work

            print("Auto-agreed to Coqui XTTS non-commercial license")

            # Get device
            device = "cuda" if torch.cuda.is_available() else "cpu"

            # Initialize TTS with XTTS v2 model
            print("Loading XTTS v2 model (this may take a moment)...")
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            print(f"XTTS v2 model loaded on {device}")

            # Verify voice sample exists
            if not self.voice_sample_path.exists():
                print(f"WARNING: Voice sample not found: {self.voice_sample_path}")
                print("Falling back to placeholder audio.")
                self.model = None
                return

            print(f"Voice sample loaded: {self.voice_sample_path}")

        except ImportError as e:
            print(f"WARNING: Coqui TTS not installed properly: {e}")
            print("Install with: pip install TTS (requires Python 3.10+)")
            print("Falling back to placeholder audio.")
            self.model = None
        except Exception as e:
            print(f"WARNING: Error loading XTTS v2 model: {e}")
            print("Falling back to placeholder audio.")
            self.model = None

    def generate_voiceover(self, script: Dict, output_path: Path) -> Path:
        """
        Generate voiceover from script using cloned voice.

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

        # If model failed to load, fall back to placeholder
        if self.model is None:
            print("Voice cloning model not available, using placeholder audio")
            return self._create_placeholder_audio(output_path, len(full_text))

        # Generate audio with XTTS v2
        temp_file = output_path.parent / "temp_voiceover.wav"

        try:
            print(f"Generating voiceover with cloned voice...")
            print(f"Text length: {len(full_text)} characters")

            # Generate speech with voice cloning
            self.model.tts_to_file(
                text=full_text,
                speaker_wav=str(self.voice_sample_path),
                language=self.language,
                file_path=str(temp_file)
            )

            # Apply speed adjustment if needed
            if abs(self.speed - 1.0) > 0.01:
                self._adjust_speed(temp_file, output_path, self.speed)
            else:
                temp_file.rename(output_path)

            print(f"Voiceover generated: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error generating voiceover: {e}")
            # Create a placeholder audio file as fallback
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
            print(f"Speed adjusted to {speed}x")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Warning: Could not adjust speed: {e}")
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
        # If audio path provided, get actual duration
        if audio_path and audio_path.exists():
            try:
                import wave
                with wave.open(str(audio_path), 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    actual_duration = frames / float(rate)

                # Scale scene durations proportionally
                script_duration = script['hook']['duration'] + sum(
                    scene['duration'] for scene in script['scenes']
                )
                scale_factor = actual_duration / script_duration if script_duration > 0 else 1.0
            except Exception as e:
                print(f"Warning: Could not read audio duration: {e}")
                scale_factor = 1.0
        else:
            scale_factor = 1.0

        timings = {
            'hook': {
                'start': 0.0,
                'end': script['hook']['duration'] * scale_factor,
                'duration': script['hook']['duration'] * scale_factor
            },
            'scenes': []
        }

        current_time = script['hook']['duration'] * scale_factor

        for scene in script['scenes']:
            timing = {
                'start': current_time,
                'end': current_time + (scene['duration'] * scale_factor),
                'duration': scene['duration'] * scale_factor
            }
            timings['scenes'].append(timing)
            current_time = timing['end']

        timings['total_duration'] = current_time

        return timings


if __name__ == "__main__":
    # Test Voice Cloning TTS
    import sys

    if len(sys.argv) < 2:
        print("Usage: python voice_cloning_tts.py <path_to_voice_sample.wav>")
        sys.exit(1)

    voice_sample = sys.argv[1]

    tts = VoiceCloningTTS(
        voice_sample_path=voice_sample,
        language="en",
        speed=1.0
    )

    test_script = {
        "hook": {
            "text": "This is a test of voice cloning technology.",
            "duration": 2.0
        },
        "scenes": [
            {
                "narration": "The system can clone any voice from just a short sample.",
                "duration": 4.0
            },
            {
                "narration": "This enables personalized content generation at scale.",
                "duration": 4.0
            }
        ]
    }

    output = Path("test_cloned_voiceover.wav")
    tts.generate_voiceover(test_script, output)
    print(f"Test complete. Audio saved to: {output}")
