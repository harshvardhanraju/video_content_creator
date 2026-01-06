# System Architecture: ReelForge

**Last Updated:** 2026-01-06
**Status:** Design Complete ✓

## Project Overview

**ReelForge** is a 100% local, open-source pipeline for generating engaging Instagram/YouTube Reels from text inputs, research papers, or markdown files.

**Design Philosophy:**
- Viral-first: Hook-driven, fast-paced, attention-grabbing
- Privacy-focused: All processing on-device
- Optimized for: M4 Mac Air (16GB RAM)
- Output format: 9:16 vertical video (1080x1920)

---

## High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT PROCESSOR                         │
│  Accepts: Text/Topic/Paper/MD → Extracts key points         │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   SCRIPT GENERATOR (LLM)                     │
│  - Creates hook (first 2 sec)                                │
│  - Breaks content into 5-8 punchy scenes                     │
│  - Generates image prompts for each scene                    │
│  - Optimizes for 30-60 second duration                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              PARALLEL GENERATION PIPELINE                    │
│                                                              │
│  ┌─────────────────┐        ┌──────────────────┐           │
│  │  TTS Generator  │        │ Image Generator  │           │
│  │  (Piper TTS)    │        │ (SD 1.5 Core ML) │           │
│  │  → audio.wav    │        │ → scene_1.png    │           │
│  └─────────────────┘        │   scene_2.png    │           │
│                             │   ...            │           │
│                             └──────────────────┘           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   VIDEO ASSEMBLER                            │
│  - Syncs images with audio timing                           │
│  - Adds zoom/pan effects (Ken Burns)                        │
│  - Generates captions from script                           │
│  - Overlays captions with viral styling                     │
│  - Applies transitions                                       │
│  - Exports as 9:16 MP4                                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
                  output.mp4
```

---

## Component Details

### 1. Input Processor (`src/input_processor/`)

**Responsibility:** Normalize various input formats into structured data

**Supported Inputs:**
- Plain text prompt
- Topic/keyword (auto-expanded)
- Research paper (PDF/MD)
- Markdown file

**Output Format:**
```python
{
    "title": str,
    "key_points": List[str],
    "context": str,
    "target_length": int  # seconds
}
```

---

### 2. Script Generator (`src/script_generator/`)

**Responsibility:** Transform input into viral-optimized video script

**Model:** Llama 3.2 (3B) via MLX

**Script Structure:**
```python
{
    "hook": {
        "text": str,           # First 1-2 seconds
        "duration": float      # seconds
    },
    "scenes": [
        {
            "narration": str,
            "duration": float,
            "visual_prompt": str,  # For image generation
            "text_overlay": str    # Caption text
        }
    ],
    "total_duration": float
}
```

**Viral Optimization:**
- Start with attention-grabbing hook
- Use pattern interrupt every 3-5 seconds
- Keep sentences punchy (<10 words)
- End with CTA or cliffhanger

**Prompt Template:**
```
Create a viral Instagram reel script for: [TOPIC]

Requirements:
- Duration: 30-60 seconds
- Start with a strong hook (1-2 sec)
- 5-8 fast-paced scenes
- Each scene needs narration + visual description
- Style: Engaging, conversational, punchy
- Format as JSON
```

---

### 3. TTS Generator (`src/tts_generator/`)

**Responsibility:** Convert narration to natural-sounding voiceover

**Model:** Piper TTS

**Features:**
- Multiple voice options
- Speed control (1.1-1.3x for viral content)
- Output: WAV file (44.1kHz, 16-bit)

**API:**
```python
def generate_voiceover(script: Script) -> AudioFile:
    # Concatenate all narration
    # Generate with piper
    # Apply speed adjustment
    # Return audio file path
```

---

### 4. Image Generator (`src/image_generator/`)

**Responsibility:** Create eye-catching visuals for each scene

**Model:** Stable Diffusion 1.5 (Core ML optimized)

**Configuration:**
- Resolution: 1080x1920 (9:16)
- Steps: 20-25 (quality vs speed)
- Guidance scale: 7.5
- Style: Vibrant, high-contrast, social-media-ready

**Prompt Enhancement:**
```python
def enhance_prompt(visual_prompt: str) -> str:
    return f"{visual_prompt}, vibrant colors, high contrast, " \
           f"professional photography, trending on instagram, " \
           f"vertical composition, 9:16 aspect ratio"
