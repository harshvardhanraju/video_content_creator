"""
Video Assembler Module

Combines audio, images, and captions into final vertical reel.
"""

from .compositor import VideoCompositor
from .caption_generator import CaptionGenerator

__all__ = ["VideoCompositor", "CaptionGenerator"]
