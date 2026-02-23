"""
stages/video.py — Video assembly stage.

Takes your input images + voiceover and builds a polished 9:16 video:
  - Each image gets equal screen time across the voiceover duration
  - Ken Burns (slow zoom + pan) effect on each image
  - Crossfade transitions between images
  - Background music mixed under the voiceover
  - Optional: intro title card, outro card
  - Captions composited on top (handled in stages/captions.py)
"""

import glob
import logging
import math
import random
from itertools import cycle
from pathlib import Path
from typing import List, Optional

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    ImageClip,
    VideoClip,
    concatenate_audioclips,
    concatenate_videoclips,
    vfx,
)
from PIL import Image as PILImage
import numpy as np

import config

log = logging.getLogger(__name__)

# ── Image utilities ───────────────────────────────────────────────────────────

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in _IMAGE_EXTENSIONS


def find_images(slug: str) -> List[Path]:
    """
    Return sorted list of image paths for a topic slug.
    Looks in input/images/<slug>/.
    """
    img_dir = config.IMAGES_BASE_DIR / slug
    if not img_dir.exists():
        log.warning("📁 No image folder found at %s", img_dir)
        return []

    images = sorted(p for p in img_dir.iterdir() if _is_image(p))
    log.info("🖼️  Found %d image(s) in %s/", len(images), img_dir.name)
    return images


def _load_image_as_rgb_array(path: Path) -> np.ndarray:
    """Load image, convert to RGB (strips alpha), return numpy array."""
    img = PILImage.open(str(path)).convert("RGB")
    return np.array(img)


