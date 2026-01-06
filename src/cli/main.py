#!/usr/bin/env python3
"""
ReelForge CLI

Main command-line interface for generating viral reels.
"""

import click
from pathlib import Path
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.input_processor.text_parser import TextParser
from src.input_processor.pdf_parser import PDFParser
from src.script_generator.llm_generator import ScriptGenerator
from src.tts_generator.piper_tts import PiperTTS
from src.image_generator.sd_generator import ImageGenerator
from src.video_assembler.compositor import VideoCompositor
from src.video_assembler.caption_generator import CaptionGenerator
from src.content_safety.safety_checker import ContentSafetyChecker


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    ReelForge: Generate viral Instagram/YouTube Reels from text.

    A complete pipeline optimized for M4 Mac with 16GB RAM.
    """
    pass


@cli.command()
@click.option(
    '--input', '-i',
    required=True,
    help='Input text, file path, or topic'
)
@click.option(
    '--output', '-o',
    default='outputs/reel.mp4',
    help='Output video path (default: outputs/reel.mp4)'
)
@click.option(
    '--length', '-l',
    default=45,
    type=int,
    help='Target duration in seconds (default: 45)'
)
@click.option(
    '--voice',
    default='en_US-lessac-medium',
    help='TTS voice model (default: en_US-lessac-medium)'
)
@click.option(
    '--no-captions',
    is_flag=True,
    help='Disable caption overlay'
)
@click.option(
    '--save-intermediate',
    is_flag=True,
    help='Save intermediate files (script, audio, images)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed progress'
)
def generate(input, output, length, voice, no_captions, save_intermediate, verbose):
    """
    Generate a viral reel from input.

    Examples:

        \b
        # Simple text input
        reelforge generate -i "AI is transforming healthcare"

        \b
        # From a file
        reelforge generate -i paper.md -l 60 -o my_reel.mp4

        \b
        # With options
        reelforge generate -i topic.txt --no-captions --verbose
    """
    output_path = Path(output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up intermediate directories
    temp_dir = output_dir / ".temp"
    if save_intermediate:
        temp_dir = output_dir / "intermediate"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Parse Input
        click.echo("📝 Step 1/5: Processing input...")
        input_path = Path(input)

        if input_path.exists() and input_path.suffix == '.pdf':
            parser = PDFParser()
            parsed_data = parser.parse(input_path, length)
        else:
            parser = TextParser()
            parsed_data = parser.parse(input, length)

        if verbose:
            click.echo(f"   Title: {parsed_data['title']}")
            click.echo(f"   Key points: {len(parsed_data['key_points'])}")

        # Step 2: Generate Script
        click.echo("🤖 Step 2/5: Generating viral script...")
        script_gen = ScriptGenerator()
        script = script_gen.generate_script(parsed_data)

        script_path = temp_dir / "script.json"
        script_gen.save_script(script, script_path)

        if verbose:
            click.echo(f"   Scenes: {len(script['scenes']) + 1}")
            click.echo(f"   Duration: {script['total_duration']:.1f}s")

        # Step 2.5: Content Safety Check
        click.echo("🛡️  Checking content safety...")
        safety_checker = ContentSafetyChecker(strict_mode=True)
        is_safe, safety_report, safety_details = safety_checker.check_script(script)

        if not is_safe:
            click.echo(f"\n❌ Safety Check Failed!")
            click.echo(safety_checker.get_safety_report(script))
            click.echo("\nGeneration aborted due to safety concerns.")
            click.echo("Please modify your input to remove inappropriate content.")
            sys.exit(1)

        if verbose:
            click.echo(f"   {safety_report}")

        # Step 3: Generate Voiceover
        click.echo("🎙️  Step 3/5: Creating voiceover...")
        tts = PiperTTS(voice=voice, speed=1.2)
        audio_path = temp_dir / "voiceover.wav"
        tts.generate_voiceover(script, audio_path)

        # Get precise timings
        timings = tts.generate_scene_timings(script, audio_path)

        # Step 4: Generate Images
        click.echo("🎨 Step 4/5: Generating scene images...")
        image_gen = ImageGenerator()
        images_dir = temp_dir / "images"
        image_paths = image_gen.generate_images(script, images_dir)

        if verbose:
            click.echo(f"   Generated: {len(image_paths)} images")

        # Step 5: Compose Video
        click.echo("🎬 Step 5/5: Assembling final video...")

        # Generate captions
        captions = None
        if not no_captions:
            caption_gen = CaptionGenerator()
            captions = caption_gen.generate_captions_from_script(script, timings)

            if save_intermediate:
                srt_path = temp_dir / "captions.srt"
                caption_gen.generate_srt_file(captions, srt_path)

        # Compose final video
        compositor = VideoCompositor()
        final_video = compositor.compose_video(
            script=script,
            audio_path=audio_path,
            image_paths=image_paths,
            output_path=output_path,
            captions=captions
        )

        # Cleanup temp files if not saving
        if not save_intermediate:
            import shutil
            shutil.rmtree(temp_dir)

        click.echo(f"\n✅ Reel generated successfully!")
        click.echo(f"📹 Output: {final_video.absolute()}")
        click.echo(f"⏱️  Duration: {script['total_duration']:.1f} seconds")

        if save_intermediate:
            click.echo(f"📁 Intermediate files: {temp_dir.absolute()}")

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output script path (default: script.json)')
def script_only(input_file, output):
    """
    Generate only the script without creating video.

    Useful for previewing and editing the script before generation.
    """
    output_path = Path(output) if output else Path("script.json")

    try:
        click.echo("📝 Processing input...")
        parser = TextParser()
        parsed_data = parser.parse(input_file, 45)

        click.echo("🤖 Generating script...")
        script_gen = ScriptGenerator()
        script = script_gen.generate_script(parsed_data)

        script_gen.save_script(script, output_path)

        click.echo(f"\n✅ Script saved to: {output_path.absolute()}")
        click.echo(f"📊 Scenes: {len(script['scenes']) + 1}")
        click.echo(f"⏱️  Duration: {script['total_duration']:.1f}s")

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def test():
    """
    Test the pipeline with a sample input.
    """
    click.echo("🧪 Running pipeline test...")

    test_input = "AI is revolutionizing healthcare through faster diagnosis and personalized treatment."

    try:
        from .main import generate
        ctx = click.Context(generate)
        ctx.invoke(
            generate,
            input=test_input,
            output="outputs/test_reel.mp4",
            length=30,
            voice="en_US-lessac-medium",
            no_captions=False,
            save_intermediate=True,
            verbose=True
        )

        click.echo("\n✅ Test completed successfully!")

    except Exception as e:
        click.echo(f"\n❌ Test failed: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
