"""
Video Compositor

Assembles final reel from audio, images, and captions.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import json


class VideoCompositor:
    """Compose final video from all assets."""

    def __init__(
        self,
        resolution: tuple = (1080, 1920),  # 9:16 vertical
        fps: int = 30,
        add_zoom_effect: bool = True
    ):
        """
        Initialize video compositor.

        Args:
            resolution: Output resolution (width, height)
            fps: Frames per second
            add_zoom_effect: Apply Ken Burns zoom effect
        """
        self.resolution = resolution
        self.fps = fps
        self.add_zoom_effect = add_zoom_effect
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """Check if FFmpeg is installed."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            print(f"FFmpeg found: {result.stdout.split()[2]}")
        except FileNotFoundError:
            print("WARNING: FFmpeg not found!")
            print("Install with: brew install ffmpeg")

    def compose_video(
        self,
        script: Dict,
        audio_path: Path,
        image_paths: List[Path],
        output_path: Path,
        captions: Optional[List[Dict]] = None
    ) -> Path:
        """
        Compose final video from all assets.

        Args:
            script: Script dict with timing information
            audio_path: Path to voiceover audio
            image_paths: List of scene image paths (in order)
            output_path: Output video path
            captions: Optional caption data

        Returns:
            Path to generated video
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print("Composing video...")

        # Create video from images with timing
        temp_video = output_path.parent / "temp_video.mp4"
        self._create_video_from_images(script, image_paths, temp_video)

        # Add audio
        temp_with_audio = output_path.parent / "temp_with_audio.mp4"
        self._add_audio(temp_video, audio_path, temp_with_audio)

        # Add captions if provided
        if captions:
            self._add_captions(temp_with_audio, captions, output_path)
        else:
            temp_with_audio.rename(output_path)

        # Cleanup temp files
        if temp_video.exists():
            temp_video.unlink()
        if temp_with_audio.exists() and output_path.exists():
            temp_with_audio.unlink()

        print(f"Video complete: {output_path}")
        return output_path

    def _create_video_from_images(
        self,
        script: Dict,
        image_paths: List[Path],
        output_path: Path
    ):
        """Create video from images with timing."""
        # Create concat file for FFmpeg
        concat_file = output_path.parent / "concat_list.txt"

        with open(concat_file, 'w') as f:
            # Hook
            hook_duration = script['hook']['duration']
            f.write(f"file '{image_paths[0].absolute()}'\n")
            f.write(f"duration {hook_duration}\n")

            # Scenes
            for i, scene in enumerate(script['scenes'], 1):
                if i < len(image_paths):
                    f.write(f"file '{image_paths[i].absolute()}'\n")
                    f.write(f"duration {scene['duration']}\n")

            # Last image (repeat for final frame)
            f.write(f"file '{image_paths[-1].absolute()}'\n")

        # FFmpeg command to create video
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-vf", f"scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=decrease,"
                   f"pad={self.resolution[0]}:{self.resolution[1]}:(ow-iw)/2:(oh-ih)/2:black",
            "-r", str(self.fps),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "medium",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            concat_file.unlink()
        except subprocess.CalledProcessError as e:
            print(f"Error creating video: {e}")
            print(f"stderr: {e.stderr.decode()}")
            raise

    def _add_audio(self, video_path: Path, audio_path: Path, output_path: Path):
        """Add audio track to video."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error adding audio: {e}")
            print(f"stderr: {e.stderr.decode()}")
            # If audio fails, just copy video
            import shutil
            shutil.copy(video_path, output_path)

    def _add_captions(
        self,
        video_path: Path,
        captions: List[Dict],
        output_path: Path
    ):
        """Add captions to video using FFmpeg drawtext."""
        from .caption_generator import CaptionGenerator

        caption_gen = CaptionGenerator()
        filters = caption_gen.generate_ffmpeg_drawtext(captions)

        # Combine all filters
        filter_str = ','.join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", filter_str,
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "medium",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error adding captions: {e}")
            print(f"stderr: {e.stderr.decode()}")
            # If captions fail, just copy video
            import shutil
            shutil.copy(video_path, output_path)


if __name__ == "__main__":
    # Test compositor
    compositor = VideoCompositor()
    print("Video compositor initialized")
