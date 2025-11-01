import os
import csv
import glob
import json
import time
import random
import logging
import datetime as dt
from pathlib import Path

import requests
from dotenv import load_dotenv

# MoviePy
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    vfx,
)

# ──────────────────────────────────────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

# OpenAI (>=1.0.0)
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    openai_client = None

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # set your favorite voice in .env

# Paths
ASSETS_DIR      = BASE / "assets"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
MUSIC_DIR       = ASSETS_DIR / "music"
INTROS_DIR      = ASSETS_DIR / "intros"
OUTROS_DIR      = ASSETS_DIR / "outros"

CONTENT_DIR     = BASE / "content"
TOPICS_CSV      = CONTENT_DIR / "topics.csv"
SCRIPTS_DIR     = CONTENT_DIR / "scripts"
VOICEOVERS_DIR  = CONTENT_DIR / "voiceovers"
VISUALS_DIR     = CONTENT_DIR / "visuals"     # reserved for future scene images
SUBTITLES_DIR   = CONTENT_DIR / "subtitles"   # reserved for future SRTs

RENDERS_ROOT    = BASE / "renders"
LOGS_DIR        = BASE / "logs"

for p in [SCRIPTS_DIR, VOICEOVERS_DIR, VISUALS_DIR, SUBTITLES_DIR, LOGS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Logging
LOG_FILE = LOGS_DIR / "run.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# Render settings
FPS           = 30
FRAME_SIZE    = (1080, 1920)  # 9:16
VOICE_GAIN    = 1.0
MUSIC_GAIN    = 0.15          # bed volume relative to voice
ZOOM_FACTOR   = 0.04          # total zoom over each clip (~4%)
MIN_SCENES    = 3             # backgrounds per video
MAX_SCENES    = 5

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def month_render_dir():
    now = dt.datetime.now()
    d = RENDERS_ROOT / f"{now.year:04d}-{now.month:02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d

def safe_slug(s: str) -> str:
    return "".join(c for c in s.replace(" ", "_") if c.isalnum() or c in ("_", "-", "."))[:120]

def read_next_topic(csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing topics CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if row.get("status", "").strip().lower() == "todo":
            return row, rows
    return None, rows

def write_topics(csv_path: Path, rows):
    if not rows:
        return
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def mark_done(topic_id: str, rows, success=True, error_msg=None):
    for r in rows:
        if r.get("id") == topic_id:
            r["status"] = "done" if success else f"error:{(error_msg or '')[:40]}"
            break
    write_topics(TOPICS_CSV, rows)

def read_prompt() -> str:
    prompt_file = BASE / "prompts" / "script_prompt.txt"
    with prompt_file.open("r", encoding="utf-8") as f:
        return f.read()

# ──────────────────────────────────────────────────────────────────────────────
# AI calls
# ──────────────────────────────────────────────────────────────────────────────
def generate_script(title: str, description: str) -> str:
    if openai_client is None:
        raise RuntimeError("OpenAI client not initialized. Install openai>=1.0 and set OPENAI_API_KEY.")
    template = read_prompt()
    user_prompt = template.format(title=title, description=description)

    logging.info("Calling OpenAI for script…")
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.7,
        max_tokens=400
    )
    text = resp.choices[0].message.content.strip()
    out_path = SCRIPTS_DIR / f"{safe_slug(title)}.txt"
    out_path.write_text(text, encoding="utf-8")
    logging.info("Script saved -> %s", out_path)
    return text

def tts_elevenlabs(text: str, title: str) -> Path:
    if not ELEVEN_API_KEY:
        raise RuntimeError("Missing ELEVEN_API_KEY in .env")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}

    logging.info("Calling ElevenLabs TTS…")
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    out = VOICEOVERS_DIR / f"{safe_slug(title)}.mp3"
    out.write_bytes(r.content)
    logging.info("Voiceover saved -> %s", out)
    return out

# ──────────────────────────────────────────────────────────────────────────────
# Visual assembly
# ──────────────────────────────────────────────────────────────────────────────
def pick_backgrounds(n: int):
    # Only pick image files, not README.md or other non-image files
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"]
    imgs = []
    for pattern in patterns:
        imgs.extend(glob.glob(str(BACKGROUNDS_DIR / pattern)))
    imgs = sorted(imgs)
    if not imgs:
        return []
    if n >= len(imgs):
        random.shuffle(imgs)
        return imgs
    return random.sample(imgs, n)

