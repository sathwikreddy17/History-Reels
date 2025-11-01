import requests
import os
from pathlib import Path

def download_sample_videos():
    """
    Download sample videos for immediate testing
    """
    # Free sample videos from various sources
    sample_videos = [
        {
            "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "name": "epic_landscape.mp4",
            "topic": "The_Golden_Fleece"
        },
        {
            "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_640x360_1mb.mp4", 
            "name": "mystical_scene.mp4",
            "topic": "Orpheus_in_the_Underworld"
        }
    ]
    
    base_dir = Path("assets/videos")
    
    for video in sample_videos:
        topic_dir = base_dir / video["topic"]
        topic_dir.mkdir(parents=True, exist_ok=True)
        
        video_path = topic_dir / video["name"]
        
        if not video_path.exists():
            try:
                print(f"Downloading {video['name']}...")
                response = requests.get(video["url"], timeout=30)
                response.raise_for_status()
                
                video_path.write_bytes(response.content)
                print(f"✅ Downloaded: {video_path}")
                
            except Exception as e:
                print(f"❌ Failed to download {video['name']}: {e}")

if __name__ == "__main__":
    download_sample_videos()
