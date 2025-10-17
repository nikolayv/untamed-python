#!/bin/bash
# Train models for animal pattern style images sequentially with resume support
# This script can be interrupted and resumed - it skips already-trained models

DATASET="data/train_15k"
EPOCHS=2
SAVE_DIR="models"
CHECKPOINT_DIR="models/checkpoints"
LOG_INTERVAL=100
STATE_FILE=".training_state"
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

# Function to check if a model for this style already exists
is_model_trained() {
    local style_file="$1"
    local style_basename=$(basename "$style_file" | sed 's/\.[^.]*$//')  # Remove extension

    # Check if there's a completed model for this style
    # Model files are named like: epoch_2_TIMESTAMP_CONTENT_WEIGHT_STYLE_WEIGHT.model
    # We'll check if any .model file was created after training this style
    if grep -q "^$style_file$" "$STATE_FILE" 2>/dev/null; then
        return 0  # Already trained
    else
        return 1  # Not trained yet
    fi
}

# Function to mark a model as trained
mark_trained() {
    local style_file="$1"
    echo "$style_file" >> "$STATE_FILE"
}

# Create state file if it doesn't exist
touch "$STATE_FILE"

echo "========================================"
echo "Training ${#STYLES[@]} models on 15,000 images"
echo "========================================"
echo "State file: $STATE_FILE"
echo "Resume support: Enabled"
echo ""

# Count how many are already done
trained_count=0
for style in "${STYLES[@]}"; do
    if is_model_trained "$style"; then
        ((trained_count++))
    fi
done

if [ $trained_count -gt 0 ]; then
    echo "Found $trained_count already-trained model(s)"
    echo "These will be skipped"
    echo ""
fi

for i in "${!STYLES[@]}"; do
    style="${STYLES[$i]}"
    style_name=$(basename "$style")

    echo "========================================"
    echo "[$((i+1))/${#STYLES[@]}] Style: $style_name"
    echo "========================================"

    # Check if already trained
    if is_model_trained "$style"; then
        echo "✓ SKIPPED - Already trained"
        echo ""
        continue
    fi

    echo "Started: $(date)"

    # Train the model
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

    # Check if training completed successfully
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        mark_trained "$style"
        update_mapping "$style"
        echo "✓ Completed successfully"
    else
        echo "✗ Training failed or was interrupted"
        echo "Run this script again to resume from next model"
        exit 1
    fi

    echo "Finished: $(date)"
    echo ""
done

echo ""
echo "========================================"
echo "All training completed!"
echo "========================================"
echo "Models saved in: $SAVE_DIR"
ls -lh "$SAVE_DIR"/*.model 2>/dev/null || echo "No .model files found"
echo ""
echo "To reset and retrain all models, run:"
echo "  rm $STATE_FILE"
