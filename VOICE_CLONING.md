# Voice Cloning Feature

ReelForge now supports voice cloning using Coqui XTTS v2! You can create reels with your own voice or any voice sample you provide.

## Features

- Clone any voice from just a 6-second audio sample
- Supports 17 languages: English, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Hungarian, Korean, and Hindi
- High-quality voice synthesis
- Speed control (default: 1.2x faster for viral content)

## Quick Start

### 1. Prepare Your Voice Sample

Record or provide an audio sample with these requirements:
- **Duration**: Minimum 6 seconds (10-15 seconds recommended)
- **Quality**: Clear speech, minimal background noise
- **Format**: WAV, MP3, or any common audio format
- **Content**: Natural speaking, preferably varied sentences

Example voice samples are in the project root:
- `male_voice.wav`
- `test.wav`

### 2. Use Voice Cloning in CLI

Basic usage:
```bash
reelforge generate \
  -i "Your content here" \
  --voice-sample path/to/your_voice.wav \
  --tts-language en \
  -o my_reel.mp4
```

With more options:
```bash
reelforge generate \
  -i paper.md \
  -l 60 \
  --voice-sample my_voice.wav \
  --tts-language en \
  --save-intermediate \
  --verbose \
  -o custom_voice_reel.mp4
```

### 3. Supported Languages

Use the `--tts-language` flag with any of these codes:

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | `en` | Russian | `ru` |
| Spanish | `es` | Dutch | `nl` |
| French | `fr` | Czech | `cs` |
| German | `de` | Arabic | `ar` |
| Italian | `it` | Chinese | `zh` |
| Portuguese | `pt` | Japanese | `ja` |
| Polish | `pl` | Hungarian | `hu` |
| Turkish | `tr` | Korean | `ko` |
| Hindi | `hi` | | |

## Technical Details

### How It Works

1. **Voice Sample Loading**: XTTS v2 analyzes your voice sample to extract voice characteristics
2. **Text-to-Speech**: The model generates speech in the cloned voice using your script
3. **Speed Adjustment**: Audio is automatically adjusted to 1.2x speed for better engagement
4. **Integration**: The cloned voice seamlessly integrates with the existing pipeline

### Architecture

```
Voice Sample (6+ seconds)
    ↓
XTTS v2 Model Loading
    ↓
Voice Characteristics Extraction
    ↓
Script Text → Cloned TTS Generation
    ↓
Speed Adjustment (1.2x)
    ↓
Video Assembly with Cloned Voice
```

### Python API

You can also use voice cloning programmatically:

```python
from pathlib import Path
from src.tts_generator.voice_cloning_tts import VoiceCloningTTS

# Initialize TTS with voice sample
tts = VoiceCloningTTS(
    voice_sample_path="my_voice.wav",
    language="en",
    speed=1.2  # 20% faster
)

# Generate voiceover
script = {
    "hook": {
        "text": "This is my cloned voice!",
        "duration": 2.0
    },
    "scenes": [
        {
            "narration": "It sounds just like me.",
            "duration": 3.0
        }
    ]
}

output_path = Path("output_voiceover.wav")
tts.generate_voiceover(script, output_path)
```

## Performance Notes

### First Run
- XTTS v2 model download: ~2GB (one-time)
- Model loading: 10-30 seconds depending on hardware

### Subsequent Runs
- Model already cached
- Generation speed: ~1-2 seconds per second of audio
- Memory usage: ~4-6GB RAM

### Hardware Recommendations

| Hardware | Performance |
|----------|-------------|
| M4 Mac (16GB) | Excellent - runs on CPU efficiently |
| CUDA GPU | Fast - automatic GPU acceleration |
| CPU-only | Good - still usable, slightly slower |

## Tips for Best Results

1. **Voice Sample Quality**:
   - Use clear, high-quality audio
   - Avoid background noise, music, or echo
   - Natural speaking pace and intonation
   - Multiple sentences with varied pitch

2. **Language Matching**:
   - Ensure voice sample language matches `--tts-language`
   - Cross-language voice cloning works but may sound less natural

3. **Content Optimization**:
   - Shorter sentences work better
   - Avoid complex technical jargon in voice sample
   - Natural prosody improves output quality

## Fallback Behavior

If voice cloning fails (network issues, model errors, etc.):
- System automatically falls back to Piper TTS
- OR creates placeholder silent audio
- Error messages guide troubleshooting

## Comparison: Voice Cloning vs. Piper TTS

| Feature | Voice Cloning (XTTS v2) | Piper TTS |
|---------|------------------------|-----------|
| Customization | Your own voice | Pre-defined voices |
| Languages | 17 languages | Limited |
| Quality | High, natural | Good, synthetic |
| Speed | Slower (2-3s per audio sec) | Very fast |
| Model Size | ~2GB | ~20MB |
| Use Case | Personal branding, unique voice | Fast prototyping |

## Examples

### Example 1: Personal Brand Reel
```bash
reelforge generate \
  -i "My innovative ADAS research breakthrough" \
  --voice-sample my_professional_voice.wav \
  --tts-language en \
  -l 45 \
  -o branded_reel.mp4
```

### Example 2: Multilingual Content
```bash
# Record in English, generate in Hindi
reelforge generate \
  -i hindi_content.txt \
  --voice-sample english_voice.wav \
  --tts-language hi \
  -o hindi_reel.mp4
```

### Example 3: Fast Iteration
```bash
# Test with voice sample, save intermediate files
reelforge generate \
  -i "Test content" \
  --voice-sample test_voice.wav \
  --tts-language en \
  --save-intermediate \
  --verbose
```

## Troubleshooting

### Model Download Fails
```bash
# Manually download XTTS v2 model
python3 -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2')"
```

### Audio Quality Issues
- Check voice sample quality (sample rate, clarity)
- Try longer voice sample (15-20 seconds)
- Ensure language match between sample and target

### Memory Errors
- Close other applications
- Reduce concurrent processes
- Consider shorter content length

### Slow Generation
- First run always slower (model download)
- CPU generation slower than GPU
- Normal speed: 1-2 seconds per second of audio

## Future Enhancements

Planned improvements:
- Voice mixing (multiple speakers)
- Emotion control (happy, sad, excited)
- Speaking style transfer
- Real-time voice cloning
- Voice library management

## Credits

This feature uses [Coqui XTTS v2](https://github.com/coqui-ai/TTS), an open-source voice cloning model.

For questions or issues, see the main [README](README.md) or open an issue on GitHub.
