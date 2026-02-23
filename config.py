"""
config.py — Central configuration for the Reels Factory pipeline.
All tuneable settings live here. Edit this file, not the stage files.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

INPUT_DIR       = BASE / "input"
TOPICS_DIR      = INPUT_DIR / "topics"       # .txt files — one per topic
IMAGES_BASE_DIR = INPUT_DIR / "images"       # sub-folder per topic with your images

ASSETS_DIR      = BASE / "assets"
MUSIC_DIR       = ASSETS_DIR / "music"
FONTS_DIR       = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"  # fallback if no images provided

CONTENT_DIR     = BASE / "content"
SCRIPTS_DIR     = CONTENT_DIR / "scripts"
VOICEOVERS_DIR  = CONTENT_DIR / "voiceovers"

RENDERS_ROOT    = BASE / "renders"
LOGS_DIR        = BASE / "logs"

# Auto-create all required directories
for _d in [TOPICS_DIR, IMAGES_BASE_DIR, SCRIPTS_DIR, VOICEOVERS_DIR,
           RENDERS_ROOT, LOGS_DIR, MUSIC_DIR, FONTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
ELEVEN_API_KEY   = os.getenv("ELEVEN_API_KEY", "")

# ── LM Studio (local LLM) ─────────────────────────────────────────────────────
# LM Studio exposes an OpenAI-compatible server on localhost:1234
# Start the server in LM Studio before running the pipeline.
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_API_KEY  = os.getenv("LM_STUDIO_API_KEY", "lm-studio")  # any string works

# Model to use for script generation.
# "yi-1.5-34b-chat" is the best narrative model you have downloaded.
# Switch to any other loaded model id from LM Studio's model list.
LM_STUDIO_MODEL    = os.getenv("LM_STUDIO_MODEL", "yi-1.5-34b-chat")

# ── Script Generation ─────────────────────────────────────────────────────────
# Use "local" for LM Studio, "openai" for OpenAI API cloud fallback
SCRIPT_BACKEND = os.getenv("SCRIPT_BACKEND", "local")   # "local" | "openai"
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Word count target — ElevenLabs reads ~140 wpm, so 130-150 ≈ 55-65 seconds
SCRIPT_MIN_WORDS = int(os.getenv("SCRIPT_MIN_WORDS", "130"))
SCRIPT_MAX_WORDS = int(os.getenv("SCRIPT_MAX_WORDS", "150"))

# ── TTS / Voiceover ───────────────────────────────────────────────────────────
# "elevenlabs" uses the API. "kokoro" uses local model (no internet needed).
TTS_BACKEND = os.getenv("TTS_BACKEND", "elevenlabs")   # "elevenlabs" | "kokoro"

# ElevenLabs settings
# Voice IDs worth trying for narration:
#   George (warm storyteller, British):  JBFqnCBsd6RMkjVDRZzb  ← CURRENT (best for reels)
#   Brian (deep, resonant):              nPczCjzI2devNBz1zQrb
#   Daniel (steady broadcaster, Brit):   onwK4e9ZLuTAKqWW03F9
#   Bill (wise, mature):                 pqHfZKP75CvOlQylNhV4
#   Adam (dominant, authoritative):      pNInz6obpgDQGcFmaJgB
#   Charlie (deep, energetic, Aus):      IKne3meq5aSn9XLyUdCD
ELEVEN_VOICE_ID    = os.getenv("ELEVEN_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # George
# Models: eleven_v3 (best, emotional), eleven_multilingual_v2 (solid fallback)
ELEVEN_MODEL       = os.getenv("ELEVEN_MODEL", "eleven_v3")
# eleven_v3 stability: must be exactly 0.0 (Creative), 0.5 (Natural), or 1.0 (Robust)
# eleven_multilingual_v2: accepts any float 0.0–1.0
# We pick the right value at runtime in voice.py based on the model
ELEVEN_STABILITY   = float(os.getenv("ELEVEN_STABILITY", "0.5"))    # 0.5 = Natural for v3
ELEVEN_SIMILARITY  = float(os.getenv("ELEVEN_SIMILARITY", "0.80"))
ELEVEN_STYLE       = float(os.getenv("ELEVEN_STYLE", "0.45"))        # emotional character
ELEVEN_BOOST       = os.getenv("ELEVEN_BOOST", "true").lower() == "true"

# Kokoro local TTS settings (fallback / offline mode)
KOKORO_VOICE  = os.getenv("KOKORO_VOICE", "af_sky")   # options: af_sky, af_bella, am_adam, am_michael
KOKORO_SPEED  = float(os.getenv("KOKORO_SPEED", "1.0"))

# ── Video ─────────────────────────────────────────────────────────────────────
FRAME_SIZE  = (1080, 1920)   # Instagram Reels 9:16
FPS         = 30

# Ken Burns zoom — fraction of total zoom over a clip's duration
ZOOM_FACTOR = 0.06           # 6% — slightly more dynamic than before

# Seconds of crossfade between images
CROSSFADE_DURATION = 0.6

# Min/max time each image is shown. Images cycle to fill the full duration —
# no black frames, no blank padding.
MIN_SECONDS_PER_IMAGE = float(os.getenv("MIN_SECONDS_PER_IMAGE", "3.0"))
MAX_SECONDS_PER_IMAGE = float(os.getenv("MAX_SECONDS_PER_IMAGE", "15.0"))

# Audio mix
VOICE_GAIN  = 1.0
MUSIC_GAIN  = 0.12           # background music at 12% — keeps voice clear

# ── Captions ─────────────────────────────────────────────────────────────────
CAPTIONS_ENABLED   = os.getenv("CAPTIONS_ENABLED", "true").lower() == "true"

# Font for captions. Falls back to system default if file not found.
CAPTION_FONT       = str(FONTS_DIR / "Impact.ttf")

# Visual style
CAPTION_FONT_SIZE   = int(os.getenv("CAPTION_FONT_SIZE", "72"))
CAPTION_COLOR       = os.getenv("CAPTION_COLOR", "white")
CAPTION_STROKE_COLOR= os.getenv("CAPTION_STROKE_COLOR", "black")
CAPTION_STROKE_WIDTH= int(os.getenv("CAPTION_STROKE_WIDTH", "4"))

# Words shown per caption card (word-by-word style)
CAPTION_WORDS_PER_CARD = int(os.getenv("CAPTION_WORDS_PER_CARD", "3"))

# Vertical position of caption block (fraction from top, 0.0-1.0)
CAPTION_Y_POSITION  = float(os.getenv("CAPTION_Y_POSITION", "0.82"))

# ── Output ────────────────────────────────────────────────────────────────────
VIDEO_CODEC  = "libx264"
AUDIO_CODEC  = "aac"
VIDEO_PRESET = "fast"        # ultrafast → fast: slightly better quality, still quick
VIDEO_CRF    = "20"          # 18=visually lossless, 23=default, 20 is a good balance
