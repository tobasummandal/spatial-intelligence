#!/usr/bin/env python3
"""
Flask Web UI for Structured JSON Generation with Claude API
"""
import os
import sys
import json
import glob
import base64
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import subprocess
import threading
import queue
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'spatial-intelligence-key'

# Global progress tracking
progress_queue = queue.Queue()
current_process = None


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


if __name__ == '__main__':
    app.run(debug=True, port=5000)

