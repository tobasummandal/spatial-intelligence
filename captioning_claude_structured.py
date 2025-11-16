#!/usr/bin/env python3
# ==============================================================================
# Structured JSON Generation from 3D Object Renderings using Claude API
# ==============================================================================
import base64
import anthropic
import os
import json
import glob
import argparse
import pickle
import numpy as np
from pathlib import Path
from tqdm import tqdm
import time


def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_paths(folder_path, num_views=6, use_diffurank=True):
    """
    Get image paths for a given folder.
    If diffurank_scores.pkl exists, use top-ranked views.
    Otherwise, use first num_views images.
    """
    image_paths = []
    
    # Try to use DiffuRank scores if available
    diffurank_path = os.path.join(folder_path, 'diffurank_scores.pkl')
    if use_diffurank and os.path.exists(diffurank_path):
        try:
            diffurank_scores = pickle.load(open(diffurank_path, 'rb'))
            ranks = np.argsort(diffurank_scores)[::-1]  # Sort descending
            for i in range(min(num_views, len(ranks))):
                img_path = os.path.join(folder_path, '%05d.png' % ranks[i])
                if os.path.exists(img_path):
                    image_paths.append(img_path)
        except Exception as e:
            print(f"Warning: Could not load diffurank scores: {e}")
            image_paths = []
    
    # Fallback: use sequentially numbered files (00000.png...)
    if not image_paths:
        for i in range(num_views):
            img_path = os.path.join(folder_path, '%05d.png' % i)
            if os.path.exists(img_path):
                image_paths.append(img_path)
    
    # Final fallback: grab actual files present regardless of numbering
    if not image_paths:
        all_images = sorted(glob.glob(os.path.join(folder_path, '*.png')))
        if not all_images:
            all_images = sorted(glob.glob(os.path.join(folder_path, '*.jpg')))
        image_paths = all_images[:num_views]
    
    return image_paths


def create_claude_prompt(template_structure):
    """Create a prompt for Claude based on the template structure"""
    template_str = json.dumps(template_structure, indent=2)
    
    prompt = f"""You are analyzing rendered views of a 3D object or scene. Multiple images show different angles of the same object/scene.

Based on these images, generate a structured JSON output following this exact template:

{template_str}

Instructions:
- Analyze all provided images to understand the 3D object/scene from multiple angles
- Fill in the JSON structure with accurate information based on what you observe
- For bounding boxes, provide [x_min, y_min, x_max, y_max] coordinates in pixels
- Be specific and detailed in descriptions
- Maintain the exact JSON structure provided
- Only output the JSON, no additional text

Return only valid JSON."""
    
    return prompt


def process_folder(folder_path, client, template_structure, args):
    """Process a single folder with rendered images"""
    uid = os.path.basename(folder_path)
    output_path = os.path.join(folder_path, 'structured_output.json')
    
    # Skip if already processed
    if os.path.exists(output_path) and not args.overwrite:
        return None, "Already processed"
    
    # Get image paths
    image_paths = get_image_paths(folder_path, args.num_views, args.use_diffurank)
    if not image_paths:
        return None, "No images found"
    
    # Encode images
    try:
        image_contents = []
        for img_path in image_paths:
            with open(img_path, "rb") as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
                image_contents.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data,
                    }
                })
    except Exception as e:
        return None, f"Image encoding error: {e}"
    
    # Create prompt
    prompt = create_claude_prompt(template_structure)
    
    # Prepare message content
    message_content = [{"type": "text", "text": prompt}] + image_contents
    
    # Call Claude API
    try:
        message = client.messages.create(
            model=args.model,
            max_tokens=args.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": message_content
                }
            ]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text
        
        # Try to parse as JSON
        try:
            result_json = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                result_json = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                result_json = json.loads(json_str)
            else:
                return None, f"Could not parse JSON from response"
        
        # Save output
        with open(output_path, 'w') as f:
            json.dump(result_json, f, indent=2)
        
        return result_json, "Success"
        
    except anthropic.RateLimitError as e:
        return None, f"Rate limit error: {e}"
    except Exception as e:
        return None, f"API error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured JSON descriptions from 3D object renderings using Claude API"
    )
    parser.add_argument('--api_key', type=str, required=True, 
                       help="Anthropic Claude API Key")
    parser.add_argument('--parent_dir', type=str, default='./example_material',
                       help="Parent directory containing Cap3D_imgs folder")
    parser.add_argument('--template_file', type=str, default='./example_template.json',
                       help="Path to JSON template file")
    parser.add_argument('--template_json', type=str, default=None,
                       help="Inline JSON template string (overrides template_file)")
    parser.add_argument('--model', type=str, default='claude-3-5-sonnet-latest',
                       choices=[
                           'claude-3-5-sonnet-latest',
                           'claude-3-5-haiku-latest',
                           'claude-3-opus-20240229',
                           'claude-3-sonnet-20240229',
                           'claude-3-haiku-20240307',
                           'claude-sonnet-4-5-20250929'
                       ],
                       help="Claude model to use")
    parser.add_argument('--num_views', type=int, default=6,
                       help="Number of views to send to Claude")
    parser.add_argument('--use_diffurank', action='store_true', default=True,
                       help="Use DiffuRank scores if available")
    parser.add_argument('--no_diffurank', dest='use_diffurank', action='store_false',
                       help="Don't use DiffuRank scores")
    parser.add_argument('--max_tokens', type=int, default=4096,
                       help="Maximum tokens for Claude response")
    parser.add_argument('--overwrite', action='store_true',
                       help="Overwrite existing outputs")
    parser.add_argument('--rate_limit_delay', type=float, default=1.0,
                       help="Delay between API calls (seconds)")
    
    args = parser.parse_args()
    
    # Load template
    if args.template_json:
        template_structure = json.loads(args.template_json)
    else:
        with open(args.template_file, 'r') as f:
            template_structure = json.load(f)
    
    print(f"Template structure loaded:")
    print(json.dumps(template_structure, indent=2))
    print()
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=args.api_key)
    
    # Find all folders with images
    imgs_dir = os.path.join(args.parent_dir, 'Cap3D_imgs')
    if not os.path.exists(imgs_dir):
        print(f"Error: {imgs_dir} does not exist")
        return
    
    folders = glob.glob(os.path.join(imgs_dir, '*'))
    folders = [f for f in folders if os.path.isdir(f)]
    print(f"Found {len(folders)} folders to process\n")
    
    # Process folders
    results = {
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    for folder in tqdm(folders, desc="Processing folders"):
        uid = os.path.basename(folder)
        
        result, status = process_folder(folder, client, template_structure, args)
        
        if status == "Already processed":
            results['skipped'] += 1
        elif status == "Success":
            results['success'] += 1
            print(f"\n✓ {uid}: Success")
        else:
            results['failed'] += 1
            results['errors'].append((uid, status))
            print(f"\n✗ {uid}: {status}")
        
        # Rate limiting
        if status == "Success" and args.rate_limit_delay > 0:
            time.sleep(args.rate_limit_delay)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total processed: {len(folders)}")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    
    if results['errors']:
        print(f"\nErrors:")
        for uid, error in results['errors'][:10]:  # Show first 10 errors
            print(f"  - {uid}: {error}")
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more")


if __name__ == "__main__":
    main()

