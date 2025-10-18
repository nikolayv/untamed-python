# EC2 Parallel Training Setup

Train all 6 remaining models in parallel on EC2 spot instances.

## Quick Setup (30 minutes)

### 1. Upload Style Images to S3

First, upload your style images so EC2 instances can download them:

```bash
# Create S3 bucket (one-time)
aws s3 mb s3://neural-style-training-YOUR-NAME

# Upload style images
cd examples/fast_neural_style/images/style-images
aws s3 cp mandarin_duck_plumage_1.png s3://neural-style-training-YOUR-NAME/
aws s3 cp mandarin_duck_nature.jpg s3://neural-style-training-YOUR-NAME/
aws s3 cp fawn_fur.jpg s3://neural-style-training-YOUR-NAME/
aws s3 cp fawn_in_nature_1.jpeg s3://neural-style-training-YOUR-NAME/
aws s3 cp gray_wolf_fur.jpg s3://neural-style-training-YOUR-NAME/
aws s3 cp gray_wolf_whole.jpg s3://neural-style-training-YOUR-NAME/

# Make them publicly readable (or use presigned URLs)
aws s3 sync s3://neural-style-training-YOUR-NAME/ s3://neural-style-training-YOUR-NAME/ --acl public-read
```

### 2. Configure Launch Script

Edit `launch_training_fleet.sh`:

```bash
# Update these values:
KEY_NAME="your-ec2-key-name"  # Your EC2 SSH key name
SECURITY_GROUP="your-security-group"  # Security group with SSH access
S3_BUCKET="neural-style-training-YOUR-NAME"  # Your bucket name

# Update AMI for your region (shown: us-east-1)
# Find Ubuntu AMI: aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" --query 'Images[0].ImageId'
```

Update the S3 URLs in `STYLES` array to match your bucket.

### 3. Launch Training Fleet

```bash
chmod +x launch_training_fleet.sh
./launch_training_fleet.sh
```

This will:
- Launch 6 g4dn.xlarge spot instances
- Each downloads COCO dataset independently
- Each trains 1 model in parallel
- Models uploaded to S3 when done

**Cost: ~$6 for 1 hour** (or ~$18 on-demand if spot unavailable)

### 4. Monitor Progress

```bash
# Check instance status
aws ec2 describe-instances --filters "Name=tag:Project,Values=neural-style" --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' --output table

# SSH to instance and watch logs
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>
tail -f /var/log/training.log

# Check S3 for completed models
aws s3 ls s3://neural-style-training-YOUR-NAME/
```

### 5. Download Trained Models

```bash
# Download all models from S3
aws s3 sync s3://neural-style-training-YOUR-NAME/ examples/fast_neural_style/models/ --exclude "*" --include "*.model"
```

### 6. Cleanup (Save Money!)

```bash
# Terminate all training instances
aws ec2 terminate-instances --instance-ids $(aws ec2 describe-instances --filters "Name=tag:Project,Values=neural-style" "Name=instance-state-name,Values=running" --query 'Reservations[*].Instances[*].InstanceId' --output text)
```

## Alternative: Manual Single Instance

If you just want to test one model first:

```bash
# 1. Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type g4dn.xlarge \
  --key-name your-key \
  --security-groups your-sg \
  --instance-market-options "MarketType=spot" \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=50}"

# 2. SSH in
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>

# 3. Run setup manually
sudo apt update && sudo apt install -y python3-pip git wget unzip
pip3 install torch torchvision Pillow numpy
git clone https://github.com/pytorch/examples.git
cd examples/fast_neural_style

# 4. Download COCO dataset
mkdir -p data && cd data
wget http://images.cocodataset.org/zips/train2014.zip
unzip train2014.zip
mv train2014 train_15k
cd train_15k && ls | head -n 15000 > /tmp/keep.txt && ls | grep -v -F -f /tmp/keep.txt | xargs rm
cd ../..

# 5. Download style image
mkdir -p images/style-images && cd images/style-images
wget https://your-bucket.s3.amazonaws.com/mandarin_duck_plumage_1.png
cd ../..

# 6. Train
python neural_style/neural_style.py train \
  --dataset data/train_15k \
  --style-image images/style-images/mandarin_duck_plumage_1.png \
  --style-size 512 \
  --save-model-dir models \
  --epochs 2 \
  --cuda 1 \
  --log-interval 100
```

## Timing

- Instance launch: 1-2 min
- COCO download: 5-10 min
- Training (2 epochs, 15k images): 30-60 min per model
- **Total: ~1 hour** for all 6 models in parallel

## Cost Breakdown

**Spot instances (recommended):**
- 6 × g4dn.xlarge × 1 hour × $0.16/hr = **$0.96**
- Plus storage: 6 × 50GB × 1 hour × $0.10/GB-month = **$0.02**
- **Total: ~$1**

**On-demand (if spot unavailable):**
- 6 × g4dn.xlarge × 1 hour × $0.526/hr = **$3.16**
- Plus storage: **$0.02**
- **Total: ~$3.20**

Much cheaper than running your Mac for 12 hours!
