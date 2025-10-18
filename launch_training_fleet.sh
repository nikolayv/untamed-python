#!/bin/bash
# Launch multiple EC2 spot instances for parallel training

set -e

# Configuration
INSTANCE_TYPE="g4dn.xlarge"  # NVIDIA T4, $0.16/hr spot
AMI_ID="ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS (us-east-1) - update for your region
KEY_NAME="your-key-name"  # UPDATE THIS
SECURITY_GROUP="your-security-group"  # UPDATE THIS
S3_BUCKET=""  # Optional: S3 bucket name to upload models to

# Remaining style images to train (with public URLs or upload to S3 first)
declare -A STYLES=(
    ["mandarin_duck_plumage_1.png"]="https://your-bucket.s3.amazonaws.com/mandarin_duck_plumage_1.png"
    ["mandarin_duck_nature.jpg"]="https://your-bucket.s3.amazonaws.com/mandarin_duck_nature.jpg"
    ["fawn_fur.jpg"]="https://your-bucket.s3.amazonaws.com/fawn_fur.jpg"
    ["fawn_in_nature_1.jpeg"]="https://your-bucket.s3.amazonaws.com/fawn_in_nature_1.jpeg"
    ["gray_wolf_fur.jpg"]="https://your-bucket.s3.amazonaws.com/gray_wolf_fur.jpg"
    ["gray_wolf_whole.jpg"]="https://your-bucket.s3.amazonaws.com/gray_wolf_whole.jpg"
)

echo "=========================================="
echo "Launching Training Fleet"
echo "=========================================="
echo "Instance type: $INSTANCE_TYPE"
echo "Models to train: ${#STYLES[@]}"
echo ""

# Read the setup script and base64 encode it
SETUP_SCRIPT=$(cat ec2_training_setup.sh | base64)

INSTANCE_IDS=()

# Launch one instance per style
for style_name in "${!STYLES[@]}"; do
    style_url="${STYLES[$style_name]}"

    echo "Launching instance for: $style_name"

    # Create user data that calls the setup script with parameters
    USER_DATA=$(cat <<EOF
#!/bin/bash
echo "$SETUP_SCRIPT" | base64 -d > /tmp/setup.sh
chmod +x /tmp/setup.sh
/tmp/setup.sh "$style_url" "$style_name" "$S3_BUCKET" > /var/log/training.log 2>&1
EOF
)

    # Launch spot instance
    INSTANCE_JSON=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-groups "$SECURITY_GROUP" \
        --instance-market-options "MarketType=spot,SpotOptions={MaxPrice=0.50,SpotInstanceType=one-time}" \
        --user-data "$USER_DATA" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=training-$style_name},{Key=Project,Value=neural-style}]" \
        --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=50,VolumeType=gp3}" \
        --output json)

    INSTANCE_ID=$(echo "$INSTANCE_JSON" | jq -r '.Instances[0].InstanceId')
    INSTANCE_IDS+=("$INSTANCE_ID")

    echo "  Instance ID: $INSTANCE_ID"
    echo ""

    # Small delay to avoid rate limiting
    sleep 2
done

echo "=========================================="
echo "All instances launched!"
echo "=========================================="
echo "Instance IDs:"
printf '%s\n' "${INSTANCE_IDS[@]}"
echo ""
echo "Monitor training:"
echo "  aws ec2 describe-instances --instance-ids ${INSTANCE_IDS[@]}"
echo ""
echo "SSH to instance:"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@<instance-public-ip>"
echo ""
echo "View logs:"
echo "  ssh ubuntu@<ip> tail -f /var/log/training.log"
echo ""
echo "When complete, download models or check S3 bucket: $S3_BUCKET"
