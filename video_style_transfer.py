import cv2, torch, sys
import numpy as np
from torchvision import transforms
from PIL import Image
sys.path.insert(0, 'examples/fast_neural_style')
from neural_style.transformer_net import TransformerNet

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

# Available style models (model_file, display_name)
BASE_MODELS = {
    '1': ('mosaic.pth', 'Mosaic'),
    '2': ('candy.pth', 'Candy'),
    '3': ('rain_princess.pth', 'Rain Princess'),
    '4': ('udnie.pth', 'Udnie'),
    '5': ('epoch_2_2025-10-16_04-29-41_100000.0_10000000000.0.model', 'Autumn Forest'),
    '6': ('epoch_2_2025-10-16_05-26-24_100000.0_10000000000.0.model', 'Kuker Ritual'),
    '7': ('epoch_2_2025-10-16_06-24-07_100000.0_10000000000.0.model', 'Cave Painting'),
    '8': ('epoch_2_2025-10-16_07-21-54_100000.0_10000000000.0.model', 'Krampus'),
    '9': ('epoch_2_2025-10-16_08-19-42_100000.0_10000000000.0.model', 'Storm King'),
    'a': ('epoch_2_2025-10-16_09-17-25_100000.0_10000000000.0.model', 'Purple Swirl')
}

def load_state_dict(model_file):
    """Load state dict from a model file."""
    if model_file.endswith('.model'):
        model_path = f"examples/fast_neural_style/models/{model_file}"
    else:
        model_path = f"examples/fast_neural_style/saved_models/{model_file}"

    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    # Remove running_mean and running_var from old InstanceNorm2d layers
    state_dict = {k: v for k, v in state_dict.items() if not ('running_mean' in k or 'running_var' in k)}
    return state_dict

def load_model(model_file):
    """Load a single model."""
    model = TransformerNet()
    state_dict = load_state_dict(model_file)
    model.load_state_dict(state_dict, strict=False)
    return model.to(device).eval()

# Configuration
INPUT_VIDEO = "/Users/nikolay/Library/CloudStorage/GoogleDrive-valtchanov@gmail.com/My Drive/Demos/Point Cloud/cloud3.mov"
OUTPUT_VIDEO = "styled_output.mp4"
PROCESS_EVERY_N_FRAMES = 10  # Process every Nth frame (1=all frames, 2=every other frame, etc.)
STYLE_KEY = '7'  # Default to Cave Painting

print(f"\n=== Video Style Transfer ===")
print(f"Input: {INPUT_VIDEO}")
print(f"Output: {OUTPUT_VIDEO}")
print(f"Style: {BASE_MODELS[STYLE_KEY][1]}")
print(f"Processing every {PROCESS_EVERY_N_FRAMES} frame(s)")

# Load the style transfer model
print(f"\nLoading model...", flush=True)
model = load_model(BASE_MODELS[STYLE_KEY][0])
print(f"Model loaded: {BASE_MODELS[STYLE_KEY][1]}", flush=True)

# Open input video
print(f"\nOpening video file...", flush=True)
cap = cv2.VideoCapture(INPUT_VIDEO)
if not cap.isOpened():
    print(f"Error: Cannot open video file: {INPUT_VIDEO}")
    exit(1)

# Get video properties
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = total_frames / fps

print(f"\nVideo info:")
print(f"  Resolution: {width}x{height}")
print(f"  FPS: {fps}")
print(f"  Total frames: {total_frames}")
print(f"  Duration: {duration:.2f}s")
print(f"  Frames to process: {total_frames // PROCESS_EVERY_N_FRAMES}")

# Create video writer
print(f"\nCreating output video writer...", flush=True)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (width, height))
print(f"Output writer ready", flush=True)

# Transform for style transfer
to_tensor = transforms.ToTensor()

def stylize_frame(frame):
    """Apply style transfer to a frame."""
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    t = to_tensor(img).unsqueeze(0).to(device) * 255
    with torch.no_grad():
        styled = model(t).cpu()[0].clamp(0, 255)
    return cv2.cvtColor(styled.permute(1, 2, 0).byte().numpy(), cv2.COLOR_RGB2BGR)

# Process video
print(f"\nProcessing video...", flush=True)
frame_idx = 0
processed_count = 0
last_styled_frame = None

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process every Nth frame
        if frame_idx % PROCESS_EVERY_N_FRAMES == 0:
            if processed_count == 0:
                print(f"Processing first frame...", flush=True)
            last_styled_frame = stylize_frame(frame)
            processed_count += 1

            # Progress update
            if processed_count % 5 == 0:
                progress = (frame_idx / total_frames) * 100
                print(f"  Progress: {progress:.1f}% ({frame_idx}/{total_frames} frames, {processed_count} processed)", flush=True)

        # Write the last styled frame (creates frame duplication for skipped frames)
        if last_styled_frame is not None:
            out.write(last_styled_frame)

        frame_idx += 1

except KeyboardInterrupt:
    print("\n\nInterrupted by user", flush=True)

# Cleanup
cap.release()
out.release()

print(f"\n=== Complete ===")
print(f"Processed {processed_count} frames")
print(f"Output saved to: {OUTPUT_VIDEO}")
print(f"Output duration: {frame_idx / fps:.2f}s")