def make_zoom_clip(img_path: Path, duration: float):
    """
    Gentle Ken Burns (zoom/pan) effect.
    """
    clip = ImageClip(str(img_path)).resize(FRAME_SIZE).set_duration(duration)
    # subtle zoom from 100% to (100% + ZOOM_FACTOR)
    # MoviePy trick: resize by a factor that depends on time t (0..duration)
    def scaler(t):
        return 1.0 + (ZOOM_FACTOR * (t / max(duration, 0.1)))
    return clip.resize(lambda t: scaler(t)).fx(vfx.fadein, 0.25).fx(vfx.fadeout, 0.25)

def enhance_video_clip(clip, effect_type="cinematic"):
    """
    Add professional effects to video clips
    """
    try:
        if effect_type == "cinematic":
            # Add cinematic color grading and effects
            clip = clip.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5)
            
            # Slight zoom effect (Ken Burns style)
            if hasattr(clip, 'resize'):
                def zoom_effect(t):
                    # Subtle zoom from 100% to 105% over duration
                    zoom = 1.0 + (0.05 * (t / clip.duration))
                    return zoom
                clip = clip.resize(lambda t: zoom_effect(t))
            
        elif effect_type == "dramatic":
            # More dramatic effects for action scenes
            clip = clip.fx(vfx.fadein, 0.3).fx(vfx.fadeout, 0.3)
            
        elif effect_type == "mystical":
            # Mystical/ethereal effects
            clip = clip.fx(vfx.fadein, 1.0).fx(vfx.fadeout, 1.0)
            
        return clip
        
    except Exception as e:
        logging.warning(f"Error applying effects to video clip: {e}")
        return clip

def build_video(title: str, voice_path: Path) -> Path:
    # Resolve assets
    intro_candidates = sorted(glob.glob(str(INTROS_DIR / "*.mp4")))
    outro_candidates = sorted(glob.glob(str(OUTROS_DIR / "*.mp4")))
    music_candidates = sorted(glob.glob(str(MUSIC_DIR  / "*.mp3")))

    # Load audio
    voice = AudioFileClip(str(voice_path)).volumex(VOICE_GAIN)
    narration_dur = voice.duration

    music_clip = None
    if music_candidates:
        music_clip = AudioFileClip(music_candidates[0]).volumex(MUSIC_GAIN)
        # Ensure music doesn't exceed its natural duration
        needed_duration = narration_dur + 0.5
        if music_clip.duration < needed_duration:
            # Repeat the music if it's shorter than needed
            loops_needed = int(needed_duration / music_clip.duration) + 1
            music_clip = concatenate_audioclips([music_clip] * loops_needed)
        music_clip = music_clip.set_duration(needed_duration)

    # Try to get real video content first, fallback to backgrounds
    video_clips = get_video_content(title, narration_dur)
    
    if video_clips:
        # Use real video content (images or videos)
        main = concatenate_videoclips(video_clips, method="compose")
        logging.info("✨ Using curated content for video")
    else:
        # Fallback to backgrounds with effects
        bg_files = pick_backgrounds(random.randint(MIN_SCENES, MAX_SCENES))
        if not bg_files:
            # Ultimate fallback to solid color
            scene = ColorClip(FRAME_SIZE, color=(18, 12, 8)).set_duration(narration_dur)
            scenes = [scene]
            logging.info("⚠️  Using solid color fallback")
        else:
            # Split narration duration across scenes evenly
            per = narration_dur / len(bg_files)
            scenes = [make_zoom_clip(Path(p), per) for p in bg_files]
            logging.info("📸 Using background images with effects")
        
        main = concatenate_videoclips(scenes, method="compose")
        logging.info("📸 Using background images with effects")
    # Attach audio
    if music_clip:
        audio_mix = CompositeAudioClip([voice, music_clip])
    else:
        audio_mix = voice
    main = main.set_audio(audio_mix)

    # Intro/Outro
    clips = []
    if intro_candidates:
        intro = VideoFileClip(intro_candidates[0]).resize(FRAME_SIZE)
        clips.append(intro)
    clips.append(main)
    if outro_candidates:
        outro = VideoFileClip(outro_candidates[0]).resize(FRAME_SIZE)
        clips.append(outro)

    final = concatenate_videoclips(clips, method="compose")

    # Output paths
    out_dir = month_render_dir()
    date_prefix = dt.datetime.now().strftime("%Y-%m-%d")
    base_name = f"{date_prefix}_{safe_slug(title)}_v1"
    out_mp4 = out_dir / f"{base_name}.mp4"
    thumb_png = out_dir / f"{base_name}_thumb.png"

    # Save thumbnail at 3 seconds (or middle if shorter)
    thumb_t = min(3.0, max(0.1, final.duration / 2))
    final.save_frame(str(thumb_png), t=thumb_t)

    logging.info("Rendering video -> %s", out_mp4)
    # Fast preset to reduce friction; tweak CRF if you want smaller files
    final.write_videofile(
        str(out_mp4),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )

    # Cleanup dynamically opened clips
    try:
        voice.close()
        if music_clip: music_clip.close()
        for c in scenes:
            c.close()
        for c in clips:
            try: c.close()
            except: pass
        final.close()
    except Exception:
        pass

    logging.info("Rendered ✅  %s", out_mp4)
    logging.info("Thumbnail  📸 %s", thumb_png)
    return out_mp4

