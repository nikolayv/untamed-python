# Resumable Training Script

## Problem

The original `train_batch.sh` script trains models sequentially without resume support. If interrupted:
- All progress is lost for the current model
- Already-completed models must be retrained from scratch
- No way to track which models finished successfully

## Solution

`train_batch_resumable.sh` adds state tracking and smart skip logic:
- Tracks completed models in `.training_state` file
- Skips already-trained models automatically
- Safe to interrupt and resume at any time

## How It Works

**State File**: `.training_state`
- Plain text file with one style path per line
- Each line represents a successfully completed model
- Only written after training completes successfully (exit code 0)

**Skip Logic**:
```bash
# Before training each style:
1. Check if style path exists in .training_state
2. If yes → Skip with ✓ indicator
3. If no → Train the model
4. After successful training → Add to .training_state
```

**Interruption Handling**:
- Ctrl+C or failure → script exits immediately
- Incomplete model is NOT marked as complete
- Next run will retry that model

## Usage

### Basic Usage
```bash
cd /Users/nikolay/src/untamed/examples/fast_neural_style
./train_batch_resumable.sh
```

### Resume After Interruption
```bash
# Same command - automatically resumes
./train_batch_resumable.sh
```

### Reset and Start Over
```bash
# Remove state file to retrain all models
rm .training_state
./train_batch_resumable.sh
```

### Check Progress
```bash
# See which models are marked complete
cat .training_state

# Count completed models
wc -l < .training_state
```

## Example Workflow

### Initial Run (Interrupted)
```bash
$ ./train_batch_resumable.sh
========================================
Training 10 models on 15,000 images
========================================
State file: .training_state
Resume support: Enabled

========================================
[1/10] Style: zebra_fur.jpg
========================================
Started: Fri Oct 17 13:43:24 EDT 2025
# ... training ...
✓ Completed successfully

========================================
[2/10] Style: zebra_nature.jpg
========================================
# ... training ...
^C  # User interrupts here
```

### Resume Run
```bash
$ ./train_batch_resumable.sh
========================================
Training 10 models on 15,000 images
========================================
State file: .training_state
Resume support: Enabled

Found 1 already-trained model(s)
These will be skipped

========================================
[1/10] Style: zebra_fur.jpg
========================================
✓ SKIPPED - Already trained

========================================
[2/10] Style: zebra_nature.jpg
========================================
Started: Fri Oct 17 16:30:15 EDT 2025
# ... continues training from model 2 ...
```

## Testing the Resume Feature

### Test 1: Interrupt and Resume
```bash
# Start training
./train_batch_resumable.sh

# After first model completes, press Ctrl+C

# Check state file
cat .training_state
# Should show: images/style-images/zebra_fur.jpg

# Resume
./train_batch_resumable.sh
# Should skip zebra_fur.jpg and continue with zebra_nature.jpg
```

### Test 2: Verify Skip Logic
```bash
# Manually add a style to state file
echo "images/style-images/tiger_fur.png" >> .training_state

# Run training
./train_batch_resumable.sh
# Should skip tiger_fur.png when it reaches that style
```

### Test 3: Reset and Retrain
```bash
# Train a few models
./train_batch_resumable.sh
# Ctrl+C after 2-3 models

# Check progress
wc -l < .training_state  # Should show 2 or 3

# Reset
rm .training_state

# Verify reset
cat .training_state  # Should say "No such file or directory"

# Restart from beginning
./train_batch_resumable.sh
# Should train all models from scratch
```

## Current Training Status

As of 2025-10-17:
- Original `train_batch.sh` is currently running (model 1/10)
- Estimated completion: 5-10 hours
- New `train_batch_resumable.sh` ready for future training runs

## Configuration

Both scripts use the same configuration:
```bash
DATASET="data/train_15k"
EPOCHS=2
SAVE_DIR="models"
CHECKPOINT_DIR="models/checkpoints"
LOG_INTERVAL=100
STATE_FILE=".training_state"  # Only in resumable version
```

## Troubleshooting

**State file out of sync**:
```bash
# If .training_state lists models that don't exist in models/
# Remove the state file and let it rebuild
rm .training_state
```

**Want to retrain specific model**:
```bash
# Edit .training_state and remove the line for that style
# Or delete entire file to retrain all
```

**Training fails silently**:
```bash
# Check the exit code
echo $?  # Non-zero means failure

# Check training logs
tail -f training_zebra_fur.jpg.log
```

## Notes

- The original `train_batch.sh` is unchanged and still works
- Use `train_batch_resumable.sh` for long training runs that might be interrupted
- State file is intentionally simple (plain text) for easy inspection and editing
- Each training run still creates individual log files: `training_{style_name}.log`
