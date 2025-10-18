# EC2 Training Session State - 2025-10-17

## Current Situation

### Goal
Train all 30 style transfer models using EC2 for faster parallel training.
Currently testing 2 different approaches to get stronger stylization than current models.

### Mac Training Status (Background)
- **Running**: `examples/fast_neural_style/train_batch.sh` (Bash 269634)
- **Completed**: 4 models (zebra_fur, zebra_nature, tiger_fur, tiger_whole)
- **In Queue**: 6 more models (mandarin duck, fawn, gray wolf)
- **Total in script**: 10 models

### Total Style Images Available
**30 total style images** in `examples/fast_neural_style/images/style-images/`:
- 4 already trained
- 6 in Mac training queue
- **20 not yet trained**

### Problem Identified
User noticed trained models produce **milder stylization** than original pre-trained models (mosaic, candy, etc.).
This is likely because:
- Original models trained on more images (82k vs our 15k)
- Original models may have used higher style-weight parameter

### Test Plan
Launch 2 EC2 instances to test which approach gives stronger stylization:
1. **Test 1**: 15k images, style-weight=5e10 (5x default)
2. **Test 2**: 40k images, style-weight=1e10 (default)

**Test style**: zebra_nature.jpg (not zebra_fur - we want clean test)

## AWS Resources Created

### S3 Bucket
**Name**: `nav-untamed-style-transfer-models`
**Region**: us-east-1

**Uploaded files**:
- zebra_fur.jpg
- zebra_nature.jpg
- mandarin_duck_plumage_1.png
- mandarin_duck_nature.jpg
- fawn_fur.jpg
- fawn_in_nature_1.jpeg
- gray_wolf_fur.jpg
- gray_wolf_whole.jpg

**Bucket is private** - EC2 instances access via IAM role

### EC2 Instances
**Currently Running** (as of last check):
- Instance 1: `i-016296f85af1bb025` (3.237.33.13) - test-15k-5x-style
- Instance 2: `i-08fd7e9e55c0da83a` (35.175.120.38) - test-40k-default

**Status**: Started training with zebra_fur.jpg, need to switch to zebra_nature.jpg

**Configuration**:
- Type: g4dn.xlarge (NVIDIA T4 GPU)
- AMI: ami-0c398cb65a93047f2 (Ubuntu 22.04)
- Key: memgenie_deploy (located at ~/.aws/memgenie_deploy.pem)
- Security Group: sg-198b6e12 (default)
- Spot instances: $0.16/hr each
- Storage: 50GB gp3

## Files Created

### Training Scripts

**`/Users/nikolay/src/untamed/ec2_training_test.sh`**
- Configurable EC2 training script
- Parameters: STYLE_URL, STYLE_NAME, NUM_IMAGES, STYLE_WEIGHT, S3_BUCKET
- Downloads COCO dataset from source (no upload needed)
- Uploads trained model to S3 with config in filename

**`/Users/nikolay/src/untamed/ec2_training_setup.sh`**
- Original setup script (superseded by ec2_training_test.sh)

**`/Users/nikolay/src/untamed/launch_training_fleet.sh`**
- Script to launch multiple instances in parallel
- Not yet configured/used

### Documentation

**`/Users/nikolay/src/untamed/EC2_TRAINING.md`**
- Complete EC2 training guide
- Manual and automated approaches
- Cost estimates

**`/Users/nikolay/src/untamed/ONNX_JS_CONVERSION.md`**
- Guide for converting models to ONNX for JavaScript use

**`/Users/nikolay/src/untamed/convert_to_onnx.py`**
- Python script to convert .pth/.model files to ONNX format
- Already converted: candy.onnx (6.5MB)

### Model Mapping

