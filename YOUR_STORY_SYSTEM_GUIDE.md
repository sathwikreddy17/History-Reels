# 🎯 **YOUR COMPLETE STORY-TO-REEL SYSTEM**

## ✅ **Perfect! You Now Have Full Control**

This system lets you:
1. **Write/paste your own stories** 
2. **Add your own curated images**
3. **Get professional Instagram Reels** automatically

---

## 📁 **Where to Put Your Content**

### **1. Your Stories** 📝
**Location:** `input/stories/`

**Format:** Create a `.txt` file with your reel name:
```
input/stories/Ganga_Divine_Sacrifice.txt
input/stories/Perseus_Hero_Journey.txt
input/stories/Shiva_Cosmic_Dance.txt
```

**Content:** Paste your complete story (any length). The AI will convert it into a perfect 60-second Instagram script.

### **2. Your Images** 🖼️
**Location:** `input/images/`

**Format:** Create a folder with the SAME name as your story:
```
input/images/Ganga_Divine_Sacrifice/
├── goddess_ganga.jpg
├── sacred_river.jpg
├── lord_shiva.jpg
└── heavenly_realm.jpg

input/images/Perseus_Hero_Journey/
├── perseus_hero.jpg
├── medusa_head.jpg
├── greek_temple.jpg
└── divine_sword.jpg
```

---

## 🚀 **How to Create a Reel**

### **Step 1: Add Your Story**
Create a text file in `input/stories/` with your reel name:

**Example:** `input/stories/Krishna_Butter_Thief.txt`
```
Paste your complete story here...
Krishna was a mischievous child who loved butter...
[Your full story - any length]
```

### **Step 2: Add Your Images**
Create a folder with the SAME name in `input/images/`:

**Example:** `input/images/Krishna_Butter_Thief/`
```
Add 3-8 relevant images:
- baby_krishna.jpg
- butter_pot.jpg
- village_scene.jpg
- divine_child.jpg
```

### **Step 3: Run the Processor**
```bash
cd myth-factory
source myth-factory-env/bin/activate
python process_stories.py
```

### **Step 4: Get Your Video!**
The system will:
- ✅ Convert your story into perfect 60-second script
- ✅ Generate professional AI voiceover
- ✅ Create video with your images (Ken Burns effects)
- ✅ Add background music
- ✅ Save to `renders/2025-11/` folder

---

## 🎬 **What Happens Automatically**

### **AI Script Generation:**
- Takes your full story (any length)
- Creates engaging 60-second Instagram script
- Perfect for modern social media audience
- Hooks viewers in first 5 seconds
- Dramatic storytelling with visual descriptions

### **Professional Production:**
- AI voiceover with perfect timing
- Your images with cinematic effects (zoom, pan, fade)
- Background music mixing
- 1080x1920 Instagram Reel format
- Automatic thumbnail generation

---

## 📋 **File Naming Guide**

**Story Name Rules:**
- Use underscores instead of spaces
- Keep it descriptive but concise
- Same name for story file and image folder

**Examples:**
```
✅ Good:
- Krishna_Butter_Thief.txt
- Ganga_Divine_Sacrifice.txt
- Hanuman_Mountain_Lift.txt

❌ Avoid:
- story 1.txt (spaces)
- verylongstorynamethatistoohardtoread.txt (too long)
- story.txt (not descriptive)
```

---

## 🖼️ **Image Guidelines**

### **How Many Images:**
- **3-5 images** = Perfect for 60 seconds
- **6-8 images** = Maximum (each gets shorter duration)

### **Image Quality:**
- **High resolution** (minimum 1080px wide)
- **Clear and detailed** for zoom effects
- **JPG, PNG, WEBP** formats supported

### **Content Suggestions:**
- Main character/deity images
- Symbolic objects (weapons, artifacts)
- Location/setting scenes (temples, forests)
- Action moments from the story
- Divine/mystical elements

---

## 🔄 **Processing System**

The system automatically:

1. **Scans** for new story files
2. **Checks** if video already exists (skips if done)
3. **Processes** only new/pending stories
4. **Creates** professional Instagram Reels
5. **Logs** everything for debugging

---

## 📂 **Complete File Structure**

```
myth-factory/
├── process_stories.py          # NEW: Your main processor
├── input/                      # NEW: Your content folder
│   ├── stories/               # Your story text files
│   │   ├── Story_Name_1.txt
│   │   └── Story_Name_2.txt
│   └── images/                # Your image folders
│       ├── Story_Name_1/
│       │   ├── image1.jpg
│       │   └── image2.jpg
│       └── Story_Name_2/
│           ├── image1.jpg
│           └── image2.jpg
├── content/                   # Generated content
│   ├── scripts/              # AI-generated scripts
│   └── voiceovers/           # AI-generated audio
├── renders/                  # Your final videos
│   └── 2025-11/
│       ├── 2025-11-01_Story_Name_1_v1.mp4
│       └── 2025-11-01_Story_Name_1_v1_thumb.png
└── assets/
    └── music/                # Background music
```

---

## 🎯 **Quick Start Example**

### **Create Your First Reel:**

1. **Add story:** `input/stories/Vishnu_Avatar.txt`
   ```
   Lord Vishnu, the preserver of the universe, incarnates on Earth whenever dharma is threatened. In the ancient age of Treta Yuga, the demon king Ravana had grown so powerful that even the gods feared him...
   [Your complete story]
   ```

2. **Add images:** `input/images/Vishnu_Avatar/`
   ```
   - lord_vishnu.jpg
   - divine_conch.jpg
   - cosmic_wheel.jpg
   - blue_deity.jpg
   ```

3. **Run processor:**
   ```bash
   python process_stories.py
   ```

4. **Get your video:**
   ```
   renders/2025-11/2025-11-01_Vishnu_Avatar_v1.mp4
   ```

---

## ✨ **Benefits of This System**

- ✅ **Full Control** - You choose stories and images
- ✅ **Professional Quality** - AI script optimization
- ✅ **Authentic Content** - Your curated mythology images
- ✅ **Perfect Timing** - 60-second Instagram format
- ✅ **Batch Processing** - Handle multiple stories at once
- ✅ **No Manual Work** - Automatic video generation

**🎬 You now have a professional mythology content factory! 🏛️✨**
