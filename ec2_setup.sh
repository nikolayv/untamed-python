#!/bin/bash
# EC2 Instance Setup Script
# Prepares instance for neural style training (userdata or manual execution)
# This script ONLY sets up the environment - does not train

set -e

echo "=========================================="
echo "EC2 Neural Style Training Setup"
echo "Started: $(date)"
echo "=========================================="

# Install system packages
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3-pip git wget unzip screen

# Install PyTorch with CUDA
echo "Installing PyTorch with CUDA support..."
pip3 install --break-system-packages -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install --break-system-packages -q Pillow numpy

# Clone repo
cd /home/ubuntu
if [ ! -d "neural_style_training" ]; then
    echo "Cloning PyTorch examples..."
    git clone -q https://github.com/pytorch/examples.git neural_style_training
fi

cd neural_style_training/fast_neural_style

# Fix Pillow compatibility (Image.ANTIALIAS deprecated)
echo "Patching Pillow compatibility..."
sed -i 's/Image\.ANTIALIAS/Image.LANCZOS/g' neural_style/utils.py 2>/dev/null || true

# Download and prepare datasets
echo "Downloading COCO dataset..."
mkdir -p data && cd data

# Download once
if [ ! -f "train2014.zip" ]; then
    wget -q http://images.cocodataset.org/zips/train2014.zip
fi

# Extract if not already extracted
if [ ! -d "train_full" ]; then
    echo "Extracting dataset..."
    unzip -q train2014.zip
    mv train2014 train_full
fi

# Create 15k subset
if [ ! -d "train_15k" ]; then
    echo "Creating 15k image subset..."
    mkdir -p train_15k/images
    cd train_full
    find . -maxdepth 1 -name "*.jpg" | head -n 15000 | xargs -I {} cp {} ../train_15k/images/
    cd ..
    echo "15k dataset ready: $(find train_15k/images -name "*.jpg" | wc -l) images"
fi

# Create 40k subset
if [ ! -d "train_40k" ]; then
    echo "Creating 40k image subset..."
    mkdir -p train_40k/images
    cd train_full
    find . -maxdepth 1 -name "*.jpg" | head -n 40000 | xargs -I {} cp {} ../train_40k/images/
    cd ..
    echo "40k dataset ready: $(find train_40k/images -name "*.jpg" | wc -l) images"
fi

# Cleanup full dataset zip
rm -f train2014.zip

cd /home/ubuntu/neural_style_training/fast_neural_style

# Fix permissions for checkpoint directory
mkdir -p models/checkpoints images/style-images
chmod -R 777 models images

# Set ownership to ubuntu user
chown -R ubuntu:ubuntu /home/ubuntu/neural_style_training

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "Finished: $(date)"
echo "=========================================="
echo "Ready to train models"