def get_video_content(title: str, duration: float) -> list:
    """
    Get video content - prioritizes curated images, then local videos, then Pexels API:
    1. Curated images (best quality, specific to mythology)
    2. Local video files  
    3. Pexels API (fallback)
    """
    video_clips = []
    title_slug = safe_slug(title)
    
    # PRIORITY 1: Look for curated images matching this topic
    topic_images_dir = ASSETS_DIR / "images" / title_slug
    if topic_images_dir.exists():
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            image_files.extend(list(topic_images_dir.glob(ext)))
        
        if image_files:
            logging.info(f"🖼️  Found {len(image_files)} curated images for {title}")
            return create_video_from_images(image_files, duration, title)
    
    # PRIORITY 2: Check for existing video files for this topic
    video_dir = ASSETS_DIR / "videos" / title_slug
    if video_dir.exists():
        video_files = list(video_dir.glob("*.mp4"))
        if video_files:
            logging.info(f"🎬 Found {len(video_files)} local videos for {title}")
            total_used = 0
            for video_file in video_files:
                if total_used >= duration:
                    break
                try:
                    clip = VideoFileClip(str(video_file)).resize(FRAME_SIZE)
                    clip_duration = min(clip.duration, duration - total_used)
                    clip = clip.set_duration(clip_duration)
                    
                    # Add some cinematic effects
                    clip = enhance_video_clip(clip, effect_type="cinematic")
                    video_clips.append(clip)
                    total_used += clip_duration
                except Exception as e:
                    logging.warning(f"Error loading video {video_file}: {e}")
                    continue
    
    # If we have enough video content, return it
    if video_clips and sum(clip.duration for clip in video_clips) >= duration * 0.8:
        return video_clips
    
    # PRIORITY 3: If no curated content, try Pexels API as fallback
    if not video_clips or sum(clip.duration for clip in video_clips) < duration * 0.8:
        logging.info("⚠️  No curated content found. Using Pexels API as fallback...")
        pexels_clips = fetch_pexels_videos(title, duration)
        video_clips.extend(pexels_clips)
    
    # Future: Add AI video generation here  
    # video_clips.extend(generate_ai_videos(title, duration))
    
    return video_clips

# ──────────────────────────────────────────────────────────────────────────────
# Video Content APIs
# ─────────────────────────────────────────────────
def run_once():
    t0 = time.time()
    topic, rows = read_next_topic(TOPICS_CSV)
    if not topic:
        logging.info("No pending topics. Add rows to content/topics.csv with status=todo.")
        return

    tid   = topic.get("id", "")
    title = (topic.get("title") or "").strip()
    desc  = (topic.get("description") or "").strip()

    if not title:
        logging.error("Topic row missing title. id=%s", tid)
        return

    logging.info("🎬 Starting pipeline for: %s", title)
    try:
        # 1) Script
        script_text = generate_script(title, desc)
        logging.info("🧠 Script OK (%d chars)", len(script_text))

        # 2) TTS
        voice_path = tts_elevenlabs(script_text, title)
        logging.info("🎙️  Voice OK: %s", voice_path.name)

        # 3) Compose video
        out_mp4 = build_video(title, voice_path)
        elapsed = time.time() - t0
        logging.info("✅ Done in %.1fs -> %s", elapsed, out_mp4)

        # mark done in CSV
        mark_done(tid, rows, success=True)
    except Exception as e:
        logging.exception("❌ Pipeline failed: %s", e)
        mark_done(tid, rows, success=False, error_msg=str(e))

