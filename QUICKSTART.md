# Quick Start Guide

Get up and running in 3 steps!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

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

1. **Enter API Key**: Paste your Claude API key (from console.anthropic.com)
2. **Set Directory**: Default is `./example_material` (or change to your data folder)
3. **Choose Template**: Use `example_template.json` or create your own
4. **Click Run**: Watch real-time progress as images are processed!

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