**`examples/fast_neural_style/models/model_mapping.json`**
```json
{
  "zebra_fur.jpg": "epoch_2_2025-10-17_15-09-22_100000.0_10000000000.0.model",
  "zebra_nature.jpg": "epoch_2_2025-10-17_16-54-38_100000.0_10000000000.0.model",
  "tiger_fur.png": "epoch_2_2025-10-17_17-59-15_100000.0_10000000000.0.model",
  "tiger_whole.jpg": "epoch_2_2025-10-17_19-07-11_100000.0_10000000000.0.model"
}
```

## Updated Application

**`/Users/nikolay/src/untamed/style_transfer.py`**
- Updated BASE_MODELS dict with 4 new animal pattern models (keys 5-8)
- Removed old models, added comments for remaining models to be trained
- Changed controls to show "1-8" instead of "1-9,a"

## AWS Configuration

**Region**: us-east-1
**Available Keys**: memgenie-db-access, memgenie_deploy, memgenie_img_gen, blender-temp-1760683137
**Using Key**: memgenie_deploy
**Key Location**: ~/.aws/memgenie_deploy.pem
**Security Group**: sg-198b6e12 (default)

## Next Steps

### Immediate (After Restart)

1. **Check/restart test instances** with zebra_nature.jpg:
   ```bash
   # SSH to instances
   ssh -i ~/.aws/memgenie_deploy.pem ubuntu@3.237.33.13
   ssh -i ~/.aws/memgenie_deploy.pem ubuntu@35.175.120.38

   # Check training logs
   tail -f /var/log/training.log
   ```

2. **Wait for test results** (~1-2 hours):
   - Models will upload to: s3://nav-untamed-style-transfer-models/test_results/
   - Download and compare stylization strength

3. **Based on test results**, decide configuration for full fleet:
   - If 5x style-weight wins: Use 15k images, 5e10 style-weight
   - If 40k images wins: Use 40k images, 1e10 style-weight
   - Or mix: Use 40k images, 5e10 style-weight

### Full Training Fleet

**Upload all 30 style images to S3**:
```bash
cd examples/fast_neural_style/images/style-images
for img in *.{jpg,jpeg,png}; do
  aws s3 cp "$img" s3://nav-untamed-style-transfer-models/
done
```

**Launch 26 parallel instances** for remaining models:
- Edit `launch_training_fleet.sh` with chosen configuration
- Launch all 26 at once (~$4-5 on spot for 1 hour)
- Models auto-upload to S3 when complete

**Download all models**:
```bash
aws s3 sync s3://nav-untamed-style-transfer-models/models/ examples/fast_neural_style/models/
```

**Clean up**:
```bash
# Terminate all instances
aws ec2 terminate-instances --instance-ids $(aws ec2 describe-instances --filters "Name=tag:Project,Values=neural-style" --query 'Reservations[*].Instances[*].InstanceId' --output text)
```

## Cost Tracking

**So far**:
- S3 storage: ~5MB uploaded, negligible cost
- 2 test instances running: ~$0.32/hour on spot

**Expected total**:
- Test phase: ~$1-2
- Full fleet (26 instances): ~$4-5
- **Total estimated**: ~$6-7 for all 26 models

## Commands Reference

**Check instance status**:
```bash
aws ec2 describe-instances --instance-ids i-016296f85af1bb025 i-08fd7e9e55c0da83a --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value|[0],State.Name,PublicIpAddress]' --output table
```

**Check S3 results**:
```bash
aws s3 ls s3://nav-untamed-style-transfer-models/test_results/
```

**Download test models**:
```bash
aws s3 sync s3://nav-untamed-style-transfer-models/test_results/ ./test_models/
```

## Notes

- iTerm requested contacts/calendar access during setup (denied - not needed)
- Mac training continues in background (Bash 269634)
- All 30 style images preserved in `examples/fast_neural_style/images/style-images/`
- ONNX conversion working: candy.onnx already created (6.5MB)

## Todo List State
1. [in_progress] Test EC2 training with different configurations
2. [pending] Compare training results: 40k images vs higher style-weight
3. [pending] Launch full fleet of 26 instances for remaining models
