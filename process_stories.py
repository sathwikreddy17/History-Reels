"""
History Reels - AI-Powered Instagram Reels Generator
====================================================

Transforms user-provided stories into professional Instagram Reels using:
- OpenAI GPT-4o-mini for script generation
- ElevenLabs TTS for voiceover
- MoviePy for video processing with Ken Burns effects

Author: AI Assistant
Last Updated: November 1, 2025
Version: 2.0 (User-Controlled Stories)
"""

import os
import time
import logging
import datetime as dt
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

# MoviePy components
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
# CONFIGURATION & SETUP
# ──────────────────────────────────────────────────────────────────────────────

# Base paths and environment
BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

# Initialize OpenAI client
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in .env")
except Exception as e:
    logging.error(f"OpenAI initialization failed: {e}")
    openai_client = None

# ElevenLabs configuration
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
ELEVEN_MODEL = os.getenv("ELEVEN_MODEL", "eleven_multilingual_v2")

if not ELEVEN_API_KEY:
    logging.error("ELEVEN_API_KEY not found in .env")

# Video processing constants
OUTPUT_RESOLUTION = os.getenv("OUTPUT_RESOLUTION", "1080x1920")
TARGET_DURATION = int(os.getenv("TARGET_DURATION", "60"))
SCRIPT_WORD_COUNT = os.getenv("SCRIPT_WORD_COUNT", "130-160")
FPS = 24
VOICE_GAIN = 1.0
MUSIC_GAIN = 0.3

# Directory structure
INPUT_DIR = BASE / "input"
STORIES_DIR = INPUT_DIR / "stories"
INPUT_IMAGES_DIR = INPUT_DIR / "images"

ASSETS_DIR = BASE / "assets"
MUSIC_DIR = ASSETS_DIR / "music"

CONTENT_DIR = BASE / "content"
SCRIPTS_DIR = CONTENT_DIR / "scripts"
VOICEOVERS_DIR = CONTENT_DIR / "voiceovers"

RENDERS_ROOT = BASE / "renders"
LOGS_DIR = BASE / "logs"

# Ensure required directories exist
for directory in [INPUT_DIR, STORIES_DIR, INPUT_IMAGES_DIR, CONTENT_DIR, SCRIPTS_DIR, VOICEOVERS_DIR, RENDERS_ROOT, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configure logging
LOG_FILE = LOGS_DIR / "run.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# Video processing settings
FRAME_SIZE = (1080, 1920)  # Instagram Reels format (9:16)
MUSIC_GAIN = 0.15
ZOOM_FACTOR = 0.04

# ──────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def validate_environment() -> bool:
    """Validate that all required environment variables and dependencies are present."""
    missing = []
    
    if not openai_client:
        missing.append("OpenAI API key or client")
    if not ELEVEN_API_KEY:
        missing.append("ElevenLabs API key")
    
    if missing:
        logging.error(f"❌ Missing required configuration: {', '.join(missing)}")
        return False
    
    logging.info("✅ Environment validation passed")
    return True

def safe_slug(s: str) -> str:
    """Create a safe filename from string."""
    return "".join(c for c in s.replace(" ", "_") if c.isalnum() or c in ("_", "-", "."))[:120]

def month_render_dir():
    now = dt.datetime.now()
    d = RENDERS_ROOT / f"{now.year:04d}-{now.month:02d}"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_pending_stories() -> List[Path]:
    """Get list of story files that need processing."""
    if not STORIES_DIR.exists():
        logging.warning(f"📁 Stories directory not found: {STORIES_DIR}")
        return []
    
    # Get both .txt and .docx files
    story_files = []
    story_files.extend(list(STORIES_DIR.glob("*.txt")))
    story_files.extend(list(STORIES_DIR.glob("*.docx")))
    
    if not story_files:
        logging.warning("📄 No story files found in stories directory")
        return []
    
    pending = []
    for story_file in story_files:
        # Skip example files
        if "Ganga_Divine_Sacrifice" in story_file.name:
            continue
            
        story_name = story_file.stem
        render_dir = month_render_dir()
        existing_videos = list(render_dir.glob(f"*{story_name}*.mp4"))
        
        if not existing_videos:
            pending.append(story_file)
        else:
            logging.info(f"⏭️  Skipping {story_name} (already processed)")
    
    return pending

def create_script_from_story(story_content: str, story_name: str) -> str:
    """Convert full story into 60-second Instagram Reel script"""
    
    prompt = f"""
You are a master storyteller creating engaging 60-second Instagram Reels about ancient history and cultural stories.

Convert this story into a captivating 60-second script for an Instagram Reel:

STORY:
{story_content}

REQUIREMENTS:
- Must be exactly 130-160 words (for 60-second duration)
- Hook viewers in first 5 seconds with dramatic opening
- Use vivid, cinematic language
- Include emotional moments and visual imagery
- End with powerful message or lesson
- Write for voiceover narration (no text overlays needed)
- Make it engaging for modern social media audience
- Focus on the most dramatic and visually compelling parts

STYLE:
- Dramatic, storytelling tone
- Present tense for immediacy
- Short, punchy sentences
- Emotional peaks and valleys
- Visual descriptions that work with images

Create a script that will captivate viewers and make them feel the power of this ancient story:
"""

    if not openai_client:
        raise RuntimeError("Missing OpenAI client. Check OPENAI_API_KEY in .env")
    
    logging.info("🧠 Creating Instagram Reel script from your story...")
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=400
    )
    
    script = resp.choices[0].message.content.strip()
    
    # Save the script
    script_path = SCRIPTS_DIR / f"{safe_slug(story_name)}.txt"
    script_path.write_text(script, encoding="utf-8")
    logging.info(f"📝 Script saved: {script_path}")
    
    return script

