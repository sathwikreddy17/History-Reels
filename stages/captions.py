"""
stages/captions.py — Animated word-by-word caption overlay.

Uses Pillow to render text frames directly — NO ImageMagick required.

How it works
------------
1. The script is split into small groups of words (e.g. 3 words per card).
2. Each group is assigned a proportional time window based on word count.
3. For each frame of the video, the matching caption card is drawn onto a
   transparent RGBA canvas with Pillow, then composited via numpy.

The result is CapCut / podcast-style animated captions.
"""

import logging
from typing import List, Tuple

import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont
from moviepy.editor import VideoClip

import config

log = logging.getLogger(__name__)


# ── Font loading ──────────────────────────────────────────────────────────────

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load the configured caption font, falling back to PIL default."""
    try:
        return ImageFont.truetype(config.CAPTION_FONT, size)
    except Exception:
        log.warning("⚠️  Could not load font %s — using PIL default", config.CAPTION_FONT)
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


# ── Card splitting & timing ───────────────────────────────────────────────────

def _split_into_cards(script: str, words_per_card: int) -> List[str]:
    words = script.split()
    return [
        " ".join(words[i : i + words_per_card])
        for i in range(0, len(words), words_per_card)
    ]


def _assign_timings(
    cards: List[str], total_duration: float
) -> List[Tuple[str, float, float]]:
    """Returns list of (text, start_sec, end_sec)."""
    total_words = sum(len(c.split()) for c in cards)
    secs_per_word = total_duration / max(total_words, 1)
    timed, cursor = [], 0.0
    for card in cards:
        n = len(card.split())
        end = cursor + n * secs_per_word
        timed.append((card, cursor, end))
        cursor = end
    return timed


# ── Pillow text rendering ─────────────────────────────────────────────────────

def _render_caption_frame(
    text: str,
    frame_w: int,
    frame_h: int,
    font: ImageFont.FreeTypeFont,
) -> np.ndarray:
    """
    Render caption text onto a transparent RGBA frame using Pillow.
    Returns an RGBA numpy array of shape (frame_h, frame_w, 4).
    """
    canvas = PILImage.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    display_text = text.upper()

    # Measure text bounding box
    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Wrap text if it's wider than 88% of the frame
    max_w = int(frame_w * 0.88)
    if text_w > max_w:
        words = display_text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            tw = draw.textbbox((0, 0), test_line, font=font)[2]
            if tw <= max_w or not current_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        display_text = "\n".join(lines)
        bbox = draw.textbbox((0, 0), display_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    # Position: centred horizontally, at CAPTION_Y_POSITION vertically
    x = (frame_w - text_w) // 2
    y = int(frame_h * config.CAPTION_Y_POSITION) - text_h // 2

    sw = config.CAPTION_STROKE_WIDTH

    # Draw stroke (shadow outline) by drawing text offset in all directions
    stroke_color = config.CAPTION_STROKE_COLOR
    for dx in range(-sw, sw + 1):
        for dy in range(-sw, sw + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), display_text, font=font, fill=stroke_color)

    # Draw main text
    draw.text((x, y), display_text, font=font, fill=config.CAPTION_COLOR)

    return np.array(canvas)


# ── Compositing ───────────────────────────────────────────────────────────────

def _composite_caption(base_frame: np.ndarray, caption_rgba: np.ndarray) -> np.ndarray:
    """Alpha-composite caption RGBA over a BGR/RGB base frame (uint8)."""
    alpha = caption_rgba[:, :, 3:4].astype(np.float32) / 255.0
    caption_rgb = caption_rgba[:, :, :3].astype(np.float32)
    base = base_frame.astype(np.float32)
    result = base * (1.0 - alpha) + caption_rgb * alpha
    return result.clip(0, 255).astype(np.uint8)


# ── Public API ────────────────────────────────────────────────────────────────

def add_captions(
    video: VideoClip,
    script: str,
    audio_duration: float,
    time_offset: float = 0.0,
) -> VideoClip:
    """
    Composite animated word-group captions onto a VideoClip.
    Uses Pillow — no ImageMagick required.

    Parameters
    ----------
    video          : The assembled video (without captions)
    script         : The narration script text
    audio_duration : Duration of the voiceover in seconds
    time_offset    : Seconds to shift all caption timings by (e.g. title card duration)
    """
    if not config.CAPTIONS_ENABLED:
        return video

    log.info("💬 Generating captions (%d words/card)…", config.CAPTION_WORDS_PER_CARD)

    cards = _split_into_cards(script, config.CAPTION_WORDS_PER_CARD)
    timed = _assign_timings(cards, audio_duration)

    # Shift all timings so captions start after the title card (or any offset)
    if time_offset:
        timed = [(text, start + time_offset, end + time_offset) for text, start, end in timed]
        log.info("  ⏱  Caption timings shifted by +%.2fs (title card offset)", time_offset)

    fw, fh = config.FRAME_SIZE
    font = _load_font(config.CAPTION_FONT_SIZE)

    # Pre-render all caption frames (RGBA arrays)
    card_frames = {}
    for text, start, end in timed:
        card_frames[(start, end)] = _render_caption_frame(text, fw, fh, font)

    log.info("  ✅ %d caption cards pre-rendered", len(card_frames))

    original_make_frame = video.make_frame

    def make_captioned_frame(t: float) -> np.ndarray:
        base = original_make_frame(t)
        # Find which caption card is active at time t
        for (start, end), caption_rgba in card_frames.items():
            if start <= t < end:
                return _composite_caption(base, caption_rgba)
        return base

    result = VideoClip(make_captioned_frame, duration=video.duration)
    result = result.set_audio(video.audio)
    return result