```

**Output:** PNG files (scene_001.png, scene_002.png, ...)

---

### 5. Video Assembler (`src/video_assembler/`)

**Responsibility:** Combine all assets into final reel

**Tech Stack:**
- FFmpeg (core video processing)
- MoviePy (Python orchestration)

**Assembly Steps:**
1. **Timeline Calculation**
   - Parse script timing
   - Align images with narration
   - Calculate transition points

2. **Visual Effects**
   - Ken Burns effect (zoom/pan)
   - Crossfade transitions (0.3s)
   - Color grading (optional)

3. **Caption Generation**
   - Extract key phrases
   - Style with viral fonts (Impact, Montserrat Bold)
   - Position: Center or bottom third
   - Styling: White text, black outline, yellow highlights

4. **Audio Mixing**
   - Voiceover (primary)
   - Background music (optional, -20dB)
   - Fade in/out

5. **Export**
   - Codec: H.264
   - Resolution: 1080x1920
   - Frame rate: 30fps
   - Bitrate: 8-10 Mbps

**Caption Styling (FFmpeg drawtext):**
```bash
drawtext=fontfile=/path/to/font.ttf:
         text='CAPTION TEXT':
         fontsize=60:
         fontcolor=white:
         borderw=3:
         bordercolor=black:
         x=(w-text_w)/2:
         y=h-200
```

---

### 6. CLI Interface (`src/cli/`)

**Responsibility:** User-facing command-line tool

**Usage:**
```bash
# Basic usage
reelforge generate --input "AI is transforming healthcare"

# From file
reelforge generate --input paper.md --length 45

# Advanced options
reelforge generate \
    --input topic.txt \
    --length 60 \
    --voice female \
    --style vibrant \
    --output my_reel.mp4
```

**Options:**
- `--input`: Input file or text
- `--length`: Target duration (default: 45s)
- `--voice`: Voice selection (default: en_US-female)
- `--style`: Visual style preset
- `--output`: Output file path
- `--no-captions`: Disable captions
- `--verbose`: Show detailed progress

---

## Data Flow

```
Input Text
    ↓
[Normalize & Extract] → structured_input.json
    ↓
[LLM Script Gen] → script.json
    ↓
    ├─→ [TTS] → voiceover.wav
    └─→ [Image Gen] → scene_001.png, scene_002.png, ...
    ↓
[Video Assembly]
    ├─ Load script.json
    ├─ Load voiceover.wav
    ├─ Load all scene images
    ├─ Generate captions
    ├─ Apply effects & transitions
    └─ Export → final_reel.mp4
```

---

## Directory Structure

```
content_generate/
├── src/
│   ├── input_processor/
│   │   ├── __init__.py
│   │   ├── text_parser.py
│   │   └── pdf_parser.py
│   ├── script_generator/
│   │   ├── __init__.py
│   │   └── llm_generator.py
│   ├── tts_generator/
│   │   ├── __init__.py
│   │   └── piper_tts.py
│   ├── image_generator/
│   │   ├── __init__.py
│   │   └── sd_generator.py
│   ├── video_assembler/
│   │   ├── __init__.py
│   │   ├── compositor.py
│   │   └── caption_generator.py
│   └── cli/
│       ├── __init__.py
│       └── main.py
├── docs/
│   ├── 01_research_findings.md
│   ├── 02_architecture.md
│   └── 03_implementation_log.md
├── examples/
│   ├── sample_input.txt
│   └── sample_paper.md
├── outputs/
│   └── .gitkeep
├── requirements.txt
├── setup.py
├── README.md
└── .gitignore
```

---

## Performance Considerations

### Memory Management
- **Sequential Processing:** LLM → TTS + Images → Video Assembly
- **Avoid:** Running LLM and SD simultaneously (exceeds 16GB)
- **Cleanup:** Delete intermediate files after assembly

### Optimization Opportunities
1. **Batch Image Generation:** Generate 2-3 images in parallel
2. **Model Caching:** Keep models loaded between runs
3. **Quantization:** Use Q4 quantized models for LLM
4. **Resolution Scaling:** Generate at 720p, upscale to 1080p

---

## Future Enhancements (Roadmap)

- [ ] Web UI (Gradio/Streamlit)
- [ ] B-roll video clips integration
- [ ] Background music library
- [ ] Multi-language support
- [ ] Custom voice cloning
- [ ] Batch processing
- [ ] YouTube/Instagram direct upload
- [ ] Analytics integration

---

## Design Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Python as primary language | Best AI/ML ecosystem | 2026-01-06 |
| 100% local processing | Privacy, no API costs | 2026-01-06 |
| Llama 3.2 3B over larger models | Memory constraints | 2026-01-06 |
| SD 1.5 over SDXL | Faster, lower RAM | 2026-01-06 |
| Sequential pipeline | Avoid memory overflow | 2026-01-06 |
| FFmpeg for video | Industry standard | 2026-01-06 |
