"""
pipeline.py — Reels Factory: main entry point.

Usage
-----
    # Process all pending topics in input/topics/
    python pipeline.py

    # Process a single topic by name (no .txt extension)
    python pipeline.py --topic "The_Berlin_Wall"

    # Skip script generation (use existing script)
    python pipeline.py --skip-script

    # Skip voiceover generation (use existing mp3)
    python pipeline.py --skip-voice

    # Disable captions for this run
    python pipeline.py --no-captions

Topic file format (input/topics/<slug>.txt)
-------------------------------------------
    Title: The Fall of the Berlin Wall
    ---
    <any amount of raw text, notes, story, bullet points>
    The title line is optional — if missing, the filename is used as title.

Image folder: input/images/<slug>/
    Drop any number of JPG/PNG/WEBP images here.
    They will be displayed in sorted filename order.
"""

import argparse
import datetime as dt
import logging
import sys
import time
from pathlib import Path

import config  # must be imported before stages (sets up dirs)
from stages import script as script_stage
from stages import voice as voice_stage
from stages import video as video_stage
from stages import captions as caption_stage

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_FILE = config.LOGS_DIR / "pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_slug(s: str) -> str:
    return "".join(c for c in s.replace(" ", "_") if c.isalnum() or c in ("_", "-"))[:120]


def month_render_dir() -> Path:
    now = dt.datetime.now()
    d = config.RENDERS_ROOT / f"{now.year:04d}-{now.month:02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def parse_topic_file(topic_file: Path) -> tuple[str, str]:
    """
    Parse a topic .txt file into (title, content).

    Format:
        Title: Some Title Here   ← optional first line
        ---                      ← optional separator
        ... body content ...
    """
    raw = topic_file.read_text(encoding="utf-8").strip()

    # Extract explicit title line if present
    lines = raw.splitlines()
    title = ""
    content_start = 0

    if lines and lines[0].lower().startswith("title:"):
        title = lines[0].split(":", 1)[1].strip()
        content_start = 1
        # Skip optional separator line
        if len(lines) > 1 and lines[1].strip() in ("---", "===", ""):
            content_start = 2

    if not title:
        # Use filename as title (convert underscores to spaces)
        title = topic_file.stem.replace("_", " ")

    content = "\n".join(lines[content_start:]).strip()
    return title, content


def get_pending_topics() -> list[Path]:
    """Return all .txt files in input/topics/ that don't have a rendered video yet."""
    all_topics = sorted(config.TOPICS_DIR.glob("*.txt"))
    if not all_topics:
        return []

    render_dir = month_render_dir()
    pending = []
    for t in all_topics:
        slug = t.stem
        existing = list(render_dir.glob(f"*{slug}*.mp4"))
        if existing:
            log.info("⏭️  Skipping %s (video exists)", slug)
        else:
            pending.append(t)
    return pending


# ── Per-topic pipeline ────────────────────────────────────────────────────────

