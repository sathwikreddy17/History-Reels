"""
stages/voice.py — Voiceover generation stage.

Supports two backends:
  - elevenlabs : Cloud API (best quality, needs ELEVEN_API_KEY)
  - kokoro     : Local model on MPS/CPU (free, offline, near-EL quality)

ElevenLabs is used with eleven_v3 + George voice. The text is pre-processed
before sending to the API:
  - 4-digit years → spoken form  (1989 → nineteen eighty-nine)
  - Ordinal numbers → spoken form (12th → twelfth)
  - Plain numbers → spoken form   (42 → forty-two)
  - Sentence-end pauses injected via <break> SSML tags for natural pacing
  - Common abbreviations expanded (USSR, WW2, etc.)
"""

import logging
import re
import time
from pathlib import Path

import requests

import config

log = logging.getLogger(__name__)


# ── Text pre-processing ───────────────────────────────────────────────────────

# Ordinals up to 31 (enough for days/centuries)
_ORDINALS = {
    1:"first",2:"second",3:"third",4:"fourth",5:"fifth",6:"sixth",
    7:"seventh",8:"eighth",9:"ninth",10:"tenth",11:"eleventh",12:"twelfth",
    13:"thirteenth",14:"fourteenth",15:"fifteenth",16:"sixteenth",
    17:"seventeenth",18:"eighteenth",19:"nineteenth",20:"twentieth",
    21:"twenty-first",22:"twenty-second",23:"twenty-third",24:"twenty-fourth",
    25:"twenty-fifth",26:"twenty-sixth",27:"twenty-seventh",28:"twenty-eighth",
    29:"twenty-ninth",30:"thirtieth",31:"thirty-first",
}

_ONES = ["","one","two","three","four","five","six","seven","eight","nine",
         "ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen",
         "seventeen","eighteen","nineteen"]
_TENS = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]

