#!/usr/bin/env python3
"""
Flask Web UI for Structured JSON Generation with Claude API
"""
import os
import sys
import json
import glob
import base64
import tempfile
import shutil
import pickle
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import subprocess
import threading
import queue
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'spatial-intelligence-key'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Supported 3D file formats
ALLOWED_EXTENSIONS = {'.obj', '.glb', '.gltf', '.fbx', '.stl', '.ply', '.dae', '.blend', '.3ds', '.x3d'}

# Global progress tracking
progress_queue = queue.Queue()
current_process = None
temp_dirs = []  # Track temp directories for cleanup


def allowed_file(filename):
    """Check if file has an allowed extension"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List available template files"""
    templates = []
    for file in glob.glob('*.json'):
        if 'template' in file.lower():
            templates.append(file)
    return jsonify(templates)


@app.route('/api/template/<filename>', methods=['GET'])
def get_template(filename):
    """Get template file content"""
    try:
        with open(filename, 'r') as f:
            content = json.load(f)
        return jsonify(content)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/folders', methods=['POST'])
def list_folders():
    """List folders in parent_dir/Cap3D_imgs/"""
    parent_dir = request.json.get('parent_dir', './example_material')
    imgs_dir = os.path.join(parent_dir, 'Cap3D_imgs')
    
    if not os.path.exists(imgs_dir):
        return jsonify({'error': f'{imgs_dir} does not exist'}), 400
    
    folders = []
    for folder in glob.glob(os.path.join(imgs_dir, '*')):
        if os.path.isdir(folder):
            uid = os.path.basename(folder)
            images = glob.glob(os.path.join(folder, '*.png'))
            has_output = os.path.exists(os.path.join(folder, 'structured_output.json'))
            folders.append({
                'uid': uid,
                'path': folder,
                'num_images': len(images),
                'has_output': has_output
            })
    
    return jsonify(folders)


