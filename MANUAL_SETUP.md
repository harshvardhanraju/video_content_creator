# Manual Setup Guide - System Dependencies

**Last Updated:** 2026-01-06

This guide covers installing the system dependencies needed for ReelForge: **Homebrew**, **FFmpeg**, and **Piper TTS**.

---

## Prerequisites

- M4 Mac Air running macOS
- Administrator access (for Homebrew installation)
- Internet connection

---

## Step 1: Install Homebrew (Package Manager)

Homebrew is needed to easily install FFmpeg and Piper TTS.

### Installation

1. **Open Terminal** (Applications → Utilities → Terminal)

2. **Run this command:**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Enter your password** when prompted

4. **Wait for installation** (~5-10 minutes)

5. **Follow post-install instructions** to add Homebrew to PATH:
   ```bash
   # For Apple Silicon Macs (M1/M2/M3/M4)
   echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
   eval "$(/opt/homebrew/bin/brew shellenv)"
   ```

6. **Verify installation:**
   ```bash
   brew --version
   # Should output: Homebrew 4.x.x
   ```

---

## Step 2: Install FFmpeg (Video Processing)

FFmpeg is required for video assembly, transitions, and caption overlay.

### Option A: Via Homebrew (Recommended)

```bash
brew install ffmpeg
```

Wait ~5 minutes for installation.

### Option B: Download Binary

If Homebrew doesn't work:

1. Visit: https://ffmpeg.org/download.html#build-mac
2. Download the macOS build
3. Extract and move to `/usr/local/bin/`
4. Make executable: `chmod +x /usr/local/bin/ffmpeg`

### Verify Installation

```bash
ffmpeg -version
# Should output: ffmpeg version 6.x.x or higher
```

---

## Step 3: Install Piper TTS (Text-to-Speech)

Piper TTS generates the voiceover audio for reels.

### Option A: Via Homebrew

```bash
brew install piper
```

**Note:** If Homebrew doesn't have Piper, use Option B.

### Option B: Download from GitHub (Alternative)

1. Visit: https://github.com/rhasspy/piper/releases

2. Download the macOS binary:
   - Look for: `piper_macos_arm64.tar.gz` (for M4 Mac)

3. Extract and install:
   ```bash
   cd ~/Downloads
   tar -xzf piper_macos_arm64.tar.gz
   sudo mv piper /usr/local/bin/
   sudo chmod +x /usr/local/bin/piper
   ```

4. Download a voice model:
   ```bash
   mkdir -p ~/.local/share/piper/voices
   cd ~/.local/share/piper/voices

   # Download English voice (example)
   curl -L -O https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx
   curl -L -O https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json
   ```

### Verify Installation

```bash
piper --version
# Should output: Piper version info

# Test voice generation
echo "Hello world" | piper --model en_US-lessac-medium --output_file test.wav
ls -lh test.wav
# Should create a test.wav file
```

---

## Step 4: Verify Complete Setup

Once all dependencies are installed, verify everything:

```bash
# Activate your virtual environment
cd /Users/harsha/dev/content_generate
source venv/bin/activate

# Check versions
python --version      # Should be 3.9+
ffmpeg -version       # Should show FFmpeg info
piper --version       # Should show Piper info
reelforge --version   # Should be 0.1.0

# Run component tests
python test_basic.py  # Should pass all tests
```

---

## Step 5: Test Full Pipeline

Once everything is installed, test the complete reel generation:

```bash
# Activate virtual environment
source venv/bin/activate

# Generate a complete reel
reelforge generate \
    --input "AI is transforming healthcare" \
    --output test_reel.mp4 \
    --length 30 \
    --verbose
```

This should:
1. ✅ Parse input
2. ✅ Generate script with LLM
3. ✅ Create voiceover with Piper
4. ✅ Generate images with Stable Diffusion
5. ✅ Assemble video with FFmpeg
6. ✅ Add captions
7. ✅ Output: `test_reel.mp4`

