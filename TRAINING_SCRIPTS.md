# EC2 Training Scripts - Clean Architecture

Three-script system for managing neural style transfer model training on EC2.

## Scripts Overview

### 1. `ec2_setup.sh` - Instance Setup (runs ON EC2)
Prepares a fresh EC2 instance with all dependencies and datasets.

**What it does:**
- Installs Python, PyTorch, CUDA, system dependencies
- Clones PyTorch examples repo
- Downloads and prepares COCO datasets (15k and 40k subsets)
- Fixes compatibility issues
- Sets up directory structure

**Usage:**
```bash
# As EC2 userdata (recommended for new instances)
aws ec2 run-instances \
  --image-id ami-0b5ea73381626fce3 \
  --instance-type g4dn.xlarge \
  --user-data file://ec2_setup.sh \
  ...

# Or run manually on instance
sudo bash ec2_setup.sh
```

**Duration:** ~5-10 minutes (downloads ~18GB dataset)

### 2. `ec2_train.sh` - Training Script (runs ON EC2)
Trains a single neural style transfer model.

**Parameters:**
- `STYLE_NAME` - Filename of style image (e.g., `zebra_fur.jpg`)
- `NUM_IMAGES` - 15000 or 40000
- `STYLE_WEIGHT` - 1e10 (default) or 5e10 (5x stronger)
- `S3_BUCKET` - Your S3 bucket name
- `CHECKPOINT` - (optional) S3 path to resume from

**Usage:**
```bash
# On EC2 instance
./ec2_train.sh zebra_fur.jpg 15000 1e10 nav-untamed-style-transfer-models

# Or from local machine via SSH
ssh ubuntu@INSTANCE_IP "/tmp/ec2_train.sh zebra_fur.jpg 15000 1e10 nav-untamed-style-transfer-models"
```

**Duration:** ~15-20 minutes (15k images), ~40-60 minutes (40k images)

**Output:** Automatically uploads trained model to S3 in organized folders

### 3. `monitor_training.sh` - Local Monitor (runs LOCALLY)
Manages training from your local machine with intelligent monitoring.

**What it does:**
- Tests SSH connectivity
- Uploads local style image to S3 (if provided)
- Copies training script to instance
- Starts training in background
- Monitors with increasing intervals (10s → 5min)
- Shows progress, GPU utilization, errors
- Saves detailed logs locally

**Parameters:**
- `INSTANCE_IP` - EC2 public IP
- `STYLE_NAME` - Filename of style image
- `NUM_IMAGES` - 15000 or 40000
- `STYLE_WEIGHT` - 1e10 or 5e10
- `S3_BUCKET` - Your S3 bucket
- `LOCAL_STYLE_IMAGE` - (optional) Local path to upload

**Usage:**
```bash
# Using style already in S3
./monitor_training.sh 3.239.111.89 zebra_fur.jpg 15000 1e10 nav-untamed-style-transfer-models

# Upload new local style first
./monitor_training.sh 3.239.111.89 my_art.jpg 15000 1e10 nav-untamed-style-transfer-models ~/Downloads/my_art.jpg
```

**Monitoring intervals:** 10s, 10s, 15s, 15s, 20s, 20s, 30s, 30s, 60s, 60s, 120s, 120s, 180s, 180s, 300s... (max 5min)

**Logs:** Saved to `/tmp/training_monitor_TIMESTAMP.log`

## Complete Workflow Example

### Launch and Setup Instance
```bash
# 1. Launch EC2 instance with setup script as userdata
aws ec2 run-instances \
  --image-id ami-0b5ea73381626fce3 \
  --instance-type g4dn.xlarge \
  --key-name memgenie_deploy \
  --security-group-ids sg-198b6e12 \
  --iam-instance-profile Name=EC2-NeuralStyle-Profile \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
  --user-data file://ec2_setup.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=neural-training}]' \
  --query 'Instances[0].[InstanceId,PublicIpAddress]' \
  --output table

# 2. Wait ~5-10 minutes for setup to complete
# Check setup completion:
ssh -i ~/.aws/memgenie_deploy.pem ubuntu@INSTANCE_IP "tail /var/log/setup.log"
# Look for "Setup Complete!"
```

