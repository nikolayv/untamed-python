#!/bin/bash
# EC2 User Data Script for Neural Style Transfer Training
# This script runs on instance launch and trains one model

set -e

# Parse arguments from user data
STYLE_IMAGE_URL="$1"
STYLE_IMAGE_NAME="$2"
S3_BUCKET="$3"  # Optional: S3 bucket to upload model to

echo "=========================================="
echo "EC2 Neural Style Transfer Training"
echo "=========================================="
echo "Style: $STYLE_IMAGE_NAME"
echo "Starting: $(date)"

# Update system and install dependencies
apt-get update
apt-get install -y python3-pip git wget unzip

# Install PyTorch with CUDA support
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install Pillow numpy

# Create working directory
cd /home/ubuntu
mkdir -p neural_style_training
cd neural_style_training

# Clone fast neural style repo
git clone https://github.com/pytorch/examples.git
cd examples/fast_neural_style

# Download COCO 2014 training dataset (~13GB)
echo "Downloading COCO dataset..."
mkdir -p data
cd data
wget http://images.cocodataset.org/zips/train2014.zip
unzip -q train2014.zip
mv train2014 train_15k
# Use first 15k images
cd train_15k
ls | head -n 15000 > /tmp/keep_files.txt
ls | grep -v -F -f /tmp/keep_files.txt | xargs rm
cd ../../

echo "COCO dataset ready: $(ls data/train_15k/*.jpg | wc -l) images"

# Download style image
mkdir -p images/style-images
cd images/style-images
wget -O "$STYLE_IMAGE_NAME" "$STYLE_IMAGE_URL"
cd ../../

# Train the model
echo "Starting training..."
python neural_style/neural_style.py train \
    --dataset data/train_15k \
    --style-image "images/style-images/$STYLE_IMAGE_NAME" \
    --style-size 512 \
    --save-model-dir models \
    --epochs 2 \
    --cuda 1 \
    --checkpoint-model-dir models/checkpoints \
    --log-interval 100

# Find the trained model
MODEL_FILE=$(ls -t models/*.model | head -1)
echo "Training complete: $MODEL_FILE"

# Upload to S3 if bucket specified
if [ -n "$S3_BUCKET" ]; then
    apt-get install -y awscli
    aws s3 cp "$MODEL_FILE" "s3://$S3_BUCKET/$(basename $MODEL_FILE)"
    echo "Uploaded to S3: s3://$S3_BUCKET/$(basename $MODEL_FILE)"
fi

echo "Finished: $(date)"

# Optional: Shutdown instance when done (save money!)
# shutdown -h now
