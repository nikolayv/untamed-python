#!/bin/bash
# EC2 Training Script
# Trains a single neural style transfer model (runs ON the EC2 instance)
# Usage: ./ec2_train.sh STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET [CHECKPOINT]

set -e

STYLE_IMAGE_NAME="$1"
NUM_IMAGES="${2:-15000}"
STYLE_WEIGHT="${3:-1e10}"
S3_BUCKET="$4"
CHECKPOINT_FILE="$5"  # Optional: S3 path to checkpoint

if [ -z "$STYLE_IMAGE_NAME" ] || [ -z "$S3_BUCKET" ]; then
    echo "Usage: $0 STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET [CHECKPOINT]"
    echo "Example: $0 zebra_fur.jpg 15000 1e10 nav-untamed-style-transfer-models"
    exit 1
fi

echo "=========================================="
echo "EC2 Neural Style Transfer Training"
echo "=========================================="
echo "Style: $STYLE_IMAGE_NAME"
echo "Images: $NUM_IMAGES"
echo "Style Weight: $STYLE_WEIGHT"
echo "S3 Bucket: $S3_BUCKET"
echo "Started: $(date)"
echo ""

# Navigate to training directory
cd /home/ubuntu/neural_style_training/fast_neural_style

# Determine dataset folder based on size
NUM_IMGS_K=$(echo $NUM_IMAGES | awk '{printf "%.0fk", $1/1000}')
DATASET_DIR="data/train_${NUM_IMGS_K}"

if [ ! -d "$DATASET_DIR" ]; then
    echo "ERROR: Dataset $DATASET_DIR not found!"
    echo "Available datasets:"
    ls -la data/
    exit 1
fi

echo "Using dataset: $DATASET_DIR ($(find $DATASET_DIR/images -name "*.jpg" | wc -l) images)"

# Download style image from S3 if not already present
if [ ! -f "images/style-images/$STYLE_IMAGE_NAME" ]; then
    echo "Downloading style image from S3..."
    aws s3 cp "s3://$S3_BUCKET/style-images/$STYLE_IMAGE_NAME" "images/style-images/$STYLE_IMAGE_NAME"
else
    echo "Style image already present locally"
fi

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
echo "Dataset: $DATASET_DIR"
echo "Style Weight: $STYLE_WEIGHT"
if [ -n "$CHECKPOINT_FILE" ]; then
    echo "Resuming from: $CHECKPOINT_FILE"
fi
echo "=========================================="
echo ""

python3 neural_style/neural_style.py train \
    --dataset $DATASET_DIR \
    --style-image "images/style-images/$STYLE_IMAGE_NAME" \
    --style-size 512 \
    --save-model-dir models \
    --epochs 2 \
    --accel \
    --style-weight $STYLE_WEIGHT \
    --checkpoint-model-dir models/checkpoints \
    --log-interval 100 \
    $RESUME_ARG

# Find the trained model
MODEL_FILE=$(ls -t models/*.model 2>/dev/null | head -1)

if [ -z "$MODEL_FILE" ]; then
    echo "ERROR: No model file found after training!"
    exit 1
fi

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
echo "Uploading to S3..."
aws s3 cp "models/$NEW_NAME" "s3://$S3_BUCKET/models/$MODEL_FOLDER/$NEW_NAME"
echo "Uploaded to: s3://$S3_BUCKET/models/$MODEL_FOLDER/$NEW_NAME"

echo ""
echo "All done!"