def run_topic(
    topic_file: Path,
    skip_script: bool = False,
    skip_voice: bool = False,
    add_captions: bool = True,
    show_title_card: bool = True,
) -> Path:
    """
    Full pipeline for a single topic file.
    Returns the path of the rendered video.
    """
    t0 = time.time()
    slug = topic_file.stem
    title, content = parse_topic_file(topic_file)

    log.info("")
    log.info("=" * 60)
    log.info("🎬  %s", title)
    log.info("=" * 60)

    # ── Stage 1: Script ───────────────────────────────────────────
    script_path = config.SCRIPTS_DIR / f"{slug}.txt"
    if skip_script and script_path.exists():
        script_text = script_path.read_text(encoding="utf-8").strip()
        log.info("📝 Using existing script (%d words)", len(script_text.split()))
    else:
        script_text = script_stage.generate_script(title, content, slug)

    # ── Stage 2: Voiceover ────────────────────────────────────────
    voice_path = config.VOICEOVERS_DIR / f"{slug}.mp3"
    if skip_voice and voice_path.exists():
        log.info("🎙️  Using existing voiceover: %s", voice_path.name)
    else:
        voice_path = voice_stage.generate_voiceover(script_text, slug)

    # ── Stage 3: Video assembly ───────────────────────────────────
    # title_card_duration is returned so captions can be offset correctly
    video_clip, title_card_dur = video_stage.assemble_video(
        slug=slug,
        voice_path=voice_path,
        title=title,
        show_title_card=show_title_card,
    )

    # ── Stage 4: Captions ─────────────────────────────────────────
    # Captions are timed against the voiceover, which starts AFTER the title
    # card. We pass the offset so each caption fires at the right moment.
    if add_captions:
        from moviepy.editor import AudioFileClip as _AFC
        voice_dur = _AFC(str(voice_path)).duration
        video_clip = caption_stage.add_captions(
            video_clip, script_text, voice_dur,
            time_offset=title_card_dur,
        )

    # ── Stage 5: Render ───────────────────────────────────────────
    render_dir = month_render_dir()
    date_str   = dt.datetime.now().strftime("%Y-%m-%d")
    out_mp4    = render_dir / f"{date_str}_{slug}_v1.mp4"
    thumb_png  = render_dir / f"{date_str}_{slug}_v1_thumb.png"

    log.info("🖥️  Rendering → %s", out_mp4.name)
    video_clip.write_videofile(
        str(out_mp4),
        fps=config.FPS,
        codec=config.VIDEO_CODEC,
        audio_codec=config.AUDIO_CODEC,
        preset=config.VIDEO_PRESET,
        ffmpeg_params=["-crf", config.VIDEO_CRF],
        threads=4,
        logger=None,     # suppress verbose MoviePy progress bar
    )

    # Thumbnail at ~20% into the video
    thumb_t = max(0.5, video_clip.duration * 0.20)
    video_clip.save_frame(str(thumb_png), t=thumb_t)

    # Cleanup
    try:
        video_clip.close()
    except Exception:
        pass

    elapsed = time.time() - t0
    log.info("✅  Done in %.0fs  →  %s", elapsed, out_mp4.name)
    log.info("📸  Thumbnail     →  %s", thumb_png.name)

    return out_mp4


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Reels Factory — generate Instagram Reels from topic files"
    )
    parser.add_argument(
        "--topic", "-t",
        help="Process a single topic by slug/filename (without .txt). "
             "If omitted, all pending topics are processed.",
    )
    parser.add_argument(
        "--skip-script", action="store_true",
        help="Skip script generation and use existing script file.",
    )
    parser.add_argument(
        "--skip-voice", action="store_true",
        help="Skip voiceover generation and use existing mp3.",
    )
    parser.add_argument(
        "--no-captions", action="store_true",
        help="Disable caption overlay for this run.",
    )
    parser.add_argument(
        "--no-title-card", action="store_true",
        help="Disable the intro title card.",
    )
    args = parser.parse_args()

    add_captions   = not args.no_captions
    show_title_card = not args.no_title_card

    # Determine topic list
    if args.topic:
        slug = safe_slug(args.topic)
        topic_file = config.TOPICS_DIR / f"{slug}.txt"
        if not topic_file.exists():
            log.error("❌  Topic file not found: %s", topic_file)
            sys.exit(1)
        topics = [topic_file]
    else:
        topics = get_pending_topics()

    if not topics:
        log.info("")
        log.info("✅  Nothing to process.")
        log.info("")
        log.info("To create a video:")
        log.info("  1. Add a topic file to:  input/topics/<slug>.txt")
        log.info("  2. Add your images to:   input/images/<slug>/")
        log.info("  3. Run:                  python pipeline.py")
        return

    log.info("📚  %d topic(s) to process", len(topics))

    success, failed = 0, []
    total_start = time.time()

    for topic_file in topics:
        try:
            run_topic(
                topic_file,
                skip_script=args.skip_script,
                skip_voice=args.skip_voice,
                add_captions=add_captions,
                show_title_card=show_title_card,
            )
            success += 1
        except Exception as e:
            log.exception("❌  FAILED: %s — %s", topic_file.stem, e)
            failed.append(topic_file.stem)

    total_elapsed = time.time() - total_start
    log.info("")
    log.info("=" * 60)
    log.info("📊  SUMMARY")
    log.info("=" * 60)
    log.info("✅  Success : %d / %d", success, len(topics))
    if failed:
        log.info("❌  Failed  : %s", ", ".join(failed))
    log.info("⏱️   Total   : %.0fs", total_elapsed)
    log.info("📁  Output  : %s", month_render_dir())


if __name__ == "__main__":
    main()
