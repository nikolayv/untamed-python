#!/bin/bash
# Local Training Monitor Script
# Runs on your local machine to manage and monitor remote EC2 training
# Usage: ./monitor_training.sh INSTANCE_IP STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET [LOCAL_STYLE_IMAGE]

INSTANCE_IP="$1"
STYLE_NAME="$2"
NUM_IMAGES="${3:-15000}"
STYLE_WEIGHT="${4:-1e10}"
S3_BUCKET="${5:-nav-untamed-style-transfer-models}"
LOCAL_STYLE_IMAGE="$6"  # Optional: path to local style image to upload

SSH_KEY="${SSH_KEY:-$HOME/.aws/memgenie_deploy.pem}"
SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@$INSTANCE_IP"

if [ -z "$INSTANCE_IP" ] || [ -z "$STYLE_NAME" ]; then
    echo "Usage: $0 INSTANCE_IP STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET [LOCAL_STYLE_IMAGE]"
    echo "Example: $0 3.239.111.89 zebra_fur.jpg 15000 1e10 nav-untamed-style-transfer-models"
    echo "         $0 3.239.111.89 my_style.jpg 15000 1e10 nav-untamed-style-transfer-models ~/Downloads/my_style.jpg"
    exit 1
fi

LOG_FILE="/tmp/training_monitor_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "EC2 Training Monitor"
echo "=========================================="
echo "Instance: $INSTANCE_IP"
echo "Style: $STYLE_NAME"
echo "Images: $NUM_IMAGES"
echo "Weight: $STYLE_WEIGHT"
echo "S3 Bucket: $S3_BUCKET"
echo "Log: $LOG_FILE"
echo "Started: $(date)"
echo ""

# Check instance connectivity
echo "Checking instance connectivity..."
if ! $SSH_CMD "echo 'Connected'" >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to instance $INSTANCE_IP"
    exit 1
fi
echo "✓ Instance is reachable"

# Upload local style image if provided
if [ -n "$LOCAL_STYLE_IMAGE" ] && [ -f "$LOCAL_STYLE_IMAGE" ]; then
    echo ""
    echo "Uploading local style image to S3..."
    aws s3 cp "$LOCAL_STYLE_IMAGE" "s3://$S3_BUCKET/style-images/$STYLE_NAME"
    echo "✓ Style image uploaded to S3"
fi

# Copy training script to instance
echo ""
echo "Copying training script to instance..."
scp -i $SSH_KEY -o StrictHostKeyChecking=no /Users/nikolay/src/untamed/ec2_train.sh ubuntu@$INSTANCE_IP:/tmp/ec2_train.sh
$SSH_CMD "chmod +x /tmp/ec2_train.sh"
echo "✓ Training script copied"

# Start training in background
echo ""
echo "=========================================="
echo "Starting Training on EC2"
echo "=========================================="
TRAIN_LOG="training_$(echo $STYLE_NAME | sed 's/\.[^.]*$//')_$(date +%s).log"
$SSH_CMD "nohup /tmp/ec2_train.sh '$STYLE_NAME' '$NUM_IMAGES' '$STYLE_WEIGHT' '$S3_BUCKET' > ~/$TRAIN_LOG 2>&1 & echo 'Training started - log: ~/$TRAIN_LOG'"

echo "Waiting 10 seconds for training to initialize..."
sleep 10

# Monitor with increasing intervals
echo ""
echo "=========================================="
echo "Monitoring Training Progress"
echo "=========================================="
echo "Remote log file: ~/$TRAIN_LOG"
echo ""

INTERVALS=(10 10 15 15 20 20 30 30 60 60 120 120 180 180 300 300 300 300 300 300)
CHECK_NUM=0

for INTERVAL in "${INTERVALS[@]}"; do
    CHECK_NUM=$((CHECK_NUM + 1))

    # Get training status - check both possible log locations
    TRAINING_LOG=$($SSH_CMD "tail -50 ~/$TRAIN_LOG 2>/dev/null || tail -50 /tmp/training.log 2>/dev/null" 2>/dev/null)

    # Check if complete
    if echo "$TRAINING_LOG" | grep -q "All done!"; then
        echo ""
        echo "=========================================="
        echo "✓ TRAINING COMPLETE!"
        echo "=========================================="
        echo "$TRAINING_LOG" | grep -E "Uploaded to:|All done!"
        echo ""
        echo "Final log saved to: $LOG_FILE"
        exit 0
    fi

    # Get current progress
    EPOCH=$(echo "$TRAINING_LOG" | grep "Epoch" | tail -1)
    ERRORS=$(echo "$TRAINING_LOG" | grep -i "error" | tail -3)

    # Get resource utilization
    GPU_UTIL=$($SSH_CMD "nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu --format=csv,noheader,nounits 2>/dev/null" 2>/dev/null)

    # Display status
    echo "[Check #$CHECK_NUM @ $(date '+%H:%M:%S')]"
    if [ -n "$EPOCH" ]; then
        echo "  Progress: $EPOCH"
    else
        echo "  Progress: Initializing..."
    fi

    if [ -n "$GPU_UTIL" ]; then
        echo "  GPU: $GPU_UTIL (util%, mem%, temp°C)"
    fi

    if [ -n "$ERRORS" ]; then
        echo "  ⚠ Errors detected:"
        echo "$ERRORS" | sed 's/^/    /'
    fi

    # Save full log periodically
    if [ $((CHECK_NUM % 5)) -eq 0 ]; then
        echo "$TRAINING_LOG" > "/tmp/training_snapshot_${CHECK_NUM}.log"
    fi

    echo "  Next check in ${INTERVAL}s..."
    echo ""

    sleep $INTERVAL
done

# If we've exhausted all intervals without completion
echo "=========================================="
echo "Monitoring period exhausted"
echo "=========================================="
echo "Training appears to still be running after all checks."
echo "Connect manually to check status:"
echo "  ssh -i $SSH_KEY ubuntu@$INSTANCE_IP"
echo "  tail -f /tmp/training.log"
echo ""
echo "Full log saved to: $LOG_FILE"
