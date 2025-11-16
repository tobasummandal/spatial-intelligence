# Structured JSON Generation with Claude API

Generate structured JSON descriptions from 3D object renderings using Claude's vision API.

## Features

- Send multiple rendered views to Claude for comprehensive 3D understanding
- Flexible JSON structure definition via template file or inline JSON
- Automatic use of DiffuRank scores to select best views (if available)
- Progress tracking with resume capability
- Rate limiting and error handling

## Installation

```bash
pip install anthropic
```

## Usage

### Basic Usage

```bash
python captioning_claude_structured.py \
  --api_key "YOUR_CLAUDE_API_KEY" \
  --parent_dir ./example_material \
  --template_file ./example_template.json
```

### Using Inline Template

```bash
python captioning_claude_structured.py \
  --api_key "YOUR_CLAUDE_API_KEY" \
  --parent_dir ./example_material \
  --template_json '{"summary": "description", "objects": []}'
```

### Advanced Options

```bash
python captioning_claude_structured.py \
  --api_key "YOUR_CLAUDE_API_KEY" \
  --parent_dir ./example_material \
  --template_file ./example_template.json \
  --model claude-3-5-sonnet-latest \
  --num_views 6 \
  --use_diffurank \
  --max_tokens 4096 \
  --rate_limit_delay 1.0 \
  --overwrite
```

## Arguments

- `--api_key`: Anthropic Claude API key (required)
- `--parent_dir`: Parent directory containing Cap3D_imgs folder (default: `./example_material`)
- `--template_file`: Path to JSON template file (default: `./example_template.json`)
- `--template_json`: Inline JSON template string (overrides template_file)
- `--model`: Claude model to use (default: `claude-3-5-sonnet-latest`)
  - Options: `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest`, `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`, `claude-sonnet-4-5-20250929`
- `--num_views`: Number of views to send (default: 6)
- `--use_diffurank`: Use DiffuRank scores if available (default: true)
- `--no_diffurank`: Don't use DiffuRank scores
- `--max_tokens`: Maximum tokens for Claude response (default: 4096)
- `--overwrite`: Overwrite existing outputs
- `--rate_limit_delay`: Delay between API calls in seconds (default: 1.0)

## Template Structure

The template defines the JSON structure you want Claude to generate. You can customize it for your specific needs.

Example template (`example_template.json`):

```json
{
  "image_summary": "",
  "objects": [
    {
      "label": "",
      "bbox": [0, 0, 0, 0],
      "attributes": []
    }
  ],
  "spatial_relationships": [
    {
      "a": "",
      "b": "",
      "relation": ""
    }
  ]
}
```

## Output

The script generates `structured_output.json` files in each object's folder:
```
parent_dir/
  Cap3D_imgs/
    object_uid/
      00000.png
      00001.png
      ...
      structured_output.json  ← Generated output
```

## Example Output

For a bedroom scene:

```json
{
  "image_summary": "A small dorm room with a bed on the right side...",
  "objects": [
    {
      "label": "bed",
      "bbox": [820, 210, 1150, 860],
      "attributes": ["unmade", "twin_size"]
    }
  ],
  "spatial_relationships": [
    {
      "a": "laptop",
      "b": "desk",
      "relation": "on_top_of"
    }
  ]
}
```

## Notes

- The script automatically skips folders that already have `structured_output.json` (use `--overwrite` to reprocess)
- If DiffuRank scores exist, the top-ranked views are used
- Rate limiting helps avoid API throttling
- Progress is saved per-folder, so you can safely interrupt and resume

