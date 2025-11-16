#!/bin/bash

# Script to render bedroom.obj with both rendering types

echo "=== Rendering bedroom.obj with Cap3D pipeline ==="
echo ""

# Check if Blender exists
if [ ! -d "blender-3.4.1-linux-x64" ] && [ ! -d "blender-3.4.1-macos-x64" ] && [ ! -d "/Applications/Blender.app" ]; then
    echo "⚠️  Blender not found!"
    echo ""
    echo "Please download Blender first:"
    echo "  Option 1 (Recommended): Download Cap3D's Blender package:"
    echo "    wget https://huggingface.co/datasets/tiange/Cap3D/resolve/main/misc/blender.zip"
    echo "    unzip blender.zip"
    echo ""
    echo "  Option 2: Use system Blender (if installed):"
    echo "    brew install --cask blender"
    echo ""
    exit 1
fi

# Detect Blender path
if [ -d "blender-3.4.1-linux-x64" ]; then
    BLENDER="./blender-3.4.1-linux-x64/blender"
elif [ -d "blender-3.4.1-macos-x64" ]; then
    BLENDER="./blender-3.4.1-macos-x64/blender"
elif [ -d "/Applications/Blender.app" ]; then
    BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
else
    BLENDER="blender"  # Try system path
fi

echo "Using Blender: $BLENDER"
echo ""

# Create output directory
mkdir -p bedroom_output

echo "=== Type 1: Rendering 8 horizontal views ==="
$BLENDER -b -P render_script_type1.py -- \
    --object_path_pkl './bedroom_object_path.pkl' \
    --parent_dir './bedroom_output'

echo ""
echo "=== Type 2: Rendering 20 random views ==="
$BLENDER -b -P render_script_type2.py -- \
    --object_path_pkl './bedroom_object_path.pkl' \
    --parent_dir './bedroom_output'

echo ""
echo "✅ Done! Rendered images are in: ./bedroom_output/Cap3D_imgs/bedroom/"