def _int_to_words(n: int) -> str:
    """Convert a non-negative integer up to 9999 into English words."""
    if n == 0:
        return "zero"
    if n < 20:
        return _ONES[n]
    if n < 100:
        ones = n % 10
        return _TENS[n // 10] + ("-" + _ONES[ones] if ones else "")
    if n < 1000:
        rest = n % 100
        return _ONES[n // 100] + " hundred" + (" " + _int_to_words(rest) if rest else "")
    # 1000–9999
    hi, lo = divmod(n, 1000)
    return _ONES[hi] + " thousand" + (" " + _int_to_words(lo) if lo else "")


def _year_to_words(year: int) -> str:
    """1989 → 'nineteen eighty-nine', 2000 → 'two thousand', 2026 → 'twenty twenty-six'"""
    if 1100 <= year <= 1999:
        hi, lo = divmod(year, 100)
        hi_w = _int_to_words(hi)
        if lo == 0:
            return hi_w + " hundred"
        lo_w = _int_to_words(lo) if lo >= 20 else ("oh " + _ONES[lo] if lo < 10 else _int_to_words(lo))
        return hi_w + " " + lo_w
    if 2000 <= year <= 2099:
        lo = year - 2000
        if lo == 0:
            return "two thousand"
        if lo < 10:
            return "two thousand and " + _ONES[lo]
        return "twenty " + _int_to_words(lo)
    return _int_to_words(year)


# Common abbreviations / acronyms that TTS mispronounces
_ABBREVS = {
    r"\bWW1\b": "World War One",
    r"\bWWI\b": "World War One",
    r"\bWW2\b": "World War Two",
    r"\bWWII\b": "World War Two",
    r"\bUSSR\b": "the U.S.S.R.",
    r"\bNATO\b": "NATO",
    r"\bUS\b":   "the U.S.",
    r"\bUSA\b":  "the U.S.A.",
    r"\bUK\b":   "the U.K.",
    r"\bBC\b":   "B.C.",
    r"\bAD\b":   "A.D.",
    r"\bBCE\b":  "B.C.E.",
    r"\bCE\b":   "C.E.",
    r"\bDr\.\b": "Doctor",
    r"\bMr\.\b": "Mister",
    r"\bMrs\.\b":"Missus",
    r"\bSt\.\b": "Saint",
    r"\bvs\.\b": "versus",
    r"\betc\.\b":"et cetera",
}


def _preprocess_text(text: str) -> str:
    """
    Normalise text for natural TTS delivery:
    1. Expand abbreviations
    2. Convert years (4-digit 1000-2099) to spoken form
    3. Convert ordinals (1st, 2nd … 31st) to spoken form
    4. Convert remaining standalone integers to spoken form
    5. Inject <break time="0.4s"/> after sentence-ending punctuation
       so eleven_v3 breathes between sentences
    """
    # 1. Abbreviations
    for pattern, replacement in _ABBREVS.items():
        text = re.sub(pattern, replacement, text)

    # 2. Years — must come before generic number conversion
    def _replace_year(m):
        y = int(m.group(0))
        return _year_to_words(y)
    text = re.sub(r"\b(1[0-9]{3}|20[0-9]{2})\b", _replace_year, text)

    # 3. Ordinals (1st, 2nd, 3rd, 4th … 31st)
    def _replace_ordinal(m):
        n = int(m.group(1))
        return _ORDINALS.get(n, _int_to_words(n) + m.group(2))
    text = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", _replace_ordinal, text, flags=re.IGNORECASE)

    # 4. Remaining standalone integers (not part of a decimal)
    def _replace_int(m):
        return _int_to_words(int(m.group(0)))
    text = re.sub(r"(?<![.\d])\b\d+\b(?![.\d])", _replace_int, text)

    # 5. Sentence-break pauses for natural breathing rhythm
    # After ". " "! " "? " — but not abbreviations (already expanded above)
    text = re.sub(r'([.!?])\s+', r'\1 <break time="0.4s"/> ', text)

    return text.strip()


# ── ElevenLabs ────────────────────────────────────────────────────────────────

def _tts_elevenlabs(script: str, slug: str) -> Path:
    if not config.ELEVEN_API_KEY:
        raise RuntimeError("ELEVEN_API_KEY not set in .env")

    processed = _preprocess_text(script)
    log.debug("  Pre-processed script:\n%s", processed)

    # eleven_v3 only accepts stability ∈ {0.0, 0.5, 1.0}. Snap to nearest.
    stability = config.ELEVEN_STABILITY
    if config.ELEVEN_MODEL == "eleven_v3":
        stability = min([0.0, 0.5, 1.0], key=lambda v: abs(v - stability))
        log.debug("  v3 stability snapped to %.1f", stability)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": config.ELEVEN_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": processed,
        "model_id": config.ELEVEN_MODEL,
        "voice_settings": {
            "stability":         stability,
            "similarity_boost":  config.ELEVEN_SIMILARITY,
            "style":             config.ELEVEN_STYLE,
            "use_speaker_boost": config.ELEVEN_BOOST,
        },
    }

    log.info("🎙️  ElevenLabs TTS → voice=%s  model=%s", config.ELEVEN_VOICE_ID, config.ELEVEN_MODEL)
    for attempt in range(1, 4):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            break
        log.warning("  ElevenLabs attempt %d: HTTP %s — %s", attempt, resp.status_code, resp.text[:120])
        if resp.status_code in (429, 500, 502, 503):
            time.sleep(5 * attempt)
        else:
            raise RuntimeError(f"ElevenLabs error {resp.status_code}: {resp.text[:200]}")

    out = config.VOICEOVERS_DIR / f"{slug}.mp3"
    out.write_bytes(resp.content)
    log.info("  Saved → %s", out.name)
    return out


# ── Kokoro (local) ────────────────────────────────────────────────────────────

def _tts_kokoro(script: str, slug: str) -> Path:
    """
    Generate speech with Kokoro running locally on Apple MPS.
    Saves a 24 kHz WAV then converts to MP3 via ffmpeg.
    """
    try:
        import kokoro
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        raise RuntimeError(
            f"Kokoro or soundfile not installed: {e}. "
            "Run: pip install kokoro soundfile"
        ) from e

    log.info("🎙️  Kokoro local TTS → voice=%s  speed=%.2f", config.KOKORO_VOICE, config.KOKORO_SPEED)

    # Kokoro pipeline — downloads model weights on first run (~85 MB, cached)
    pipeline = kokoro.KPipeline(lang_code="a")  # "a" = American English

    wav_path = config.VOICEOVERS_DIR / f"{slug}_raw.wav"
    mp3_path = config.VOICEOVERS_DIR / f"{slug}.mp3"

    # Generate — Kokoro yields (graphemes, phonemes, audio_array) chunks
    audio_chunks = []
    for _, _, audio in pipeline(script, voice=config.KOKORO_VOICE, speed=config.KOKORO_SPEED):
        audio_chunks.append(audio)

    if not audio_chunks:
        raise RuntimeError("Kokoro returned no audio chunks")

    import numpy as np
    full_audio = np.concatenate(audio_chunks)

    # Save as WAV first (24 kHz mono)
    sf.write(str(wav_path), full_audio, 24000)

    # Convert WAV → MP3 with ffmpeg for consistent downstream handling
    import subprocess
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame",
         "-qscale:a", "2", str(mp3_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg WAV→MP3 failed: {result.stderr[-300:]}")

    wav_path.unlink(missing_ok=True)  # clean up raw WAV
    log.info("  Saved → %s", mp3_path.name)
    return mp3_path


# ── Public API ────────────────────────────────────────────────────────────────

def generate_voiceover(script: str, slug: str) -> Path:
    """
    Generate voiceover audio for a script.
    Uses the backend specified in config.TTS_BACKEND.
    Falls back to the other backend on failure.

    Returns the path to the saved .mp3 file.
    """
    primary = config.TTS_BACKEND.lower()
    fallback = "kokoro" if primary == "elevenlabs" else "elevenlabs"

    def _run(backend: str) -> Path:
        if backend == "elevenlabs":
            return _tts_elevenlabs(script, slug)
        elif backend == "kokoro":
            return _tts_kokoro(script, slug)
        else:
            raise ValueError(f"Unknown TTS backend: {backend!r}")

    try:
        return _run(primary)
    except Exception as e:
        log.warning("⚠️  %s TTS failed: %s. Trying %s…", primary, e, fallback)
        return _run(fallback)
