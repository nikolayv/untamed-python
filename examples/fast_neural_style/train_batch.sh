#!/bin/bash
# Train models for animal pattern style images sequentially

DATASET="data/train_15k"
EPOCHS=2
SAVE_DIR="models"
CHECKPOINT_DIR="models/checkpoints"
LOG_INTERVAL=100
MAPPING_FILE="models/model_mapping.json"

# Initialize mapping file if it doesn't exist
if [ ! -f "$MAPPING_FILE" ]; then
    echo "{}" > "$MAPPING_FILE"
fi

# Function to update model mapping
update_mapping() {
    local style_image="$1"
    local style_basename=$(basename "$style_image")

    # Find the most recently created .model file
    local model_file=$(ls -t "$SAVE_DIR"/*.model 2>/dev/null | head -1)

    if [ -n "$model_file" ]; then
        local model_basename=$(basename "$model_file")

        # Update JSON mapping using Python
        python3 -c "
import json
import sys

mapping_file = '$MAPPING_FILE'
style_name = '$style_basename'
model_name = '$model_basename'

# Read existing mapping
try:
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
except:
    mapping = {}

# Add new entry
mapping[style_name] = model_name

# Write back
with open(mapping_file, 'w') as f:
    json.dump(mapping, f, indent=2)

print(f'Updated mapping: {style_name} -> {model_name}')
"
    fi
}

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

    # Update mapping file with the newly created model
    update_mapping "$style"

    echo ""
    echo "Completed: $(date)"
    echo "========================================"
done

echo ""
echo "All training completed!"
echo "Models saved in: $SAVE_DIR"
ls -lh "$SAVE_DIR"/*.model
