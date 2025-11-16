import pickle
import json

# Load the captions
with open('/Users/lingxinchen/Downloads/spatial-intelligence/bedroom_output/Cap3D_imgs/bedroom/caption.pkl', 'rb') as f:
    captions = pickle.load(f)

print("=== Bedroom Captions ===\n")
print(f"Total images captioned: {len(captions)}\n")

for image_num in sorted(captions.keys()):
    print(f"Image {image_num:05d}:")
    for i, caption in enumerate(captions[image_num], 1):
        print(f"  {i}. {caption}")
    print()

# Save to a more readable JSON format
output = {}
for image_num, caption_list in captions.items():
    output[f"{image_num:05d}.png"] = caption_list

with open('/Users/lingxinchen/Downloads/spatial-intelligence/bedroom_output/Cap3D_imgs/bedroom/captions.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n✅ Captions also saved to captions.json for easy reading")
