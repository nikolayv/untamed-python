#!/bin/bash
# Train models for all 6 new style images sequentially

DATASET="data/train_15k"
EPOCHS=2
SAVE_DIR="models"
CHECKPOINT_DIR="models/checkpoints"
LOG_INTERVAL=100

# Style images to train on
STYLES=(
    "images/style-images/Autumn Forest Sunset.jpg"
    "images/style-images/Bulgarian Kuker Rituals.jpg"
    "images/style-images/hunters_cave_painting.png"
    "images/style-images/Krampus Morzger Pass Salzburg Oct 2008.jpg"
    "images/style-images/Storm King Alexander Calder.jpg"
    "images/style-images/purple_swirly.png"
)

echo "========================================"
echo "Training ${#STYLES[@]} models on 15,000 images"
echo "========================================"

for i in "${!STYLES[@]}"; do
    style="${STYLES[$i]}"
    echo ""
    echo "========================================"
    echo "[$((i+1))/${#STYLES[@]}] Training: $(basename "$style")"
    echo "========================================"
    echo "Started: $(date)"

    python -u neural_style/neural_style.py train \
        --dataset "$DATASET" \
        --style-image "$style" \
        --style-size 512 \
        --save-model-dir "$SAVE_DIR" \
        --epochs $EPOCHS \
        --accel \
        --checkpoint-model-dir "$CHECKPOINT_DIR" \
        --log-interval $LOG_INTERVAL \
        2>&1 | tee "training_$(basename "$style" | sed 's/ /_/g').log"

    echo ""
    echo "Completed: $(date)"
    echo "========================================"
done

echo ""
echo "All training completed!"
echo "Models saved in: $SAVE_DIR"
ls -lh "$SAVE_DIR"/*.model
