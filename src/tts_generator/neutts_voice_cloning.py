"""
NeuTTS Voice Cloning Integration

Uses Neuphonic's NeuTTS for instant voice cloning with only 3-15 seconds of audio.
Optimized for on-device deployment on Apple Silicon Macs.

Repository: https://github.com/neuphonic/neutts
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Check for soundfile (needed for both direct and subprocess modes)
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

# NeuTTS requires transformers 4.x which conflicts with main venv
# Always use subprocess mode for isolation
HAS_NEUTTS = False  # Force subprocess mode

# Default voice sample bundled with NeuTTS
DEFAULT_VOICE_SAMPLE = Path(__file__).parent.parent.parent / "external" / "neutts" / "samples" / "jo.wav"
DEFAULT_VOICE_TEXT = "So I just tried Neuphonic and I'm genuinely impressed. It's super responsive, it sounds clean, supports voice cloning, and the agent feature is fun to play with too."


class NeuTTSVoiceCloning:
    """
    Voice cloning TTS using NeuTTS (Neuphonic).

    Features:
    - Instant voice cloning with 3-15 seconds of audio
    - On-device inference (CPU/MPS)
    - 24kHz audio output
    - Optimized for Apple Silicon
    """

    def __init__(
        self,
        voice_sample_path: Optional[str] = None,
        voice_sample_text: Optional[str] = None,
        model_size: str = "nano",  # "nano", "micro", "air"
        device: str = "cpu",  # "cpu" or "mps" (via llama-cpp)
        speed: float = 1.0
    ):
        """
        Initialize NeuTTS voice cloning.

        Args:
            voice_sample_path: Path to voice sample WAV (3-15 seconds)
            voice_sample_text: Transcription of the voice sample (improves quality)
            model_size: "nano" (fastest), "micro", or "air" (best quality)
            device: "cpu" or "mps" for Apple Silicon
            speed: Speech speed multiplier (0.5-2.0)
        """
        # Use provided voice sample or fall back to bundled default
        if voice_sample_path and Path(voice_sample_path).exists():
            self.voice_sample_path = voice_sample_path
            self.voice_sample_text = voice_sample_text or ""
        else:
            # Use bundled default voice
            self.voice_sample_path = str(DEFAULT_VOICE_SAMPLE) if DEFAULT_VOICE_SAMPLE.exists() else None
            self.voice_sample_text = DEFAULT_VOICE_TEXT
            if self.voice_sample_path:
                print(f"Using default NeuTTS voice sample: jo.wav")

        self.model_size = model_size
        self.device = device
        self.speed = speed

        self.tts = None
        self.ref_codes = None

        # Always use subprocess mode due to transformers version conflict
        print(f"NeuTTS initialized (subprocess mode, model: {model_size})")

    def _load_model(self):
        """Load the NeuTTS model and encode reference voice."""
        print(f"Loading NeuTTS model ({self.model_size})...")

        try:
            # Select model based on size
            model_repos = {
                "nano": "neuphonic/neutts-nano",
                "micro": "neuphonic/neutts-micro",
                "air": "neuphonic/neutts-air"
            }

            backbone_repo = model_repos.get(self.model_size, "neuphonic/neutts-nano")

            self.tts = NeuTTS(
                backbone_repo=backbone_repo,
                backbone_device=self.device,
                codec_repo="neuphonic/neucodec",
                codec_device=self.device
            )

            print(f"NeuTTS loaded on {self.device}")

            # Encode reference voice if provided
            if self.voice_sample_path and Path(self.voice_sample_path).exists():
                self._encode_reference_voice()

        except Exception as e:
            print(f"Error loading NeuTTS: {e}")
            print("Falling back to subprocess mode...")
            self.tts = None

    def _encode_reference_voice(self):
        """Encode the reference voice sample for cloning."""
        print(f"Encoding reference voice from: {self.voice_sample_path}")

        try:
            self.ref_codes = self.tts.encode_reference(self.voice_sample_path)
            print("Reference voice encoded successfully")

            # Get reference text if not provided
            if not self.voice_sample_text:
                # Use a generic placeholder - user should provide actual text
                self.voice_sample_text = ""
                print("Note: Provide voice_sample_text for better quality")

        except Exception as e:
            print(f"Error encoding reference voice: {e}")
            self.ref_codes = None

    def set_voice_sample(self, sample_path: str, sample_text: Optional[str] = None):
        """
        Set or update the voice sample for cloning.

        Args:
            sample_path: Path to voice sample WAV
            sample_text: Optional transcription of the sample
        """
        self.voice_sample_path = sample_path
        self.voice_sample_text = sample_text or ""

        if self.tts:
            self._encode_reference_voice()

    def generate_voiceover(
        self,
        script: Dict,
        output_path: Path,
        combine: bool = True
    ) -> Path:
        """
        Generate voiceover for the entire script.

        Args:
            script: Script dict with hook and scenes
            output_path: Path for output audio file
            combine: Whether to combine all audio into one file

        Returns:
            Path to the generated audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Collect all text segments
        segments = []

        # Hook
        hook_text = script.get('hook', {}).get('text', '')
        if hook_text:
            segments.append(hook_text)

        # Scenes
        for scene in script.get('scenes', []):
            narration = scene.get('narration', '')
            if narration:
                segments.append(narration)

        # Generate audio
        if not segments:
            print("No text to synthesize")
            return output_path

        # Always use subprocess mode due to dependency conflicts
        return self._generate_with_subprocess(segments, output_path)

    def _generate_cloned(self, segments: List[str], output_path: Path) -> Path:
        """Generate voice-cloned audio."""
        import numpy as np

        all_audio = []

        for i, text in enumerate(segments):
            print(f"Generating segment {i+1}/{len(segments)}: {text[:50]}...")

            try:
                # Generate with cloned voice
                audio = self.tts.infer(
                    text,
                    self.ref_codes,
                    self.voice_sample_text
                )

                # Apply speed adjustment
                if self.speed != 1.0:
                    audio = self._adjust_speed(audio, self.speed)

                all_audio.append(audio)

                # Add small pause between segments
                pause = np.zeros(int(24000 * 0.3))  # 300ms pause
                all_audio.append(pause)

            except Exception as e:
                print(f"Error generating segment {i+1}: {e}")
                # Add silence for failed segment
                silence = np.zeros(int(24000 * 2))  # 2 second silence
                all_audio.append(silence)

        # Combine all audio
        combined = np.concatenate(all_audio)

        # Save
        sf.write(str(output_path), combined, 24000)
        print(f"Voice-cloned audio saved: {output_path}")

        return output_path

    def _generate_default(self, segments: List[str], output_path: Path) -> Path:
        """Generate audio with default voice (no cloning)."""
        import numpy as np

        all_audio = []

        for i, text in enumerate(segments):
            print(f"Generating segment {i+1}/{len(segments)}...")

            try:
                # Generate without reference (uses default voice)
                audio = self.tts.infer_default(text)
                all_audio.append(audio)

                # Add pause
                pause = np.zeros(int(24000 * 0.3))
                all_audio.append(pause)

            except Exception as e:
                print(f"Error: {e}")
                silence = np.zeros(int(24000 * 2))
                all_audio.append(silence)

        combined = np.concatenate(all_audio)
        sf.write(str(output_path), combined, 24000)
        print(f"Audio saved: {output_path}")

        return output_path

    def _generate_with_subprocess(
        self,
        segments: List[str],
        output_path: Path
    ) -> Path:
        """Fallback: Generate using subprocess call with isolated venv."""
        import subprocess
        import numpy as np

        # Write segments to temp file
        temp_dir = tempfile.mkdtemp()
        segments_file = Path(temp_dir) / "segments.json"
        with open(segments_file, 'w') as f:
            json.dump(segments, f)

        # Path to subprocess script and venv
        script_path = Path(__file__).parent / "neutts_subprocess.py"
        project_root = Path(__file__).parent.parent.parent
        venv_python = project_root / "venv_neutts" / "bin" / "python"

        # Use venv_neutts python if available, otherwise fall back to system python
        python_cmd = str(venv_python) if venv_python.exists() else "python"

        # Run subprocess
        cmd = [
            python_cmd, str(script_path),
            "--segments", str(segments_file),
            "--output", str(output_path),
            "--model", self.model_size
        ]

        if self.voice_sample_path:
            cmd.extend(["--voice-sample", self.voice_sample_path])
        if self.voice_sample_text:
            cmd.extend(["--voice-text", self.voice_sample_text])

        print(f"Running NeuTTS subprocess: {' '.join(cmd[:3])}...")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                print(f"Subprocess error: {result.stderr}")
                # Create silence file
                try:
                    silence = np.zeros(int(24000 * 10))
                    sf.write(str(output_path), silence, 24000)
                except:
                    pass
            else:
                print(f"NeuTTS subprocess completed successfully")
                if result.stdout:
                    for line in result.stdout.strip().split('\n')[-5:]:
                        print(f"  {line}")
        except subprocess.TimeoutExpired:
            print("NeuTTS subprocess timed out")
        except Exception as e:
            print(f"Subprocess failed: {e}")

        return output_path

    def _adjust_speed(self, audio, speed: float):
        """Adjust audio speed using resampling."""
        import numpy as np
        from scipy import signal

        if speed == 1.0:
            return audio

        # Simple time stretching via resampling
        num_samples = int(len(audio) / speed)
        resampled = signal.resample(audio, num_samples)

        return resampled.astype(np.float32)

    def generate_scene_timings(
        self,
        script: Dict,
        audio_path: Path
    ) -> List[Tuple[float, float]]:
        """
        Generate timing information for each scene.

        Args:
            script: Script dict
            audio_path: Path to generated audio

        Returns:
            List of (start_time, end_time) tuples for each scene
        """
        timings = []

        # Get audio duration
        try:
            info = sf.info(str(audio_path))
            total_duration = info.duration
        except:
            total_duration = script.get('total_duration', 30)

        # Calculate timings based on text length
        segments = []

        # Hook
        hook_text = script.get('hook', {}).get('text', '')
        if hook_text:
            segments.append(len(hook_text))

        # Scenes
        for scene in script.get('scenes', []):
            narration = scene.get('narration', '')
            segments.append(len(narration) if narration else 100)

        # Total characters
        total_chars = sum(segments)
        if total_chars == 0:
            total_chars = 1

        # Distribute duration proportionally
        current_time = 0.0
        for char_count in segments:
            segment_duration = (char_count / total_chars) * total_duration
            timings.append((current_time, current_time + segment_duration))
            current_time += segment_duration

        return timings

    def synthesize_text(self, text: str, output_path: Path) -> Path:
        """
        Synthesize a single text string.

        Args:
            text: Text to synthesize
            output_path: Output path for audio

        Returns:
            Path to generated audio
        """
        if not HAS_NEUTTS or self.tts is None or self.ref_codes is None:
            print("NeuTTS not properly initialized")
            return output_path

        try:
            audio = self.tts.infer(text, self.ref_codes, self.voice_sample_text)

            if self.speed != 1.0:
                audio = self._adjust_speed(audio, self.speed)

            sf.write(str(output_path), audio, 24000)
            return output_path

        except Exception as e:
            print(f"Error synthesizing: {e}")
            return output_path


