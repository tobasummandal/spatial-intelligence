# Quick Start Guide

Get up and running in 3 steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**For 3D file upload feature, also install Blender:**
- macOS: `brew install blender` or download from [blender.org](https://www.blender.org/download/)
- Linux: `sudo apt install blender`
- Windows: Download from [blender.org](https://www.blender.org/download/)

## Step 2: Start the Web UI

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

## Step 3: Open Browser

Navigate to: **http://localhost:5000**

## What You'll See

A beautiful dark blue and gold interface with:
- **Left Panel**: Configuration options
- **Right Panel**: Folders, Progress, and Results viewer

## First Run

### Option 1: Upload a 3D File (New! ✨)

1. **Upload File**: Drag & drop your .obj, .glb, or other 3D file
2. **Enter API Key**: Paste your Claude API key (from console.anthropic.com)
3. **Choose Template**: Use `example_template.json` or create your own
4. **Click "Start Processing"**: File will be rendered and processed automatically!

### Option 2: Process Existing Renders

1. **Select "Process Existing Renders"** radio button
2. **Enter API Key**: Paste your Claude API key
3. **Set Directory**: Point to folder with Cap3D_imgs/
4. **Click "Start Processing"**: Process pre-rendered images

## Example Template

The included `example_template.json` generates structured JSON with:
- Image summary
- Object detection with bounding boxes
- Spatial relationships
- Room layout analysis
- Enhanced insights

Edit this file or create your own to customize the output structure!

## View Results

1. Go to **Folders** tab
2. Click **Refresh Folders**
3. Click any processed folder (green border) to view:
   - Rendered images
   - Generated JSON output

## Need Help?

Check `WEB_UI_README.md` for detailed documentation.

---

**Happy generating! 🚀**

