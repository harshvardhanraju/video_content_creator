# ReelForge 🎬

**Open-Source Viral Reel Generator for M4 Mac**

Generate engaging Instagram/YouTube Reels from text, topics, or research papers—100% locally, no cloud APIs required.

---

## Features

- **Input Flexibility:** Text prompts, topics, papers (PDF/MD), or markdown files
- **AI-Powered Script Generation:** Hook-driven, viral-optimized scripts
- **Voice Options:**
  - High-quality text-to-speech (Piper TTS)
  - Voice cloning from 6-second samples (Coqui XTTS v2)
  - 17+ language support
- **Dual Image Sources:**
  - **Stock Images** (Pexels API) - Professional quality, instant results 🌟 **Recommended**
  - **AI Generation** (Stable Diffusion) - Custom scenes, slower
- **Professional Assembly:** Automated captions, transitions, and effects
- **Content Safety:** Built-in safety checks for all generated content
- **Privacy-First:** Local processing (stock images require API key)
- **Optimized for Apple Silicon:** M4 Mac Air (16GB RAM)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Pexels API key (get free at https://www.pexels.com/api/)
export PEXELS_API_KEY=your_api_key_here

# Generate a reel with stock images (recommended)
python -m src.cli.main generate --input "How AI is revolutionizing healthcare"

# With voice cloning (use your own voice!)
python -m src.cli.main generate \
    --input "Good morning everyone" \
    --voice-sample my_voice.wav \
    --image-source stock

# From a file with AI-generated images
python -m src.cli.main generate \
    --input paper.md \
    --length 60 \
    --image-source ai
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Script Generation | Llama 3.2 (3B) via MLX | Create viral-optimized scripts |
| Text-to-Speech | Piper TTS + Coqui XTTS v2 | Natural voiceovers + voice cloning |
| Image Generation | Pexels API / Stable Diffusion 1.5 | Stock or AI-generated visuals |
| Video Assembly | FFmpeg + MoviePy | Final reel production |
| Content Safety | Custom filter system | Inappropriate content detection |

---

## Output Format

- **Resolution:** 1080x1920 (9:16 vertical)
- **Duration:** 30-60 seconds
- **Format:** MP4 (H.264)
- **Features:** Captions, transitions, voiceover

---

## Installation

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10 or higher
- 16GB RAM minimum
- ~10GB free disk space for models

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd content_generate

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download models (first run only)
python scripts/download_models.py
```

---

## Usage

### Basic Usage
```bash
# Simple text input
reelforge generate --input "The future of quantum computing"

# Specify duration
reelforge generate --input "AI ethics" --length 45

# Custom output path
reelforge generate --input topic.txt --output my_reel.mp4
```

### Advanced Options
```bash
# With voice cloning and stock images
reelforge generate \
    --input research_paper.md \
    --length 60 \
    --voice-sample my_voice.wav \
    --tts-language en \
    --image-source stock \
    --pexels-api-key YOUR_KEY \
    --save-intermediate \
    --verbose

# With AI-generated images (slower)
reelforge generate \
    --input topic.txt \
    --image-source ai \
    --no-captions \
    --verbose
```

---

## Project Structure

```
content_generate/
├── src/              # Source code
├── docs/             # Detailed documentation
├── examples/         # Sample inputs
├── outputs/          # Generated reels
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## Documentation

- **[Research Findings](docs/01_research_findings.md)** - Model selection and evaluation
- **[Architecture](docs/02_architecture.md)** - System design and component details
- **[Implementation Log](docs/03_implementation_log.md)** - Development progress

---

## Performance

| Task | Duration | Notes |
|------|----------|-------|
| Script Generation | 10-20 sec | LLM processing |
| Voiceover | 3-5 sec | TTS generation |
| Images (per scene) | 3-5 sec | 5-8 images typical |
| Video Assembly | 10-20 sec | Final composition |
| **Total Pipeline** | **60-90 sec** | For 30-60 sec reel |

---

## Roadmap

- [x] Core pipeline architecture
- [x] Documentation
- [ ] Input processor implementation
- [ ] Script generation with LLM
- [ ] TTS integration
- [ ] Image generation
- [ ] Video assembly
- [ ] CLI interface
- [ ] Web UI (future)
- [ ] Background music integration (future)
- [ ] Multi-language support (future)

---

## Contributing

This is an open-source project. Contributions welcome!

---

## License

MIT License - See LICENSE file for details

---

## System Requirements

- **OS:** macOS (Apple Silicon)
- **RAM:** 16GB minimum
- **Storage:** 10GB for models + workspace
- **Python:** 3.10+

---

**Built for M4 Mac Air. Optimized for speed and quality. Powered by open-source AI.**
