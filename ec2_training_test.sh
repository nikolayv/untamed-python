#!/bin/bash
# EC2 Training Script with configurable parameters
# Usage: ./script.sh STYLE_IMAGE_URL STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET [CHECKPOINT]

set -e

STYLE_IMAGE_URL="$1"
STYLE_IMAGE_NAME="$2"
NUM_IMAGES="${3:-15000}"  # Default 15k
STYLE_WEIGHT="${4:-1e10}" # Default 1e10
S3_BUCKET="$5"
CHECKPOINT_FILE="$6"       # Optional: S3 path to checkpoint file

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
apt-get install -y -qq python3-pip git wget unzip > /dev/null 2>&1

# Install PyTorch with CUDA (running as root, no --break-system-packages needed)
pip3 install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install -q Pillow numpy

# Setup working directory
cd /home/ubuntu
mkdir -p neural_style_training
cd neural_style_training

# Clone repo (skip if exists and resuming)
if [ ! -d "examples" ]; then
    echo "Cloning PyTorch examples..."
    git clone -q https://github.com/pytorch/examples.git
fi
cd examples/fast_neural_style

# Download COCO dataset (skip if exists and resuming)
if [ ! -d "data/train_data" ]; then
    echo "Downloading COCO dataset..."
    mkdir -p data && cd data
    wget -q http://images.cocodataset.org/zips/train2014.zip
    echo "Extracting dataset..."
    unzip -q train2014.zip
    mv train2014 train_full

    # Use first N images and organize for ImageFolder
    mkdir -p train_subset/images
    cd train_full
    find . -maxdepth 1 -name "*.jpg" | head -n $NUM_IMAGES | xargs -I {} cp {} ../train_subset/images/
    cd ..
    rm -rf train_full train2014.zip
    mv train_subset train_data
    echo "Dataset ready: $(find train_data/images -name "*.jpg" | wc -l) images"
    cd ..
else
    echo "Dataset already exists, skipping download"
fi

# Fix Pillow compatibility (Image.ANTIALIAS deprecated)
echo "Patching Pillow compatibility..."
sed -i 's/Image\.ANTIALIAS/Image.LANCZOS/g' neural_style/utils.py 2>/dev/null || true

# Fix permissions for checkpoint directory
mkdir -p models/checkpoints
chmod -R 777 models

# Download style image from S3
echo "Downloading style image..."
mkdir -p images/style-images
aws s3 cp "s3://$S3_BUCKET/style-images/$STYLE_IMAGE_NAME" "images/style-images/$STYLE_IMAGE_NAME"

# Download checkpoint if resuming
RESUME_ARG=""
if [ -n "$CHECKPOINT_FILE" ]; then
    echo "Downloading checkpoint from S3..."
    aws s3 cp "$CHECKPOINT_FILE" "models/checkpoints/resume.pth"
    RESUME_ARG="--resume models/checkpoints/resume.pth"
    echo "Will resume from checkpoint"
fi

# Train model
echo ""
echo "=========================================="
echo "Starting Training"
echo "Images: $NUM_IMAGES"
echo "Style Weight: $STYLE_WEIGHT"
if [ -n "$CHECKPOINT_FILE" ]; then
    echo "Resuming from: $CHECKPOINT_FILE"
fi
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
    --log-interval 100 \
    $RESUME_ARG

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

# Calculate descriptive folder name from parameters
STYLE_BASE=$(basename "$STYLE_IMAGE_NAME" | sed 's/\.[^.]*$//' | tr '_' '-')
NUM_IMGS_SHORT=$(echo $NUM_IMAGES | awk '{printf "%.0fk", $1/1000}')
WEIGHT_SHORT=$(echo $STYLE_WEIGHT | awk '{if ($1 == 1e10) print "default"; else if ($1 == 5e10) print "5x"; else print $1}')
MODEL_FOLDER="${STYLE_BASE}-${NUM_IMGS_SHORT}-${WEIGHT_SHORT}"

# Upload to organized S3 location
aws s3 cp "models/$NEW_NAME" "s3://$S3_BUCKET/models/$MODEL_FOLDER/$NEW_NAME"
echo "Uploaded to S3: s3://$S3_BUCKET/models/$MODEL_FOLDER/$NEW_NAME"

echo ""
echo "All done!"
