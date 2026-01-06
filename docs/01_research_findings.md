# Research Findings: Open-Source Models for M4 Mac Air (16GB RAM)

**Last Updated:** 2026-01-06
**Status:** Research Complete ✓

## Hardware Constraints
- **Device:** M4 Apple Mac Air
- **RAM:** 16GB
- **Requirement:** 100% local processing, no cloud APIs
- **Target:** Viral/engaging short-form video content (Instagram/YouTube Reels)

---

## Selected Models & Tools

### 1. Script Generation (LLM)
**Selected: Llama 3.2 (3B) via MLX**

**Options Evaluated:**
- **Llama 3.2 (3B)** ✓ SELECTED
  - Quantized Q4/Q5 models
  - Optimized for Apple Silicon via `mlx-lm`
  - RAM usage: ~4-6GB
  - Good quality for script generation

- **Phi-3-mini (3.8B)**
  - Microsoft's efficient model
  - RAM usage: ~5-7GB
  - Alternative if Llama underperforms

- **Qwen2.5 (3B)**
  - Good multilingual support
  - RAM usage: ~4-6GB
  - Backup option

**Rationale:** Llama 3.2 3B offers best balance of quality and performance for M4 Mac. MLX framework provides native Apple Silicon optimization.

---

### 2. Text-to-Speech (TTS)
**Selected: Piper TTS**

**Options Evaluated:**
- **Piper TTS** ✓ SELECTED
  - Extremely fast, CPU-optimized
  - Multiple voice options
  - RAM usage: <500MB
  - High quality output

- **Kokoro TTS**
  - New model, excellent quality
  - Good CPU performance
  - Alternative for premium voices

- **MeloTTS**
  - Multi-language support
  - Moderate speed
  - Backup option

**Rationale:** Piper TTS is battle-tested, fast, and lightweight. Perfect for viral content requiring quick generation.

---

### 3. Image Generation
**Selected: Stable Diffusion 1.5 with optimizations**

**Options Evaluated:**
- **Stable Diffusion 1.5 + Core ML** ✓ SELECTED
  - Apple-optimized
  - RAM usage: 4-6GB
  - Generation time: ~3-5 sec/image on M4

- **SDXL-Turbo**
  - Ultra-fast (1-4 steps)
  - RAM usage: 6-8GB
  - May be tight on 16GB with other processes
  - Consider for future optimization

- **LCM-LoRA models**
  - Lightning-fast inference
  - Alternative for speed optimization

**Rationale:** SD 1.5 with Core ML optimization strikes best balance for M4 Mac. Reliable, well-documented, sufficient quality for social media.

---

### 4. Video Assembly & Editing
**Selected: FFmpeg + MoviePy**

- **FFmpeg:** Industry-standard video processing
- **MoviePy:** Python wrapper for easier scripting
- **Ken Burns Effect:** For dynamic image motion
- **Caption Overlay:** FFmpeg drawtext with viral styling

---

## Memory Budget (Estimated)

| Component | RAM Usage | Notes |
|-----------|-----------|-------|
| LLM (Llama 3.2 3B) | 4-6 GB | During script generation |
| TTS (Piper) | <500 MB | Concurrent with other tasks |
| SD 1.5 | 4-6 GB | Peak during image gen |
| Video Processing | 2-3 GB | FFmpeg/MoviePy |
| **System + Buffer** | 2-3 GB | macOS overhead |
| **Total Peak** | ~14-15 GB | Sequential pipeline avoids peak |

**Strategy:** Run LLM and image generation sequentially, not in parallel, to stay within 16GB limit.

---

## Installation Requirements

```bash
# Core dependencies
- Python 3.10+
- mlx and mlx-lm (for LLM)
- piper-tts
- diffusers + Core ML Stable Diffusion
- ffmpeg
- moviepy
```

---

## Performance Expectations

| Task | Expected Time | Notes |
|------|---------------|-------|
| Script Generation | 10-20 sec | 500-800 tokens |
| TTS Generation | 3-5 sec | 30-60 sec audio |
| Image Generation (per image) | 3-5 sec | 5-8 images per reel |
| Video Assembly | 10-20 sec | Full pipeline |
| **Total Pipeline** | **60-90 sec** | For 30-60 sec reel |

---

## Next Steps
- [x] Research complete
- [x] Architecture designed
- [ ] Set up development environment
- [ ] Implement components
