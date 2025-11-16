# Flask Web UI for Structured JSON Generation

Beautiful dark blue and gold themed web interface for generating structured JSON from 3D object renderings using Claude API.

## Features

- 🎨 Dark blue and gold themed UI
- 📝 Configure all script parameters through web interface
- 📁 Browse and preview folders with rendered images
- 🖼️ View images from folders before processing
- ⚡ Real-time progress tracking
- 📊 View generated JSON outputs
- 🔄 Resume capability (skips already processed folders)
- 📋 Template editor (file-based or inline JSON)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Start the web server:**

```bash
python app.py
```

2. **Open your browser:**

Navigate to: `http://localhost:5000`

3. **Configure and run:**
   - Enter your Claude API key
   - Set parent directory (default: `./example_material`)
   - Choose model and parameters
   - Select or paste JSON template
   - Click "Run Generation"

## Usage Guide

### Configuration Panel (Left Side)

**Required Fields:**
- **Claude API Key**: Your Anthropic API key (required)
- **Parent Directory**: Path to folder containing `Cap3D_imgs/` subdirectory

**Model Settings:**
- **Model**: Choose Claude model (3.5 Sonnet recommended)
- **Number of Views**: How many images to send (1-28)
- **Max Tokens**: Maximum response length (512-8192)
- **Rate Limit Delay**: Seconds between API calls to avoid throttling

**Options:**
- **Use DiffuRank Scores**: Automatically select best views if scores available
- **Overwrite Existing Outputs**: Reprocess folders that already have outputs

**JSON Template:**
- **Use Template File**: Select from available .json templates
- **Inline JSON**: Paste custom JSON structure directly
- **Preview**: View template before running

### Results Panel (Right Side)

**Folders Tab:**
- Click "Refresh Folders" to load available folders
- Green border = already processed (has output)
- Shows number of images per folder
- Click processed folders to view results

**Progress Tab:**
- Real-time output from the running script
- Color-coded messages (green=success, red=error)
- Auto-scrolls to latest output
- Stop button to cancel processing

**Results Viewer Tab:**
- Displays images from selected folder
- Shows generated JSON output
- Syntax-highlighted JSON display
- Auto-loads when clicking processed folder

## File Structure

```
spatial-intelligence/
├── app.py                          # Flask application
├── captioning_claude_structured.py # Backend script
├── example_template.json           # Default template
├── templates/
│   └── index.html                 # Main UI template
├── static/
│   ├── css/
│   │   └── style.css              # Dark blue/gold styling
│   └── js/
│       └── app.js                 # Frontend logic
└── example_material/
    └── Cap3D_imgs/                # Your 3D object folders
        └── {uid}/
            ├── 00000.png
            ├── 00001.png
            └── ...
```

## API Endpoints

- `GET /` - Main UI page
- `GET /api/templates` - List available template files
- `GET /api/template/<filename>` - Get template content
- `POST /api/folders` - List folders in parent_dir
- `GET /api/images/<path>` - Get images from folder
- `GET /api/output/<path>` - Get generated JSON output
- `POST /api/run` - Start processing script
- `GET /api/progress` - Server-sent events for progress
- `POST /api/stop` - Stop running script

## Example Workflow

1. **Prepare Data**: Place rendered images in `parent_dir/Cap3D_imgs/{uid}/`
2. **Start Server**: Run `python app.py`
3. **Configure**: Enter API key and set parameters
4. **Choose Template**: Select template file or paste custom JSON
5. **Preview**: Click "Refresh Folders" to see available data
6. **Run**: Click "Run Generation" and monitor progress
7. **View Results**: Click processed folders to view outputs

## Tips

- **API Keys**: Store in environment variable for security
- **Rate Limiting**: Increase delay if hitting API limits
- **Templates**: Create multiple templates for different use cases
- **Batch Processing**: The script automatically processes all folders
- **Resume**: Rerun anytime - skips already processed folders (unless overwrite enabled)

## Customization

### Colors

Edit `static/css/style.css` to change color scheme:
```css
:root {
    --dark-blue: #0a1929;
    --gold: #ffd700;
    /* ... */
}
```

### Port

Change port in `app.py`:
```python
app.run(debug=True, port=5000)  # Change 5000 to your port
```

## Troubleshooting

**Images not loading:**
- Check parent_dir path is correct
- Ensure Cap3D_imgs/ subfolder exists
- Verify .png files exist in folder

**Script not running:**
- Check API key is valid
- Verify Python packages installed
- Check console for error messages

**No progress updates:**
- Check browser console for errors
- Try refreshing page
- Ensure EventSource supported by browser

## Security Notes

- Don't commit API keys to version control
- Run behind reverse proxy in production
- Use HTTPS in production
- Add authentication for public deployment

