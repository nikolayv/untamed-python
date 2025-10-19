# AWS EC2 Neural Style Training

Current AWS setup for training neural style transfer models on EC2.

## Infrastructure

### S3 Bucket: `nav-untamed-style-transfer-models`
```
style-images/           # 29 style images for training
models/                 # Trained models organized by config
  zebra-nature-15k-5x/
  zebra-nature-40k-default/
  tiger-fur-40k-default/
  mandarin-duck-plumage-2-40k-default/  # in progress
  mandarin-duck-nature-40k-default/     # in progress
checkpoints/            # Training checkpoints for resuming
```

### Training Script: `setup_and_train.sh`
Location: `/Users/nikolay/src/untamed/setup_and_train.sh` (on GitHub main branch)

**Usage:**
```bash
./setup_and_train.sh STYLE_URL STYLE_NAME NUM_IMAGES STYLE_WEIGHT S3_BUCKET [CHECKPOINT]
```

**Parameters:**
- `STYLE_NAME`: Filename of style image (e.g., `zebra_nature.jpg`)
- `NUM_IMAGES`: 15000 or 40000
- `STYLE_WEIGHT`: 1e10 (default) or 5e10 (5x stronger)
- `S3_BUCKET`: `nav-untamed-style-transfer-models`
- `CHECKPOINT`: (optional) S3 path to resume from

**Features:**
- Idempotent (can resume if interrupted)
- **Maintains separate dataset folders** - no wasteful recreation when switching sizes
  - `data/train_15k/` for 15k image training
  - `data/train_40k/` for 40k image training
- Downloads style images from `s3://BUCKET/style-images/`
- Uploads models to `s3://BUCKET/models/{style-config}/`
- Automatically uploads to S3 when training completes

### EC2 Configuration
- **Instance Type**: g4dn.xlarge (NVIDIA T4 GPU, 4 vCPUs)
- **AMI**: ami-0b5ea73381626fce3 (Ubuntu 22.04 with NVIDIA GPU drivers - comes with ~80GB pre-installed)
- **Key**: memgenie_deploy (~/.aws/memgenie_deploy.pem)
- **Security Group**: sg-198b6e12
- **IAM Role**: EC2-NeuralStyle-Profile (S3 full access)
- **vCPU Limit**: 16 total (can run 4 g4dn.xlarge simultaneously)
- **Storage**: 200GB gp3 (RECOMMENDED - AMI base: ~80GB, dataset: ~17GB, working space: ~20GB, buffer: ~80GB)

## Active Training (2025-10-18)

### Running Instances
1. **mandarin-duck-plumage-2** (i-0a258165d0dba4529 @ 3.239.111.89)
   - 40k images, default weight (1e10)
   - Status: Training in progress

2. **mandarin-duck-nature** (i-071133c23839d21dd)
   - 40k images, default weight (1e10)
   - Status: Just launched

### Completed Models
- zebra-nature-15k-5x
- zebra-nature-40k-default
- tiger-fur-40k-default (2 versions)

## Next Training Queue

Priority styles to train next (40k images, default weight):
1. ✅ mandarin_duck_plumage_2.png (in progress)
2. ✅ mandarin_duck_nature.jpg (in progress)
3. mandarin_duck_plumage_1.png
4. New styles from Downloads/animal art:
   - Verneuil flying fish (15k, default weight)
   - Squirrels 2 (15k, default weight)

Remaining 24+ style images in S3 `style-images/` folder.

## Launching New Training

### Launch Single Instance
```bash
# 1. Create userdata script
cat > /tmp/train_STYLE.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu
curl -o train.sh https://raw.githubusercontent.com/nikolayv/untamed-python/main/ec2_training_test.sh
chmod +x train.sh
nohup ./train.sh unused STYLE_NAME NUM_IMAGES STYLE_WEIGHT nav-untamed-style-transfer-models > /var/log/training.log 2>&1 &
EOF

# 2. Launch instance
aws ec2 run-instances \
  --image-id ami-0b5ea73381626fce3 \
  --instance-type g4dn.xlarge \
  --key-name memgenie_deploy \
  --security-group-ids sg-198b6e12 \
  --iam-instance-profile Name=EC2-NeuralStyle-Profile \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":200,"VolumeType":"gp3"}}]' \
  --user-data file:///tmp/train_STYLE.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=train-STYLE}]'
```

### Monitor Training
```bash
# Get instance IP
aws ec2 describe-instances --instance-ids INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

# SSH and watch logs
ssh -i ~/.aws/memgenie_deploy.pem ubuntu@INSTANCE_IP
tail -f /var/log/training.log

# Or check from local
ssh -i ~/.aws/memgenie_deploy.pem ubuntu@INSTANCE_IP "tail -50 /var/log/training.log"
```

### Reuse Instance for Multiple Jobs
After a training job completes, keep the instance running and launch new job:
```bash
# Instance already has dataset and dependencies
# Just download new style image and train
ssh -i ~/.aws/memgenie_deploy.pem ubuntu@INSTANCE_IP

cd /home/ubuntu/neural_style_training/examples/fast_neural_style
aws s3 cp s3://nav-untamed-style-transfer-models/style-images/NEW_STYLE.jpg images/style-images/

python3 neural_style/neural_style.py train \
  --dataset data/train_data \
  --style-image images/style-images/NEW_STYLE.jpg \
  --style-size 512 \
  --save-model-dir models \
  --epochs 2 \
  --accel \
  --style-weight 1e10 \
  --checkpoint-model-dir models/checkpoints \
  --log-interval 100
```

## Cleanup

### Terminate Instances
```bash
# Terminate specific instance
aws ec2 terminate-instances --instance-ids INSTANCE_ID

# Terminate all training instances
aws ec2 terminate-instances --instance-ids $(
  aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=train-*" "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' --output text
)
```

### Download Models
```bash
# Sync all models from S3
aws s3 sync s3://nav-untamed-style-transfer-models/models/ \
  examples/fast_neural_style/models/ --exclude "*" --include "*.model"
```

## Checkpoint Resume

To resume training from a checkpoint:
```bash
# Checkpoint files are in s3://nav-untamed-style-transfer-models/checkpoints/
# Pass as 6th parameter to training script:
./train.sh unused STYLE_NAME NUM_IMAGES STYLE_WEIGHT BUCKET s3://BUCKET/checkpoints/checkpoint.pth
```

## Cost Estimate

- g4dn.xlarge on-demand: $0.526/hour
- Training time: ~40-60 min per model (40k images)
- Cost per model: ~$0.35-0.50
- Full 30 models: ~$10-15

## Common Commands

```bash
# List running training instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" "Name=instance-type,Values=g4dn.xlarge" \
  --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# List models in S3
aws s3 ls s3://nav-untamed-style-transfer-models/models/ --recursive

# List style images
aws s3 ls s3://nav-untamed-style-transfer-models/style-images/

# Check training progress
ssh -i ~/.aws/memgenie_deploy.pem ubuntu@INSTANCE_IP "tail -20 /var/log/training.log"
```