@app.route('/api/images/<path:folder_path>', methods=['GET'])
def get_images(folder_path):
    """Get list of images from a folder"""
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    
    images = []
    for img_file in sorted(glob.glob(os.path.join(folder_path, '*.png')))[:10]:  # Limit to 10 for preview
        img_name = os.path.basename(img_file)
        with open(img_file, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        images.append({
            'name': img_name,
            'data': f'data:image/png;base64,{img_data}'
        })
    
    return jsonify(images)


@app.route('/api/output/<path:folder_path>', methods=['GET'])
def get_output(folder_path):
    """Get structured output JSON from a folder"""
    output_file = os.path.join(folder_path, 'structured_output.json')
    
    if not os.path.exists(output_file):
        return jsonify({'error': 'Output not found'}), 404
    
    try:
        with open(output_file, 'r') as f:
            output = json.load(f)
        return jsonify(output)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/run', methods=['POST'])
def run_script():
    """Run the captioning script"""
    global current_process
    
    data = request.json
    
    # Validate required fields
    if not data.get('api_key'):
        return jsonify({'error': 'API key is required'}), 400
    
    # Build command
    python_cmd = sys.executable
    cmd = [
        python_cmd, 'captioning_claude_structured.py',
        '--api_key', data['api_key'],
        '--parent_dir', data.get('parent_dir', './example_material'),
        '--model', data.get('model', 'claude-3-5-sonnet-20241022'),
        '--num_views', str(data.get('num_views', 6)),
        '--max_tokens', str(data.get('max_tokens', 4096)),
        '--rate_limit_delay', str(data.get('rate_limit_delay', 1.0))
    ]
    
    # Add template
    if data.get('use_inline_template') and data.get('inline_template'):
        cmd.extend(['--template_json', json.dumps(data['inline_template'])])
    else:
        cmd.extend(['--template_file', data.get('template_file', './example_template.json')])
    
    # Add flags
    if data.get('overwrite'):
        cmd.append('--overwrite')
    
    if not data.get('use_diffurank', True):
        cmd.append('--no_diffurank')
    
    # Run in thread
    def run_process():
        global current_process
        try:
            current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in current_process.stdout:
                progress_queue.put({'type': 'output', 'data': line.strip()})
            
            current_process.wait()
            progress_queue.put({'type': 'complete', 'code': current_process.returncode})
            current_process = None
            
        except Exception as e:
            progress_queue.put({'type': 'error', 'data': str(e)})
            current_process = None
    
    thread = threading.Thread(target=run_process)
    thread.start()
    
    return jsonify({'status': 'started'})


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get progress updates (SSE)"""
    def generate():
        while True:
            try:
                msg = progress_queue.get(timeout=1)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg['type'] == 'complete' or msg['type'] == 'error':
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return app.response_class(generate(), mimetype='text/event-stream')


@app.route('/api/stop', methods=['POST'])
def stop_script():
    """Stop the running script"""
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'not_running'})


@app.route('/api/upload-and-process', methods=['POST'])
def upload_and_process():
    """Upload 3D file, render, and process with Claude in one workflow"""
    global temp_dirs
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Get configuration from form data
    try:
        config = json.loads(request.form.get('config', '{}'))
    except:
        return jsonify({'error': 'Invalid configuration'}), 400
    
    if not config.get('api_key'):
        return jsonify({'error': 'API key is required'}), 400
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix='spatial_intelligence_')
    temp_dirs.append(temp_dir)
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(temp_dir, filename)
    file.save(file_path)
    
    # Start processing in thread
    def process_file():
        try:
            uid = Path(filename).stem
            
            # Step 1: Create pickle file with object path
            progress_queue.put({'type': 'output', 'data': f'📁 Processing file: {filename}'})
            progress_queue.put({'type': 'output', 'data': f'🔧 Setting up temporary workspace at {temp_dir}'})
            
            pkl_path = os.path.join(temp_dir, 'object_path.pkl')
            with open(pkl_path, 'wb') as f:
                pickle.dump({uid: file_path}, f)
            
            # Step 2: Run Blender rendering (type1 and type2)
            progress_queue.put({'type': 'output', 'data': '🎨 Starting Blender rendering...'})
            
            # Find Blender executable
            blender_paths = [
                './blender-3.4.1-linux-x64/blender',
                'blender',
                '/Applications/Blender.app/Contents/MacOS/Blender',
                'C:\\Program Files\\Blender Foundation\\Blender\\blender.exe'
            ]
            
            blender_cmd = None
            for path in blender_paths:
                if os.path.exists(path) or shutil.which(path):
                    blender_cmd = path
                    break
            
            if not blender_cmd:
                progress_queue.put({'type': 'error', 'data': 'Blender not found. Please install Blender or set correct path.'})
                return
            
            # Render type 1 (8 horizontal views)
            progress_queue.put({'type': 'output', 'data': '  → Rendering Type 1: 8 horizontal views...'})
            render1_cmd = [
                blender_cmd, '-b', '-P', 'render_script_type1.py', '--',
                '--object_path_pkl', pkl_path,
                '--parent_dir', temp_dir
            ]
            
            result = subprocess.run(render1_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                progress_queue.put({'type': 'error', 'data': f'Rendering type 1 failed: {result.stderr}'})
                return
            
            # Render type 2 (20 random views)
            progress_queue.put({'type': 'output', 'data': '  → Rendering Type 2: 20 random views...'})
            render2_cmd = [
                blender_cmd, '-b', '-P', 'render_script_type2.py', '--',
                '--object_path_pkl', pkl_path,
                '--parent_dir', temp_dir
            ]
            
            result = subprocess.run(render2_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                progress_queue.put({'type': 'error', 'data': f'Rendering type 2 failed: {result.stderr}'})
                return
            
            progress_queue.put({'type': 'output', 'data': '✓ Rendering complete! Images saved.'})
            
            # Step 3: Run Claude processing
            progress_queue.put({'type': 'output', 'data': '🤖 Starting Claude API processing...'})
            
            python_cmd = sys.executable
            claude_cmd = [
                python_cmd, 'captioning_claude_structured.py',
                '--api_key', config['api_key'],
                '--parent_dir', temp_dir,
                '--model', config.get('model', 'claude-3-5-sonnet-20241022'),
                '--num_views', str(config.get('num_views', 6)),
                '--max_tokens', str(config.get('max_tokens', 4096)),
                '--rate_limit_delay', str(config.get('rate_limit_delay', 1.0))
            ]
            
            # Add template
            if config.get('use_inline_template') and config.get('inline_template'):
                claude_cmd.extend(['--template_json', json.dumps(config['inline_template'])])
            else:
                claude_cmd.extend(['--template_file', config.get('template_file', './example_template.json')])
            
            if not config.get('use_diffurank', True):
                claude_cmd.append('--no_diffurank')
            
            # Run Claude processing
            process = subprocess.Popen(
                claude_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                progress_queue.put({'type': 'output', 'data': line.strip()})
            
            process.wait()
            
            if process.returncode == 0:
                # Step 4: Read and return results
                progress_queue.put({'type': 'output', 'data': '✓ Claude processing complete!'})
                
                output_file = os.path.join(temp_dir, 'Cap3D_imgs', uid, 'structured_output.json')
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        result_json = json.load(f)
                    
                    # Get rendered images
                    img_dir = os.path.join(temp_dir, 'Cap3D_imgs', uid)
                    images = []
                    for img_file in sorted(glob.glob(os.path.join(img_dir, '*.png')))[:10]:
                        with open(img_file, 'rb') as f:
                            img_data = base64.b64encode(f.read()).decode('utf-8')
                        images.append({
                            'name': os.path.basename(img_file),
                            'data': f'data:image/png;base64,{img_data}'
                        })
                    
                    progress_queue.put({
                        'type': 'complete',
                        'data': {
                            'json_output': result_json,
                            'images': images,
                            'temp_dir': temp_dir
                        }
                    })
                else:
                    progress_queue.put({'type': 'error', 'data': 'Output file not found after processing'})
            else:
                progress_queue.put({'type': 'error', 'data': 'Claude processing failed'})
                
        except Exception as e:
            progress_queue.put({'type': 'error', 'data': f'Processing error: {str(e)}'})
    
    thread = threading.Thread(target=process_file)
    thread.start()
    
    return jsonify({'status': 'started', 'temp_dir': temp_dir})


@app.route('/api/cleanup', methods=['POST'])
def cleanup_temp():
    """Clean up temporary directory"""
    global temp_dirs
    
    temp_dir = request.json.get('temp_dir')
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            if temp_dir in temp_dirs:
                temp_dirs.remove(temp_dir)
            return jsonify({'status': 'cleaned'})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return jsonify({'status': 'not_found'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)

