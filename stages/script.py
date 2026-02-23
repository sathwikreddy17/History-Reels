"""
stages/script.py — Script generation stage.

Converts a raw topic file (any subject) into a tight narration script
using either a local LM Studio model or OpenAI as cloud fallback.

Word count is enforced with a retry loop so the output reliably
produces ~60-second voiceovers.
"""

import logging
import re
from pathlib import Path

from openai import OpenAI

import config

log = logging.getLogger(__name__)

# ── Clients ───────────────────────────────────────────────────────────────────

def _local_client() -> OpenAI:
    """Return an OpenAI-compatible client pointed at LM Studio."""
    return OpenAI(base_url=config.LM_STUDIO_BASE_URL, api_key=config.LM_STUDIO_API_KEY)


def _openai_client() -> OpenAI:
    """Return a real OpenAI client."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in .env")
    return OpenAI(api_key=config.OPENAI_API_KEY)


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert short-form video scriptwriter. You write tight, \
emotionally gripping 60-second narration scripts for Instagram Reels \
on any topic — history, science, culture, biography, philosophy, or anything else.

Rules you MUST follow:
- Total word count: {min_words}–{max_words} words. Count carefully.
- No headings, no labels, no bullet points, no markdown.
- Return ONLY the narration text — nothing else.
- Write in present tense for immediacy.
- Open with a hook that demands attention in the first 5 seconds.
- Use short, punchy sentences. Vary sentence length for rhythm.
- Build to an emotional or surprising peak, then land a memorable closing line.
- Tone matches the content: dramatic for history/action, curious for science, \
  warm for biography, etc.
- No clichés like "In a world where…" or "Little did they know…"
"""

USER_PROMPT = """\
Topic: {title}

Source material:
{content}

Write the narration script now. Remember: {min_words}–{max_words} words, plain text only.
"""


def _count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _call_llm(client: OpenAI, model: str, title: str, content: str) -> str:
    system = SYSTEM_PROMPT.format(
        min_words=config.SCRIPT_MIN_WORDS,
        max_words=config.SCRIPT_MAX_WORDS,
    )
    user = USER_PROMPT.format(
        title=title,
        content=content,
        min_words=config.SCRIPT_MIN_WORDS,
        max_words=config.SCRIPT_MAX_WORDS,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.75,
        max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


# ── Public API ────────────────────────────────────────────────────────────────

def generate_script(title: str, content: str, slug: str) -> str:
    """
    Generate a narration script from a topic title + raw content.

    Retries up to 3 times if the word count is outside the target range.
    Saves the result to content/scripts/<slug>.txt and returns the text.

    Parameters
    ----------
    title   : Human-readable topic title (e.g. "The Fall of the Berlin Wall")
    content : Raw source text — your notes, a story, bullet points, anything
    slug    : Filesystem-safe name (e.g. "The_Fall_of_the_Berlin_Wall")
    """

    # Pick backend
    if config.SCRIPT_BACKEND == "local":
        client = _local_client()
        model  = config.LM_STUDIO_MODEL
        log.info("🧠 Script backend: LM Studio (%s)", model)
    else:
        client = _openai_client()
        model  = config.OPENAI_MODEL
        log.info("🧠 Script backend: OpenAI (%s)", model)

    MAX_RETRIES = 3
    script = ""

    for attempt in range(1, MAX_RETRIES + 1):
        log.info("  Attempt %d/%d…", attempt, MAX_RETRIES)
        try:
            script = _call_llm(client, model, title, content)
        except Exception as e:
            # If local fails, automatically fall back to OpenAI
            if config.SCRIPT_BACKEND == "local" and config.OPENAI_API_KEY:
                log.warning("⚠️  LM Studio failed (%s). Falling back to OpenAI.", e)
                client = _openai_client()
                model  = config.OPENAI_MODEL
                script = _call_llm(client, model, title, content)
            else:
                raise

        words = _count_words(script)
        log.info("  Word count: %d (target %d–%d)", words, config.SCRIPT_MIN_WORDS, config.SCRIPT_MAX_WORDS)

        if config.SCRIPT_MIN_WORDS <= words <= config.SCRIPT_MAX_WORDS:
            break
        elif attempt < MAX_RETRIES:
            direction = "shorter" if words > config.SCRIPT_MAX_WORDS else "longer"
            log.info("  Out of range — requesting %s script…", direction)
            # Prepend a correction note to the content for the next attempt
            content = f"[IMPORTANT: Your previous attempt was {words} words. Make it {direction} — strictly {config.SCRIPT_MIN_WORDS}–{config.SCRIPT_MAX_WORDS} words.]\n\n" + content
    else:
        log.warning("⚠️  Could not hit word count after %d tries. Using last attempt (%d words).", MAX_RETRIES, _count_words(script))

    # Save
    out_path = config.SCRIPTS_DIR / f"{slug}.txt"
    out_path.write_text(script, encoding="utf-8")
    log.info("📝 Script saved → %s  (%d words)", out_path.name, _count_words(script))

    return script