def check_neutts_installation():
    """Check if NeuTTS and dependencies are installed."""
    issues = []

    if not HAS_NEUTTS:
        issues.append("neutts package not installed")

    # Check espeak-ng
    import shutil
    if not shutil.which('espeak-ng'):
        issues.append("espeak-ng not found (brew install espeak-ng)")

    # Check soundfile
    try:
        import soundfile
    except ImportError:
        issues.append("soundfile not installed (pip install soundfile)")

    if issues:
        print("NeuTTS requirements missing:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("NeuTTS requirements satisfied")
    return True


if __name__ == "__main__":
    # Test the NeuTTS voice cloning
    print("Testing NeuTTS Voice Cloning...\n")

    # Check installation
    if not check_neutts_installation():
        print("\nPlease install missing dependencies and try again.")
        exit(1)

    # Create test instance
    tts = NeuTTSVoiceCloning(
        model_size="nano",  # Use smallest model for testing
        device="cpu"
    )

    # Test script
    test_script = {
        "hook": {
            "text": "Breaking news from Washington today."
        },
        "scenes": [
            {"narration": "The President made a major announcement."},
            {"narration": "Reactions continue to pour in from around the world."}
        ],
        "total_duration": 15
    }

    output_dir = Path("test_neutts")
    output_dir.mkdir(exist_ok=True)

    audio_path = output_dir / "test_voiceover.wav"
    tts.generate_voiceover(test_script, audio_path)

    print(f"\nTest audio saved to: {audio_path}")
