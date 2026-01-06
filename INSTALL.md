# Installation Guide

## Prerequisites

### System Requirements
- **OS:** macOS (Apple Silicon: M1/M2/M3/M4)
- **RAM:** 16GB minimum
- **Storage:** 10GB free space for models
- **Python:** 3.10 or higher

### External Dependencies

#### 1. Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. FFmpeg
```bash
brew install ffmpeg
```

#### 3. Piper TTS
```bash
brew install piper
```

Or download from: https://github.com/rhasspy/piper/releases

---

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/harshvardhanraju/video_content_creator.git
cd video_content_creator
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Package (Development Mode)
```bash
pip install -e .
```

This makes the `reelforge` command available.

---

## Model Downloads

Models will be downloaded automatically on first use. However, you can pre-download them:

### LLM (Llama 3.2)
```bash
python -c "from mlx_lm import load; load('mlx-community/Llama-3.2-3B-Instruct-4bit')"
```

### Stable Diffusion 1.5
```bash
python -c "from diffusers import StableDiffusionPipeline; StableDiffusionPipeline.from_pretrained('runwayml/stable-diffusion-v1-5')"
```

### Piper TTS Voice
```bash
# Download a voice model (example)
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json
```

---

## Verify Installation

### Test FFmpeg
```bash
ffmpeg -version
```

### Test Piper
```bash
echo "Hello world" | piper --model en_US-lessac-medium --output_file test.wav
```

### Test ReelForge
```bash
reelforge --version
```

### Run Pipeline Test
```bash
reelforge test
```

---

## Troubleshooting

### Issue: `mlx` not installing
**Solution:** Ensure you're on Apple Silicon Mac (M1/M2/M3/M4). MLX only works on Apple Silicon.

```bash
# Check architecture
uname -m  # Should show "arm64"
```

### Issue: `piper` command not found
**Solution:** Install via Homebrew or download binary:

```bash
brew install piper
# OR
# Download from https://github.com/rhasspy/piper/releases
```

### Issue: FFmpeg not found
**Solution:**
```bash
brew install ffmpeg
```

### Issue: Out of memory
**Solution:** Close other applications. The pipeline runs components sequentially to minimize memory usage. If still failing, reduce image generation quality in `src/image_generator/sd_generator.py`:

```python
num_inference_steps=15  # Reduce from 25
```

### Issue: Slow image generation
**Solution:** This is normal for CPU/MPS. Each image takes 3-5 seconds on M4 Mac Air. Consider:
- Using fewer scenes (shorter reels)
- Reducing inference steps
- Using SDXL-Turbo (requires code modification)

---

## Optional: GPU Acceleration

While M4 Mac uses Metal Performance Shaders (MPS) automatically, you can verify GPU usage:

```bash
# Monitor GPU usage while generating
sudo powermetrics --samplers gpu_power -i 1000
```

---

## Uninstallation

```bash
# Remove virtual environment
rm -rf venv

# Uninstall package
pip uninstall reelforge

# Remove models (optional, ~8GB)
rm -rf ~/.cache/huggingface
```

---

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Check [docs/02_architecture.md](docs/02_architecture.md) for system design
3. Try the examples in `examples/` folder
4. Generate your first reel:

```bash
reelforge generate --input "Your topic here" --output my_first_reel.mp4
```

Happy reel making! 🎬
