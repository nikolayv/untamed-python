#!/usr/bin/env python3
"""Download a subset of COCO images for training."""
import os
import sys

NUM_IMAGES = 2000

print(f"Downloading subset of {NUM_IMAGES} COCO training images...")
print("Note: We'll download the full zip (~13GB) but only extract a subset")
print("This ensures proper zip file handling.\n")

response = input("Continue with full download? (y/n): ")
if response.lower() != 'y':
    print("\nAlternative: Use your own images!")
    print("  1. Create a folder: mkdir -p data/train_custom")
    print("  2. Put any diverse images in data/train_custom/")
    print("  3. Train with: --dataset data/train_custom")
    sys.exit(0)

import zipfile
import requests

os.makedirs("data", exist_ok=True)

url = "http://images.cocodataset.org/zips/train2014.zip"
zip_path = "data/train2014.zip"

# Download
print(f"\nDownloading from {url}")
print("This will take 10-20 minutes depending on your connection...")

response = requests.get(url, stream=True)
total_size = int(response.headers.get('content-length', 0))
downloaded = 0

with open(zip_path, 'wb') as f:
    for data in response.iter_content(8192):
        downloaded += len(data)
        f.write(data)
        done = int(50 * downloaded / total_size)
        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB")
        sys.stdout.flush()

print("\n\nExtracting subset of images...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    all_files = [f for f in zip_ref.namelist() if f.endswith('.jpg')]
    files_to_extract = all_files[:NUM_IMAGES]

    for i, file in enumerate(files_to_extract, 1):
        zip_ref.extract(file, "data/")
        if i % 200 == 0:
            print(f"Extracted {i}/{len(files_to_extract)} images...")

print(f"\n✓ Dataset ready!")
print(f"  Location: data/train2014/")
print(f"  Images: {len(files_to_extract)}")
print("\nTrain with your custom style:")
print("  python neural_style/neural_style.py train --dataset data/train2014 --style-image images/style-images/your-style.jpg --save-model-dir models/ --epochs 2 --accel")