def create_voiceover(script: str, story_name: str) -> Path:
    """Generate AI voiceover using ElevenLabs"""
    
    if not ELEVEN_API_KEY:
        raise RuntimeError("Missing ELEVEN_API_KEY in .env")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.8,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }
    
    logging.info("🎙️  Generating AI voiceover...")
    response = requests.post(url, headers=headers, json=data, timeout=30)
    
    if response.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error: {response.status_code} - {response.text}")
    
    # Save voiceover
    voiceover_path = VOICEOVERS_DIR / f"{safe_slug(story_name)}.mp3"
    voiceover_path.write_bytes(response.content)
    logging.info(f"🎵 Voiceover saved: {voiceover_path}")
    
    return voiceover_path

def create_video_from_images(story_name: str, duration: float) -> list:
    """Create video clips from your curated images"""
    
    images_dir = None
    
    # Method 1: Check all existing folders in images directory
    if INPUT_IMAGES_DIR.exists():
        for folder in INPUT_IMAGES_DIR.iterdir():
            if folder.is_dir() and folder.name != ".DS_Store":
                # Check if this folder could be for our story
                folder_name_clean = folder.name.lower().replace(" ", "").replace("–", "").replace("-", "").replace("_", "")
                story_name_clean = story_name.lower().replace(" ", "").replace("–", "").replace("-", "").replace("_", "")
                
                if folder_name_clean == story_name_clean:
                    images_dir = folder
                    break
                    
                # Also check if key words match
                story_words = story_name.lower().replace("_", " ").split()
                folder_words = folder.name.lower().split()
                if len(story_words) >= 3 and len(folder_words) >= 3:
                    matches = sum(1 for word in story_words[:5] if word in folder.name.lower())
                    if matches >= 3:  # At least 3 key words match
                        images_dir = folder
                        break
    
    if not images_dir:
        logging.warning(f"No images directory found for: {story_name}")
        logging.info(f"Available image folders:")
        if INPUT_IMAGES_DIR.exists():
            for folder in INPUT_IMAGES_DIR.iterdir():
                if folder.is_dir():
                    logging.info(f"  - {folder.name}")
        return []
    
    # Get all image files
    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        image_files.extend(list(images_dir.glob(ext)))
    
    if not image_files:
        logging.warning(f"No images found in: {images_dir}")
        return []
    
    logging.info(f"🖼️  Found {len(image_files)} images in: {images_dir.name}")
    
    # Calculate timing
    images_to_use = min(len(image_files), 8)  # Max 8 images
    time_per_image = duration / images_to_use
    
    video_clips = []
    
    for i, image_file in enumerate(image_files[:images_to_use]):
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
            logging.info(f"  ✅ Added image {i+1}/{images_to_use}: {image_file.name}")
            
        except Exception as e:
            logging.warning(f"Error processing image {image_file}: {e}")
            continue
    
    return video_clips

def get_background_music() -> AudioFileClip:
    """Get background music for the video"""
    
    music_files = list(MUSIC_DIR.glob("*.mp3"))
    if not music_files:
        logging.warning("No background music found")
        return None
    
    # Use the first available music file
    music_file = music_files[0]
    logging.info(f"🎵 Using background music: {music_file.name}")
    
    return AudioFileClip(str(music_file))

def read_story_content(story_file: Path) -> str:
    """Read story content from .txt or .docx file with proper error handling."""
    
    if story_file.suffix.lower() == '.docx':
        try:
            import docx
            doc = docx.Document(str(story_file))
            content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():  # Skip empty paragraphs
                    content.append(paragraph.text)
            return '\n'.join(content)
        except ImportError:
            logging.warning("📦 python-docx not installed. Please convert .docx to .txt or install python-docx")
            txt_file = story_file.with_suffix('.txt')
            if txt_file.exists():
                return txt_file.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError(f"Cannot read .docx file and no .txt version found: {story_file}")
        except Exception as e:
            logging.warning(f"⚠️  Error reading .docx file: {e}. Trying .txt version...")
            txt_file = story_file.with_suffix('.txt')
            if txt_file.exists():
                return txt_file.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError(f"Cannot read .docx file: {story_file}")
    else:
        # Read .txt file
        return story_file.read_text(encoding="utf-8")