---

## Troubleshooting

### Issue: "brew: command not found"

**Solution:** Homebrew not in PATH. Add it:

```bash
# For M4 Mac (Apple Silicon)
export PATH="/opt/homebrew/bin:$PATH"

# Make it permanent
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zprofile
```

### Issue: "ffmpeg: command not found" after installation

**Solution:** Restart terminal or reload shell:

```bash
source ~/.zprofile
# OR
exec zsh
```

### Issue: "piper: command not found"

**Solution:** Check installation location:

```bash
which piper
ls /usr/local/bin/piper
ls /opt/homebrew/bin/piper

# If found, add to PATH
export PATH="/usr/local/bin:$PATH"
```

### Issue: Piper "No voice model found"

**Solution:** Download voice models:

```bash
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices

# Download voices from:
# https://github.com/rhasspy/piper/releases
```

### Issue: "Permission denied" during Homebrew install

**Solution:** Ensure you have admin rights:

```bash
# Check if you're an admin
groups | grep admin

# If not admin, ask system administrator
# OR use MacPorts instead
```

### Issue: Models downloading slowly

**Solution:** This is normal for first run. Models are ~6-8GB total:

- Llama 3.2 (3B): ~2-3 GB ✅ Already downloaded!
- Stable Diffusion 1.5: ~4 GB (downloads on first image generation)

They're cached, so subsequent runs are instant.

---

## Alternative: MacPorts

If Homebrew doesn't work, use MacPorts:

### Install MacPorts

1. Download from: https://www.macports.org/install.php
2. Install the package for your macOS version
3. Install FFmpeg:
   ```bash
   sudo port install ffmpeg
   ```

---

## Installation Complete Checklist

Once done, you should have:

- [x] Homebrew installed
- [x] FFmpeg installed and working
- [x] Piper TTS installed and working
- [x] Voice models downloaded
- [x] Python dependencies installed (already done)
- [x] Virtual environment active
- [x] Models cached (Llama 3.2 already downloaded)

---

## What's Next?

### Generate Your First Reel!

```bash
# Activate environment
source venv/bin/activate

# From text
reelforge generate --input "Your topic here" --output my_reel.mp4

# From file
reelforge generate --input examples/sample_topic.md --length 60

# With all options
reelforge generate \
    --input examples/sample_input.txt \
    --output healthcare_reel.mp4 \
    --length 45 \
    --save-intermediate \
    --verbose
```

### Test with Examples

```bash
# Healthcare topic
reelforge generate --input examples/sample_input.txt

# Electric vehicles topic
reelforge generate --input examples/sample_topic.md

# Custom topic
reelforge generate --input "The future of quantum computing" --length 60
```

---

## Installation Time Estimates

| Task | Duration |
|------|----------|
| Install Homebrew | 5-10 min |
| Install FFmpeg | 3-5 min |
| Install Piper TTS | 2-3 min |
| Download voice models | 1-2 min |
| **Total** | **~15-20 min** |

Plus one-time model downloads (already done for LLM!):
- Llama 3.2: ✅ Downloaded (~2-3 GB)
- Stable Diffusion: Downloads on first use (~4 GB)

---

## Need Help?

- **Issues:** https://github.com/harshvardhanraju/video_content_creator/issues
- **Documentation:** See `docs/` folder
- **FFmpeg docs:** https://ffmpeg.org/documentation.html
- **Piper docs:** https://github.com/rhasspy/piper

---

## Summary

After following this guide, you'll have:

✅ **Homebrew** - Package manager
✅ **FFmpeg** - Video processing
✅ **Piper TTS** - Voiceover generation
✅ **Voice models** - TTS voices
✅ **Complete pipeline** - Ready to generate reels!

**Total disk space needed:** ~500 MB for system tools

Combined with Python dependencies (~7-8 GB), total project size is ~8-9 GB.

---

*Last updated: 2026-01-06*
*For M4 Mac Air with macOS*