def fetch_pexels_videos(title: str, duration: float) -> list:
    """
    Fetch real videos from Pexels API based on topic
    """
    pexels_key = os.getenv("PEXELS_API_KEY")
    if not pexels_key or pexels_key == "your_pexels_api_key_here":
        logging.info("No Pexels API key - skipping video fetch")
        return []
    
    # Extract search keywords from title
    search_terms = []
    title_lower = title.lower()
    
    # Mythology-specific keywords
    if "golden fleece" in title_lower:
        search_terms = ["epic adventure", "ocean waves", "ancient ship", "hero journey"]
    elif "orpheus" in title_lower:
        search_terms = ["mystical forest", "underworld", "ancient music", "dark cave"]
    elif "hercules" in title_lower:
        search_terms = ["strength", "ancient warrior", "epic battle", "temple"]
    elif "trojan" in title_lower:
        search_terms = ["ancient war", "burning city", "epic battle", "wooden horse"]
    elif "medusa" in title_lower:
        search_terms = ["snake", "ancient temple", "stone statue", "mythology"]
    elif "icarus" in title_lower:
        search_terms = ["flying", "sun", "wings", "falling"]
    elif "pandora" in title_lower:
        search_terms = ["ancient box", "mystical light", "opening", "magic"]
    else:
        # Generic mythology terms
        search_terms = ["ancient", "mythology", "epic", "temple", "fire", "storm"]
    
    video_clips = []
    videos_dir = ASSETS_DIR / "videos" / safe_slug(title)
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    for search_term in search_terms[:2]:  # Try 2 terms
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {"Authorization": pexels_key}
            params = {
                "query": search_term,
                "per_page": 2,
                "orientation": "portrait",
                "size": "medium"
            }
            
            logging.info(f"🎬 Searching Pexels for: {search_term}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for video in data.get("videos", []):
                    if len(video_clips) >= 3:  # Max 3 videos
                        break
                        
                    video_files = video.get("video_files", [])
                    # Find best quality video file
                    best_file = None
                    for file in video_files:
                        if file.get("height", 0) >= 720 and file.get("height", 0) <= 1920:
                            best_file = file
                            break
                    
                    if best_file:
                        video_path = videos_dir / f"pexels_{video['id']}.mp4"
                        
                        if not video_path.exists():
                            # Download video
                            logging.info(f"📥 Downloading video: {video['id']}")
                            video_response = requests.get(best_file["link"], timeout=60)
                            if video_response.status_code == 200:
                                video_path.write_bytes(video_response.content)
                                logging.info(f"✅ Downloaded: {video_path.name}")
                        
                        if video_path.exists():
                            try:
                                clip = VideoFileClip(str(video_path)).resize(FRAME_SIZE)
                                # Limit clip duration
                                clip_duration = min(clip.duration, duration / 3)
                                clip = clip.set_duration(clip_duration)
                                clip = clip.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5)
                                video_clips.append(clip)
                                logging.info(f"🎥 Added video clip: {clip_duration:.1f}s")
                            except Exception as e:
                                logging.warning(f"Error processing video {video_path}: {e}")
            
            elif response.status_code == 401:
                logging.error("Pexels API key invalid or expired")
                break
            else:
                logging.warning(f"Pexels API error: {response.status_code}")
                
        except Exception as e:
            logging.warning(f"Error fetching videos for '{search_term}': {e}")
        
        if len(video_clips) >= 3:
            break
    
    return video_clips

def create_video_from_images(image_files: list, duration: float, title: str) -> list:
    """
    Create video clips from curated images with Ken Burns effect.
    Each image gets 2-3 seconds with smooth zoom and pan.
    """
    video_clips = []
    images_per_video = max(3, min(len(image_files), int(duration / 2.5)))  # 2.5 seconds per image
    time_per_image = duration / images_per_video
    
    logging.info(f"🖼️  Creating video from {images_per_video} images, {time_per_image:.1f}s each")
    
    for i, image_file in enumerate(image_files[:images_per_video]):
        try:
            # Create image clip
            clip = ImageClip(str(image_file), duration=time_per_image)
            clip = clip.resize(FRAME_SIZE)
            
            # Add Ken Burns effect (slow zoom and pan)
            zoom_factor = 1.0 + (ZOOM_FACTOR * (i % 2))  # Alternate zoom in/out
            clip = clip.resize(zoom_factor).set_position('center')
            
            # Add fade transitions
            clip = clip.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5)
            
            video_clips.append(clip)
            logging.info(f"  ✅ Added image {i+1}: {image_file.name}")
            
        except Exception as e:
            logging.warning(f"Error processing image {image_file}: {e}")
            continue
    
    return video_clips

if __name__ == "__main__":
    run_once()
