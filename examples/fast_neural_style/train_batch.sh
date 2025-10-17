#!/bin/bash
# Train models for animal pattern style images sequentially

DATASET="data/train_15k"
EPOCHS=2
SAVE_DIR="models"
CHECKPOINT_DIR="models/checkpoints"
LOG_INTERVAL=100

# Style images to train on - Animal patterns (fur/plumage closeups and whole animals)
STYLES=(
    "images/style-images/zebra_fur.jpg"
    "images/style-images/zebra_nature.jpg"
    "images/style-images/tiger_fur.png"
    "images/style-images/tiger_whole.jpg"
    "images/style-images/mandarin_duck_plumage_1.png"
    "images/style-images/mandarin_duck_nature.jpg"
    "images/style-images/fawn_fur.jpg"
    "images/style-images/fawn_in_nature_1.jpeg"
    "images/style-images/gray_wolf_fur.jpg"
    "images/style-images/gray_wolf_whole.jpg"
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
