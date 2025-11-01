# Myth Factory - Quick Start Guide

## 🚀 **Getting Started in 3 Steps**

### **Step 1: Setup (One-time)**
```bash
cd myth-factory
source myth-factory-env/bin/activate  # Activate Python environment
```

### **Step 2: Add Your Content**
1. **Story**: Create `input/stories/Your_Story_Name.txt` with your story content
2. **Images**: Create folder `input/images/Your Story Name/` with 2-8 high-quality images

### **Step 3: Generate Video**
```bash
python process_stories.py
```

**That's it!** Your video will be in `renders/2025-11/YYYY-MM-DD_Your_Story_Name_v1.mp4`

---

## 📁 **Input Folder Structure**

```
input/
├── stories/
│   ├── Epic_of_Gilgamesh.txt           # Your story content
│   ├── Hercules_Twelve_Labors.txt      # Another story
│   └── Perseus_and_Medusa.txt          # Yet another story
└── images/
    ├── Epic of Gilgamesh/              # Flexible naming
    │   ├── image1.jpg                  # High-quality images
    │   ├── image2.png                  # 2-8 images per story
    │   └── image3.webp                 # Various formats supported
    ├── hercules-twelve-labors/         # Dashes work too
    │   ├── hercules1.jpg
    │   └── hercules2.jpg
    └── Perseus and Medusa/             # Exact match preferred
        ├── perseus.jpg
        └── medusa.png
```

---

## ⚙️ **Configuration**

### **Essential Settings (`.env`)**
```properties
# Required APIs
OPENAI_API_KEY=your_openai_key_here
ELEVEN_API_KEY=your_elevenlabs_key_here

# Video Settings (Optional - good defaults provided)
OUTPUT_RESOLUTION=1080x1920
TARGET_DURATION=60
SCRIPT_WORD_COUNT=130-160

# Voice Settings (Optional - good defaults provided)
ELEVEN_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVEN_MODEL=eleven_multilingual_v2
```

---

## 🎯 **Best Practices**

### **For Stories:**
- ✅ Any length (system adapts to 60-second script)
- ✅ Rich, descriptive content works best
- ✅ Mythology, spiritual stories, legends perform well
- ✅ Use `.txt` format (`.docx` supported but requires extra package)

### **For Images:**
- ✅ High resolution (1080p+ recommended)
- ✅ 2-8 images per story (optimal: 4-6 images)
- ✅ Mythology-themed, story-relevant visuals
- ✅ Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`

### **For Naming:**
- ✅ Story file: `"Epic of Gilgamesh.txt"`
- ✅ Image folder: `"Epic of Gilgamesh"` or `"epic-of-gilgamesh"` or `"epic_of_gilgamesh"`
- ✅ System automatically matches variations

---

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **"No images found"**
   ```
   Solution: Check folder name matches story name
   The system logs will show available image folders
   ```

2. **"OpenAI API Error"**
   ```
   Solution: Verify OPENAI_API_KEY in .env file
   Check your OpenAI account credits
   ```

3. **"ElevenLabs Error"**
   ```
   Solution: Verify ELEVEN_API_KEY in .env file
   Check your ElevenLabs account status
   ```

4. **"Import Error" (python-docx)**
   ```
   Solution: Either convert .docx to .txt, or install:
   pip install python-docx
   ```

### **Getting Help:**
- ✅ Check the logs in `logs/run.log` for detailed error information
- ✅ System provides helpful guidance in console output
- ✅ All processing steps are logged with emojis for easy reading

---

## 📊 **What Happens During Processing**

1. **📖 Story Analysis**: AI reads your story and creates engaging 60-second script
2. **🎙️ Voiceover Generation**: Professional AI voice narrates the script
3. **🖼️ Image Processing**: Ken Burns effects applied to your images
4. **🎵 Audio Mixing**: Background music blended with narration
5. **🎬 Video Rendering**: Final 1080x1920 Instagram Reel created
6. **💾 File Saving**: Video saved with timestamp and story name

---

## 🎯 **Expected Output Quality**

- **Format**: MP4, 1080x1920 (Instagram Reels)
- **Duration**: ~60 seconds (varies with story content)
- **Audio**: Professional voiceover + background music
- **Video**: Cinematic Ken Burns effects on your images
- **File Size**: 50-100MB (optimized for upload)
- **Processing Time**: 1-2 minutes per video

---

## 🚀 **Tips for Best Results**

1. **Use high-quality, mythology-themed images**
2. **Write rich, descriptive stories with visual elements**
3. **Keep one story per processing run (clean input folders)**
4. **Use consistent naming between story file and image folder**
5. **Check the logs for any warnings or suggestions**

---

*Ready to create amazing mythology reels? Just add your story and images, then run the script!*