def create_video(story_file: Path):
    """Main function to create video from your story and images"""
    
    story_name = story_file.stem
    logging.info(f"🎬 Starting video creation for: {story_name}")
    
    # 1. Read your story (handles both .txt and .docx)
    story_content = read_story_content(story_file)
    logging.info(f"📖 Read story: {len(story_content)} characters")
    
    # 2. Create Instagram Reel script
    script = create_script_from_story(story_content, story_name)
    logging.info(f"📝 Script created: {len(script.split())} words")
    
    # 3. Generate voiceover
    voiceover_path = create_voiceover(script, story_name)
    
    # 4. Get voiceover duration
    voice_clip = AudioFileClip(str(voiceover_path))
    duration = voice_clip.duration
    logging.info(f"⏱️  Video duration: {duration:.1f} seconds")
    
    # 5. Create video from your images
    video_clips = create_video_from_images(story_name, duration)
    
    if not video_clips:
        raise RuntimeError(f"No video clips created. Please add images to: input/images/{story_name}/")
    
    # 6. Combine video clips
    main_video = concatenate_videoclips(video_clips, method="compose")
    main_video = main_video.set_duration(duration)
    
    # 7. Add background music
    music_clip = get_background_music()
    if music_clip:
        music_clip = music_clip.set_duration(duration)
        music_clip = music_clip.volumex(MUSIC_GAIN)  # Fix: use volumex instead of *
        final_audio = CompositeAudioClip([voice_clip.volumex(VOICE_GAIN), music_clip])
    else:
        final_audio = voice_clip.volumex(VOICE_GAIN)
    
    # 8. Combine video and audio
    final_video = main_video.set_audio(final_audio)
    
    # 9. Render final video
    render_dir = month_render_dir()
    now = dt.datetime.now()
    output_file = render_dir / f"{now.strftime('%Y-%m-%d')}_{story_name}_v1.mp4"
    
    logging.info(f"🎬 Rendering video: {output_file}")
    
    final_video.write_videofile(
        str(output_file),
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True
    )
    
    # Create thumbnail
    thumbnail_path = output_file.with_name(output_file.stem + "_thumb.png")
    final_video.save_frame(str(thumbnail_path), t=duration/2)
    
    logging.info(f"✅ Video created: {output_file}")
    logging.info(f"📸 Thumbnail: {thumbnail_path}")
    
    # Cleanup
    voice_clip.close()
    if music_clip:
        music_clip.close()
    final_video.close()
    
    return output_file

def main():
    """Main function to process all pending stories into Instagram Reels."""
    
    logging.info("🚀 Starting History Reels - AI Instagram Reels Generator")
    
    # Validate environment before starting
    if not validate_environment():
        logging.error("❌ Environment validation failed. Please check your .env file.")
        return
    
    # Get pending stories
    pending_stories = get_pending_stories()
    
    if not pending_stories:
        logging.info("✅ No pending stories found.")
        logging.info("📝 To create a video:")
        logging.info(f"   1. Add your story to: {STORIES_DIR}/your_story_name.txt")
        logging.info(f"   2. Add images to: {INPUT_IMAGES_DIR}/your_story_name/")
        logging.info("   3. Run this script again")
        return
    
    logging.info(f"📚 Found {len(pending_stories)} stories to process")
    
    success_count = 0
    total_start_time = time.time()
    
    for i, story_file in enumerate(pending_stories, 1):
        story_name = story_file.stem
        logging.info(f"\n{'='*50}")
        logging.info(f"📖 Processing story {i}/{len(pending_stories)}: {story_name}")
        logging.info(f"{'='*50}")
        
        try:
            start_time = time.time()
            create_video(story_file)
            duration = time.time() - start_time
            logging.info(f"🎉 SUCCESS: {story_name} (completed in {duration:.1f}s)")
            success_count += 1
        except Exception as e:
            logging.error(f"❌ FAILED: {story_name} - {e}")
            logging.exception("Full error details:")
    
    # Summary
    total_duration = time.time() - total_start_time
    logging.info(f"\n{'='*50}")
    logging.info(f"📊 PROCESSING COMPLETE")
    logging.info(f"{'='*50}")
    logging.info(f"✅ Successful: {success_count}/{len(pending_stories)}")
    logging.info(f"⏱️  Total time: {total_duration:.1f}s")
    if success_count > 0:
        logging.info(f"📁 Videos saved to: {month_render_dir()}")


if __name__ == "__main__":
    main()
