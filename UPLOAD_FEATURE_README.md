# 3D File Upload Feature

The web UI now supports **direct 3D file upload** with automatic rendering and processing!

## Workflow

### Upload & Process (New!)

1. **Upload your 3D file** - Drag & drop or click to browse
2. **Configure settings** - API key, model, template
3. **Click "Start Processing"** - Everything happens automatically:
   - ✅ File upload
   - ✅ Blender rendering (28 views from 2 different camera setups)
   - ✅ Claude API processing with your template
   - ✅ Display results
   - ✅ Auto-cleanup of temporary files

### Process Existing Renders (Original)

If you already have rendered images, use the "Process Existing Renders" option to run Claude processing on existing folders.

## Supported 3D File Formats

The UI supports **ALL major 3D formats**:

- `.obj` - Wavefront OBJ
- `.glb` / `.gltf` - GL Transmission Format
- `.fbx` - Autodesk FBX
- `.stl` - Stereolithography
- `.ply` - Polygon File Format
- `.dae` - COLLADA
- `.blend` - Blender native
- `.3ds` - 3D Studio
- `.x3d` - X3D

## Requirements

### Blender Installation

The upload feature requires **Blender** to render 3D files into 2D images.

**Option 1: Use bundled Blender (Linux)**
```bash
wget https://huggingface.co/datasets/tiange/Cap3D/resolve/main/misc/blender.zip
unzip blender.zip
```

**Option 2: Install Blender system-wide**

- **macOS**: Download from [blender.org](https://www.blender.org/download/) or `brew install blender`
- **Linux**: `sudo apt install blender` or download from blender.org
- **Windows**: Download installer from blender.org

The app will automatically detect Blender in these locations:
- `./blender-3.4.1-linux-x64/blender` (bundled)
- `blender` (system PATH)
- `/Applications/Blender.app/Contents/MacOS/Blender` (macOS)
- `C:\Program Files\Blender Foundation\Blender\blender.exe` (Windows)

## How It Works

### 1. Upload
- Drag & drop or click to select your 3D file
- File is uploaded to a temporary directory
- Validation checks file format

### 2. Rendering
- **Type 1**: 8 horizontal views around the object
- **Type 2**: 20 random camera angles
- Total: 28 rendered PNG images at 512x512 resolution
- Includes camera matrices, depth maps, and material info

### 3. Processing
- Rendered images are sent to Claude API
- Claude analyzes the 3D object from multiple angles
- Generates structured JSON based on your template
- Returns: images + JSON output

### 4. Cleanup
- Results are displayed in the Results Viewer
- Temporary files are automatically deleted
- Only the JSON output is retained in memory

## Usage Example

```
1. Start the server:
   python app.py

2. Open browser:
   http://localhost:5000

3. Upload a .obj file of a chair

4. Results appear showing:
   - 28 rendered views of the chair
   - Structured JSON with:
     * Object labels
     * Bounding boxes
     * Spatial relationships
     * Material properties
     * etc.
```

## Configuration

All standard settings apply:
- **Claude API Key**: Required for processing
- **Model**: Choose Claude 3.5 Sonnet, Opus, or Sonnet
- **Number of Views**: How many images to send to Claude (default: 6 best views)
- **Template**: Define your JSON structure
- **Use DiffuRank**: Auto-select best views (if scores available)

## File Size Limits

- **Maximum file size**: 500MB
- Typical 3D models: 1-50MB
- Large scenes with textures: 50-200MB

If you need larger files, edit `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1GB
```

## Tips

### For Best Results
1. **Clean models**: Remove unnecessary complexity
2. **Proper scale**: Objects should be reasonably sized
3. **Good topology**: Clean mesh geometry renders better
4. **Materials**: Include materials for better visualization

### Troubleshooting

**"Blender not found" error:**
- Install Blender or set correct path in `app.py`
- Make sure Blender is accessible from command line

**Rendering fails:**
- Check 3D file is valid (open in Blender first)
- Check file isn't corrupted
- Try simpler geometry

**Upload fails:**
- Check file size < 500MB
- Verify file format is supported
- Check browser console for errors

**Slow processing:**
- Large files take longer to upload
- Rendering 28 views takes 1-5 minutes
- Claude processing depends on API speed

## Architecture

```
User uploads file.obj
    ↓
Temporary directory created
    ↓
File saved to temp location
    ↓
Blender renders 28 views
    ↓
Claude processes images
    ↓
Results returned to browser
    ↓
Temp directory cleaned up
```

## Security Notes

- Files are stored in temporary directories only
- Each upload gets a unique temp directory
- Auto-cleanup prevents disk space issues
- No files are permanently stored
- API keys are never logged or saved

## Performance

**Typical timing for a 10MB .obj file:**
- Upload: 2-5 seconds
- Rendering: 1-3 minutes (28 views)
- Claude processing: 10-30 seconds
- **Total: 2-4 minutes**

Larger files or complex scenes will take longer.

## Next Steps

After upload and processing:
1. View rendered images in Results Viewer
2. Inspect generated JSON
3. Copy JSON for use in your application
4. Upload another file or clear selection

The temporary files are automatically cleaned up, so you can process multiple files in sequence!

