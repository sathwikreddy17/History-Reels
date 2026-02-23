# How to add content to the pipeline

## Topic files  →  `input/topics/`

Create one `.txt` file per video. Filename becomes the video slug.

**Format:**
```
Title: Your Human-Readable Title Here
---
Your raw content goes here. This can be:
- A story you wrote
- Bullet point notes
- A Wikipedia summary you copied
- Research notes
- Anything — the AI will turn it into a 60-second script
```

The `Title:` line is optional. If you skip it, the filename is used as the title.

**Example files:**
- `The_Fall_of_the_Berlin_Wall.txt`
- `Marie_Curie.txt`
- `How_Black_Holes_Form.txt`
- `The_Invention_of_Money.txt`

---

## Image folders  →  `input/images/<slug>/`

Create a sub-folder with the **exact same slug** as your topic file (without `.txt`).
Drop your images inside. Supported formats: JPG, JPEG, PNG, WEBP.

Images are displayed in **alphabetical filename order**, so you can control
the sequence by prefixing filenames with numbers:

```
input/images/The_Fall_of_the_Berlin_Wall/
    01_wall_construction_1961.jpg
    02_checkpoint_charlie.jpg
    03_crowds_at_the_gate.jpg
    04_wall_coming_down.jpg
    05_reunification.jpg
```

**Tips:**
- Aim for 4–8 images per 60-second video (7–15 seconds per image)
- Portrait/square images work best for 9:16 format — the pipeline will
  cover-crop landscape images automatically (no letterboxing)
- Higher resolution is better; 1080px+ recommended

---

## Running the pipeline

```bash
# Activate the environment first
source myth-factory-env/bin/activate

# Process all pending topics (topics without a rendered video this month)
python pipeline.py

# Process a single specific topic
python pipeline.py --topic The_Fall_of_the_Berlin_Wall

# Re-run with an existing script (skip the LLM call)
python pipeline.py --topic The_Fall_of_the_Berlin_Wall --skip-script

# Re-run with existing script AND existing voiceover (only re-render video)
python pipeline.py --topic The_Fall_of_the_Berlin_Wall --skip-script --skip-voice

# Disable captions for this run
python pipeline.py --no-captions

# All flags combined
python pipeline.py --topic The_Fall_of_the_Berlin_Wall --skip-voice --no-title-card
```

## Output

Videos are saved to `renders/YYYY-MM/` with thumbnails.
