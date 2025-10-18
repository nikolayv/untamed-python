#!/bin/bash
# EC2 Training Script with configurable parameters
# Usage: ./script.sh STYLE_IMAGE_URL STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET

set -e

STYLE_IMAGE_URL="$1"
STYLE_IMAGE_NAME="$2"
NUM_IMAGES="${3:-15000}"  # Default 15k
STYLE_WEIGHT="${4:-1e10}" # Default 1e10
S3_BUCKET="$5"

echo "=========================================="
echo "EC2 Neural Style Transfer Training"
echo "=========================================="
echo "Style: $STYLE_IMAGE_NAME"
echo "Images: $NUM_IMAGES"
echo "Style Weight: $STYLE_WEIGHT"
echo "Started: $(date)"
echo ""

# Update and install dependencies
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3-pip git wget unzip awscli > /dev/null 2>&1

# Install PyTorch with CUDA
pip3 install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install -q Pillow numpy

# Setup working directory
cd /home/ubuntu
mkdir -p neural_style_training
cd neural_style_training

# Clone repo
echo "Cloning PyTorch examples..."
git clone -q https://github.com/pytorch/examples.git
cd examples/fast_neural_style

# Download COCO dataset
echo "Downloading COCO dataset..."
mkdir -p data && cd data
wget -q http://images.cocodataset.org/zips/train2014.zip
echo "Extracting dataset..."
unzip -q train2014.zip
mv train2014 train_full

# Use first N images
mkdir -p train_subset
cd train_full
find . -maxdepth 1 -name "*.jpg" | head -n $NUM_IMAGES | xargs -I {} cp {} ../train_subset/
cd ..
rm -rf train_full train2014.zip
mv train_subset train_data
echo "Dataset ready: $(find train_data -name "*.jpg" | wc -l) images"
cd ..

# Download style image from S3
echo "Downloading style image..."
mkdir -p images/style-images
aws s3 cp "s3://$S3_BUCKET/$STYLE_IMAGE_NAME" "images/style-images/$STYLE_IMAGE_NAME"

# Train model
echo ""
echo "=========================================="
echo "Starting Training"
echo "Images: $NUM_IMAGES"
echo "Style Weight: $STYLE_WEIGHT"
echo "=========================================="
echo ""

python3 neural_style/neural_style.py train \
    --dataset data/train_data \
    --style-image "images/style-images/$STYLE_IMAGE_NAME" \
    --style-size 512 \
    --save-model-dir models \
    --epochs 2 \
    --accel \
    --style-weight $STYLE_WEIGHT \
    --checkpoint-model-dir models/checkpoints \
    --log-interval 100

# Find trained model
MODEL_FILE=$(ls -t models/*.model | head -1)
echo ""
echo "=========================================="
echo "Training Complete!"
echo "Model: $MODEL_FILE"
echo "Finished: $(date)"
echo "=========================================="

# Rename with config info
NEW_NAME="$(basename $MODEL_FILE .model)_${NUM_IMAGES}imgs_${STYLE_WEIGHT}sw.model"
mv "$MODEL_FILE" "models/$NEW_NAME"
echo "Renamed to: $NEW_NAME"

# Upload to S3
aws s3 cp "models/$NEW_NAME" "s3://$S3_BUCKET/test_results/$NEW_NAME"
echo "Uploaded to S3: s3://$S3_BUCKET/test_results/$NEW_NAME"

echo ""
echo "All done!"