def _cover_crop(img_array: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """
    CSS `background-size: cover` equivalent.
    Scales the image so it fills target dimensions, then centre-crops.
    Prevents letterboxing / pillarboxing.

    Uses math.ceil (not int/floor) so the scaled image is always >= target
    size — float truncation was causing 1-pixel underflow → 1-row output.
    """
    h, w = img_array.shape[:2]
    scale = max(target_w / w, target_h / h)
    # ceil guarantees new_w >= target_w and new_h >= target_h always
    new_w = max(math.ceil(w * scale), target_w)
    new_h = max(math.ceil(h * scale), target_h)

    pil = PILImage.fromarray(img_array).resize((new_w, new_h), PILImage.LANCZOS)
    arr = np.array(pil)

    # Centre crop
    top  = (new_h - target_h) // 2
    left = (new_w - target_w) // 2
    return np.ascontiguousarray(arr[top : top + target_h, left : left + target_w])


# ── Ken Burns effect ──────────────────────────────────────────────────────────

def _make_ken_burns_clip(
    img_path: Path,
    duration: float,
    zoom_in: bool = True,
) -> VideoClip:
    """
    Create an ImageClip with a smooth Ken Burns zoom effect.

    zoom_in=True  → starts at 100%, ends at 100% + ZOOM_FACTOR
    zoom_in=False → starts at 100% + ZOOM_FACTOR, ends at 100% (zoom out)
    """
    tw, th = config.FRAME_SIZE
    arr = _load_image_as_rgb_array(img_path)
    arr = _cover_crop(arr, tw, th)

    # We need a slightly larger source to accommodate zoom
    pad = config.ZOOM_FACTOR
    src_w = int(tw * (1 + pad))
    src_h = int(th * (1 + pad))
    pil_large = PILImage.fromarray(arr).resize((src_w, src_h), PILImage.LANCZOS)
    arr_large = np.array(pil_large)

    def make_frame(t: float) -> np.ndarray:
        progress = t / max(duration, 0.001)
        if zoom_in:
            # Zoom in: start at full oversized, end cropped to centre
            scale_progress = 1.0 - progress * pad / (1 + pad)
        else:
            # Zoom out: start cropped, end at full oversized view
            scale_progress = (1.0 - pad / (1 + pad)) + progress * pad / (1 + pad)

        curr_w = int(src_w * scale_progress)
        curr_h = int(src_h * scale_progress)
        curr_w = max(curr_w, tw)
        curr_h = max(curr_h, th)

        frame_pil = PILImage.fromarray(arr_large).resize((curr_w, curr_h), PILImage.LANCZOS)
        frame_arr = np.array(frame_pil)

        top  = (curr_h - th) // 2
        left = (curr_w - tw) // 2
        cropped = frame_arr[top : top + th, left : left + tw]
        return np.ascontiguousarray(cropped)

    clip = VideoClip(make_frame, duration=duration)
    clip = clip.fx(vfx.fadein, min(0.4, duration * 0.1))
    clip = clip.fx(vfx.fadeout, min(0.4, duration * 0.1))
    return clip


# ── Background music ──────────────────────────────────────────────────────────

def _get_music_clip(target_duration: float) -> Optional[AudioFileClip]:
    """Load background music, loop if needed to cover the full duration."""
    music_files = []
    for ext in ("*.mp3", "*.wav", "*.m4a"):
        music_files.extend(config.MUSIC_DIR.glob(ext))

    if not music_files:
        log.warning("🎵 No music files found in %s — skipping music", config.MUSIC_DIR)
        return None

    music_path = random.choice(music_files)
    log.info("🎵 Music: %s", music_path.name)

    music = AudioFileClip(str(music_path))

    if music.duration < target_duration:
        loops = int(target_duration / music.duration) + 2
        music = concatenate_audioclips([music] * loops)

    # Hard-trim to exactly target duration, with a short fade out at end
    music = music.subclip(0, target_duration)
    music = music.audio_fadeout(min(2.0, target_duration * 0.05))
    music = music.volumex(config.MUSIC_GAIN)
    return music


# ── Title card ────────────────────────────────────────────────────────────────

def _make_title_card(title: str, duration: float = 2.5) -> VideoClip:
    """
    Dark title card rendered entirely with Pillow — no ImageMagick needed.
    """
    tw, th = config.FRAME_SIZE

    try:
        from PIL import ImageFont as _IF, ImageDraw as _ID
        font_size = 80
        try:
            font = _IF.truetype(config.CAPTION_FONT, font_size)
        except Exception:
            font = _IF.load_default()

        # Render once, return as a static VideoClip
        canvas = PILImage.new("RGB", (tw, th), (10, 10, 10))
        draw = _ID.Draw(canvas)

        display = title.upper()
        bbox = draw.textbbox((0, 0), display, font=font)
        text_w = bbox[2] - bbox[0]

        # Word-wrap if needed
        max_w = int(tw * 0.82)
        if text_w > max_w:
            words = display.split()
            lines, current = [], []
            for word in words:
                test = " ".join(current + [word])
                if draw.textbbox((0, 0), test, font=font)[2] <= max_w or not current:
                    current.append(word)
                else:
                    lines.append(" ".join(current))
                    current = [word]
            if current:
                lines.append(" ".join(current))
            display = "\n".join(lines)
            bbox = draw.textbbox((0, 0), display, font=font)

        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (tw - text_w) // 2
        y = (th - text_h) // 2

        # Stroke
        sw = 3
        for dx in range(-sw, sw + 1):
            for dy in range(-sw, sw + 1):
                if dx or dy:
                    draw.text((x + dx, y + dy), display, font=font, fill="black")
        draw.text((x, y), display, font=font, fill="white")

        frame_arr = np.array(canvas)
        card = ImageClip(frame_arr, duration=duration)
    except Exception as e:
        log.warning("⚠️  Title card render failed (%s) — using plain dark card", e)
        card = ColorClip(size=(tw, th), color=(10, 10, 10), duration=duration)

    card = card.fx(vfx.fadein, 0.3).fx(vfx.fadeout, 0.3)
    return card


# ── Playlist builder (cycling) ────────────────────────────────────────────────

def _build_cycled_playlist(
    images: List[Path],
    total_duration: float,
    time_per_image: float,
) -> List[Path]:
    """
    Return a list of image paths (with repetition) that covers total_duration.
    Images cycle in order: 1,2,3,1,2,3,... — never blank black frames.
    """
    slots_needed = int(total_duration / time_per_image) + 1
    img_cycle = cycle(images)
    return [next(img_cycle) for _ in range(slots_needed)]


# ── Main assembly ─────────────────────────────────────────────────────────────

def assemble_video(
    slug: str,
    voice_path: Path,
    title: str,
    show_title_card: bool = True,
) -> tuple:
    """
    Assemble the full video from images + voiceover + music.

    Returns (VideoClip, title_card_duration_seconds).
    The title_card_duration is passed to the captions stage so caption
    timings are correctly offset to start after the title card.
    """
    tw, th = config.FRAME_SIZE

    # --- Audio ---
    voice = AudioFileClip(str(voice_path)).volumex(config.VOICE_GAIN)
    narration_dur = voice.duration
    log.info("⏱️  Voiceover duration: %.1fs", narration_dur)

    # --- Images ---
    images = find_images(slug)

    if not images:
        # Fallback to generic backgrounds from assets/backgrounds/
        bg_files = sorted(p for p in config.BACKGROUNDS_DIR.iterdir() if _is_image(p))
        if bg_files:
            images = bg_files
            log.info("📸 No topic images found — using %d background(s) from assets/", len(images))
        else:
            log.warning("⚠️  No images at all — using solid colour background")

    if images:
        # ── Compute per-image duration ────────────────────────────────────────
        # Each image shows for MIN_SECONDS_PER_IMAGE, cycling if the list is
        # too short to fill the full narration duration.
        min_secs = config.MIN_SECONDS_PER_IMAGE          # e.g. 3.0
        max_secs = config.MAX_SECONDS_PER_IMAGE          # e.g. 15.0

        n_images = len(images)
        natural_dur = narration_dur / n_images           # if all images used once

        if natural_dur >= min_secs:
            # Enough images — each gets equal time, no cycling needed
            time_per_image = min(natural_dur, max_secs)
            # If capped by max_secs, cycle to fill remaining time
            playlist = _build_cycled_playlist(images, narration_dur, time_per_image)
        else:
            # Too few images for min time — cap at min_secs and cycle/repeat
            time_per_image = min_secs
            playlist = _build_cycled_playlist(images, narration_dur, time_per_image)

        log.info("🎞️  %d slot(s) × %.1fs each (from %d unique image(s))",
                 len(playlist), time_per_image, n_images)

        image_clips = []
        for i, img_path in enumerate(playlist):
            zoom_in = (i % 2 == 0)   # alternate zoom direction for variety
            try:
                clip = _make_ken_burns_clip(img_path, time_per_image, zoom_in=zoom_in)
                image_clips.append(clip)
                log.info("  ✅ [%d] %s", i + 1, img_path.name)
            except Exception as e:
                log.warning("  ⚠️  Skipping %s: %s", img_path.name, e)

        if not image_clips:
            raise RuntimeError("All images failed to load. Check your input/images/ folder.")

        # Crossfade between clips
        cf = config.CROSSFADE_DURATION
        if len(image_clips) > 1 and cf > 0:
            xfade_clips = [image_clips[0]]
            for clip in image_clips[1:]:
                xfade_clips.append(clip.crossfadein(cf))
            main_video = concatenate_videoclips(xfade_clips, padding=-cf, method="compose")
        else:
            main_video = concatenate_videoclips(image_clips, method="compose")

        # Trim/extend to exactly narration_dur (cycling may overshoot by <time_per_image)
        main_video = main_video.set_duration(narration_dur)

    else:
        # Pure solid colour fallback — should never reach here in practice
        main_video = ColorClip(size=(tw, th), color=(12, 10, 18), duration=narration_dur)

    # --- Music + voice mix ---
    music = _get_music_clip(narration_dur)
    if music:
        mixed_audio = CompositeAudioClip([voice, music])
    else:
        mixed_audio = voice

    main_video = main_video.set_audio(mixed_audio)

    # --- Optional title card prepended ---
    TITLE_CARD_DURATION = 2.5
    title_card_dur = 0.0
    if show_title_card and title:
        title_card = _make_title_card(title, duration=TITLE_CARD_DURATION)
        # Title card has no narration audio — silence for its duration
        final_video = concatenate_videoclips([title_card, main_video], method="compose")
        title_card_dur = TITLE_CARD_DURATION
    else:
        final_video = main_video

    return final_video, title_card_dur