### Train Multiple Models
```bash
# From your local machine, train models sequentially
./monitor_training.sh INSTANCE_IP zebra_fur.jpg 15000 1e10 nav-untamed-style-transfer-models
./monitor_training.sh INSTANCE_IP tiger_fur.jpg 15000 1e10 nav-untamed-style-transfer-models
./monitor_training.sh INSTANCE_IP mandarin_duck.png 40000 5e10 nav-untamed-style-transfer-models
```

### Cleanup
```bash
# Terminate instance when done
aws ec2 terminate-instances --instance-ids INSTANCE_ID

# Download all models from S3
aws s3 sync s3://nav-untamed-style-transfer-models/models/ ./models/
```

## File Locations

**On EC2:**
- Training directory: `/home/ubuntu/neural_style_training/examples/fast_neural_style/`
- Datasets: `/home/ubuntu/neural_style_training/examples/fast_neural_style/data/train_15k/` and `data/train_40k/`
- Models: `/home/ubuntu/neural_style_training/examples/fast_neural_style/models/`
- Training log: `/tmp/training.log`
- Setup log: `/var/log/setup.log`

**On S3:**
- Style images: `s3://BUCKET/style-images/`
- Models: `s3://BUCKET/models/{style-config}/`
  - Example: `s3://BUCKET/models/zebra-fur-15k-default/`

**Locally:**
- Monitor logs: `/tmp/training_monitor_*.log`

## Troubleshooting

### Setup Issues
```bash
# Check setup log
ssh ubuntu@INSTANCE_IP "tail -100 /var/log/setup.log"

# Verify PyTorch installed
ssh ubuntu@INSTANCE_IP "python3 -c 'import torch; print(torch.__version__)'"

# Check datasets
ssh ubuntu@INSTANCE_IP "ls -la /home/ubuntu/neural_style_training/examples/fast_neural_style/data/"
```

### Training Issues
```bash
# Check training log
ssh ubuntu@INSTANCE_IP "tail -100 /tmp/training.log"

# Check GPU
ssh ubuntu@INSTANCE_IP "nvidia-smi"

# Check running processes
ssh ubuntu@INSTANCE_IP "ps aux | grep python"
```

### Manual Training
```bash
# SSH into instance
ssh -i ~/.aws/memgenie_deploy.pem ubuntu@INSTANCE_IP

# Navigate to training directory
cd /home/ubuntu/neural_style_training/examples/fast_neural_style

# Run training directly (foreground)
python3 neural_style/neural_style.py train \
  --dataset data/train_15k \
  --style-image images/style-images/YOUR_STYLE.jpg \
  --style-size 512 \
  --save-model-dir models \
  --epochs 2 \
  --accel \
  --style-weight 1e10 \
  --checkpoint-model-dir models/checkpoints \
  --log-interval 100
```

## Cost Optimization

- **Instance:** g4dn.xlarge @ $0.526/hour
- **Training time:** ~15-20 min per model (15k), ~40-60 min (40k)
- **Cost per model:** ~$0.15-0.20 (15k), ~$0.35-0.50 (40k)
- **Tip:** Keep instance running for multiple sequential trainings
- **Tip:** Terminate immediately after batch completion

## Key Differences from Old Scripts

| Old Approach | New Approach |
|---|---|
| Single monolithic `setup_and_train.sh` | Three focused scripts |
| Breaks when run via userdata | Setup script designed for userdata |
| Training script must be downloaded from GitHub | Training script copied directly from local machine |
| Manual log checking via SSH | Automated monitoring with GPU stats |
| No local logging | Full logs saved locally |
| Hardcoded paths | Flexible parameters |
| No progress visibility | Real-time progress with increasing intervals |

---

**Last Updated:** 2025-10-19
**Author:** Nikolay + Claude
