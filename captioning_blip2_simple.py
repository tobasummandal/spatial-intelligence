import torch
from PIL import Image
import glob
import pickle
from tqdm import tqdm
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent_dir", type=str, default='./example_material')
    parser.add_argument("--model_name", type=str, default='Salesforce/blip-image-captioning-large', 
                        help='Use smaller BLIP model for faster captioning')
    parser.add_argument("--num_captions", type=int, default=5)
    return parser.parse_args()

def main():
    args = parse_args()

    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load model and processor - using smaller BLIP model
    print(f"Loading model {args.model_name}...")
    from transformers import BlipProcessor, BlipForConditionalGeneration
    processor = BlipProcessor.from_pretrained(args.model_name)
    model = BlipForConditionalGeneration.from_pretrained(args.model_name)
    model.to(device)
    model.eval()

    # Find all folders with images
    infolder = glob.glob(os.path.join(args.parent_dir, 'Cap3D_imgs', '*'))
    print(f"Found {len(infolder)} folders to process")

    count = 0
    for folder in tqdm(infolder):
        if not os.path.exists(folder):
            continue
        if os.path.exists(os.path.join(folder, 'caption.pkl')):
            print(f"Skipping {folder} - already has captions")
            continue
        
        captions = {}
        for j in range(28):
            filename = os.path.join(folder, '%05d.png' % j)
            if not os.path.exists(filename):
                continue
                
            try:
                raw_image = Image.open(filename).convert("RGB")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue

            # Generate multiple captions
            inputs = processor(raw_image, return_tensors="pt").to(device)
            
            caption_list = []
            for _ in range(args.num_captions):
                with torch.no_grad():
                    generated_ids = model.generate(
                        **inputs,
                        max_length=50,
                        do_sample=True,
                        top_p=0.9,
                        temperature=0.9
                    )
                caption = processor.decode(generated_ids[0], skip_special_tokens=True)
                caption_list.append(caption)

            captions[j] = caption_list
            print(f"  Image {j:05d}: {caption_list[0]}")

        count += 1
        print(f"\nProcessed {count}: {folder}")
        
        # Save captions
        with open(os.path.join(folder, 'caption.pkl'), 'wb') as f:
            pickle.dump(captions, f)
        print(f"Saved captions to {os.path.join(folder, 'caption.pkl')}")
            
if __name__ == "__main__":
    main()
