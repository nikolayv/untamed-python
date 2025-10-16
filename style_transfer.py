import cv2, torch, sys, time
import numpy as np
from torchvision import transforms
from PIL import Image
sys.path.insert(0, 'examples/fast_neural_style')
from neural_style.transformer_net import TransformerNet

device = "mps" if torch.backends.mps.is_available() else "cpu"

# Check for video file argument
VIDEO_FILE = None
VIDEO_FPS = 2  # Initial playback fps for video mode
if len(sys.argv) > 1:
    VIDEO_FILE = sys.argv[1]
    print(f"Video playback mode: {VIDEO_FILE}")
else:
    print("Camera mode (use: python style_transfer.py <video_file> for video playback)")

# Available style models (model_file, display_name, style_image_path)
BASE_MODELS = {
    '1': ('mosaic.pth', 'Mosaic', 'examples/fast_neural_style/images/style-images/mosaic.jpg'),
    '2': ('candy.pth', 'Candy', 'examples/fast_neural_style/images/style-images/candy.jpg'),
    '3': ('rain_princess.pth', 'Rain Princess', 'examples/fast_neural_style/images/style-images/rain_princess.jpg'),
    '4': ('udnie.pth', 'Udnie', 'examples/fast_neural_style/images/style-images/udnie.jpg'),
    '5': ('epoch_2_2025-10-16_04-29-41_100000.0_10000000000.0.model', 'Autumn Forest', 'examples/fast_neural_style/images/style-images/Autumn Forest Sunset.jpg'),
    '6': ('epoch_2_2025-10-16_05-26-24_100000.0_10000000000.0.model', 'Kuker Ritual', 'examples/fast_neural_style/images/style-images/Bulgarian Kuker Rituals.jpg'),
    '7': ('epoch_2_2025-10-16_06-24-07_100000.0_10000000000.0.model', 'Cave Painting', 'examples/fast_neural_style/images/style-images/hunters_cave_painting.png'),
    '8': ('epoch_2_2025-10-16_07-21-54_100000.0_10000000000.0.model', 'Krampus', 'examples/fast_neural_style/images/style-images/Krampus Morzger Pass Salzburg Oct 2008.jpg'),
    '9': ('epoch_2_2025-10-16_08-19-42_100000.0_10000000000.0.model', 'Storm King', 'examples/fast_neural_style/images/style-images/Storm King Alexander Calder.jpg'),
    'a': ('epoch_2_2025-10-16_09-17-25_100000.0_10000000000.0.model', 'Purple Swirl', 'examples/fast_neural_style/images/style-images/purple_swirly.png')
}

# Load style preview images
style_previews = {}
preview_size = 100
for key, (_, name, img_path) in BASE_MODELS.items():
    img = cv2.imread(img_path)
    if img is not None:
        # Resize to square preview
        h, w = img.shape[:2]
        if h > w:
            new_h, new_w = preview_size, int(w * preview_size / h)
        else:
            new_h, new_w = int(h * preview_size / w), preview_size
        resized = cv2.resize(img, (new_w, new_h))
        # Center crop to square
        y_offset = (new_h - preview_size) // 2 if new_h > preview_size else 0
        x_offset = (new_w - preview_size) // 2 if new_w > preview_size else 0
        if new_h >= preview_size and new_w >= preview_size:
            style_previews[key] = resized[y_offset:y_offset+preview_size, x_offset:x_offset+preview_size]
        else:
            # Pad to square if smaller
            padded = np.zeros((preview_size, preview_size, 3), dtype=np.uint8)
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            style_previews[key] = padded

# Blending state
blend_mode = 0  # 0=single, 2=dual blend, 3=triple blend
model_a_key = '1'
model_b_key = '2'
model_c_key = '3'
blend_alpha = 0.5  # For 2-model blend: 0.0 = 100% model A, 1.0 = 100% model B

# 3-model blend weights (barycentric coordinates - always sum to 1.0)
blend_weights = [0.33, 0.33, 0.34]  # [weight_a, weight_b, weight_c]

# Visual effects state
pulse_enabled = False

# Pulse distortion parameters - track multiple waves
active_waves = []  # List of {birth_time: frame_count, amplitude: pixels}
pulse_amplitude = 35  # max displacement in pixels
pulse_speed = 50  # pixels per frame that wave expands
pulse_width = 30  # width of each wave
frame_count = 0

def load_state_dict(model_file):
    """Load state dict from a model file."""
    # Check if it's a custom trained model or pre-trained model
    if model_file.endswith('.model'):
        model_path = f"examples/fast_neural_style/models/{model_file}"
    else:
        model_path = f"examples/fast_neural_style/saved_models/{model_file}"

    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    # Remove running_mean and running_var from old InstanceNorm2d layers
    state_dict = {k: v for k, v in state_dict.items() if not ('running_mean' in k or 'running_var' in k)}
    return state_dict

def blend_models(model_file1, model_file2, alpha=0.5):
    """Blend two models with interpolation factor alpha (0=model1, 1=model2)."""
    sd1 = load_state_dict(model_file1)
    sd2 = load_state_dict(model_file2)

    # Interpolate weights
    blended = {}
    for key in sd1.keys():
        if key in sd2:
            blended[key] = (1 - alpha) * sd1[key] + alpha * sd2[key]
        else:
            blended[key] = sd1[key]

    # Load into model
    model = TransformerNet()
    model.load_state_dict(blended, strict=False)
    return model.to(device).eval()

def blend_three_models(model_file1, model_file2, model_file3, weights):
    """Blend three models with barycentric coordinates (weights sum to 1.0)."""
    sd1 = load_state_dict(model_file1)
    sd2 = load_state_dict(model_file2)
    sd3 = load_state_dict(model_file3)

    # Normalize weights to ensure they sum to 1.0
    total = sum(weights)
    w1, w2, w3 = [w/total for w in weights]

    # Interpolate weights
    blended = {}
    for key in sd1.keys():
        blended[key] = w1 * sd1[key]
        if key in sd2:
            blended[key] += w2 * sd2[key]
        if key in sd3:
            blended[key] += w3 * sd3[key]

    # Load into model
    model = TransformerNet()
    model.load_state_dict(blended, strict=False)
    return model.to(device).eval()

def load_model(model_file):
    """Load a single model."""
    model = TransformerNet()
    state_dict = load_state_dict(model_file)
    model.load_state_dict(state_dict, strict=False)
    return model.to(device).eval()

# Load initial model
current_model_key = '1'
model = load_model(BASE_MODELS[current_model_key][0])

def update_model():
    """Update the current model based on blend mode."""
    global model, last_styled_frame
    if blend_mode == 3:
        model = blend_three_models(
            BASE_MODELS[model_a_key][0],
            BASE_MODELS[model_b_key][0],
            BASE_MODELS[model_c_key][0],
            blend_weights
        )
    elif blend_mode == 2:
        model = blend_models(BASE_MODELS[model_a_key][0], BASE_MODELS[model_b_key][0], blend_alpha)
    else:
        model = load_model(BASE_MODELS[current_model_key][0])
    # Invalidate cached frame so next frame gets re-styled
    last_styled_frame = None

def trigger_wave():
    """Trigger a new expanding wave."""
    global active_waves, frame_count
    active_waves.append({
        'birth_time': frame_count,
        'amplitude': pulse_amplitude
    })
    print(f"Wave triggered! Active waves: {len(active_waves)}")

def apply_pulse_distortion(frame):
    """Apply radial pulse distortion with multiple expanding waves."""
    global frame_count, active_waves

    if not pulse_enabled or len(active_waves) == 0:
        return frame

    h, w = frame.shape[:2]
    center_x, center_y = w // 2, h // 2

    # Create coordinate meshgrid
    y, x = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')

    # Calculate distance from center for each pixel
    dx = x - center_x
    dy = y - center_y
    distance = np.sqrt(dx**2 + dy**2)

    # Accumulate displacement from all active waves
    total_displacement = np.zeros_like(distance)

    waves_to_remove = []
    max_distance = np.sqrt(center_x**2 + center_y**2)

    for i, wave in enumerate(active_waves):
        age = frame_count - wave['birth_time']
        wave_radius = age * pulse_speed

        # Calculate how far each pixel is from the wave front
        distance_from_wave = np.abs(distance - wave_radius)

        # Wave has a certain width - only affect pixels near the wave front
        wave_influence = np.exp(-distance_from_wave**2 / (pulse_width**2 / 2))

        # Displacement magnitude (radial push/pull)
        displacement = wave_influence * wave['amplitude']

        total_displacement += displacement

        # Remove waves that have traveled beyond the frame
        if wave_radius > max_distance + pulse_width:
            waves_to_remove.append(i)

    # Remove expired waves
    for i in reversed(waves_to_remove):
        active_waves.pop(i)

    # Apply displacement radially
    angle = np.arctan2(dy, dx)
    map_x = (x + total_displacement * np.cos(angle)).astype(np.float32)
    map_y = (y + total_displacement * np.sin(angle)).astype(np.float32)

    # Remap pixels according to distortion
    distorted = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    frame_count += 1

    return distorted

to_tensor = transforms.ToTensor()
def stylize_frame(frame):
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    t = to_tensor(img).unsqueeze(0).to(device) * 255
    with torch.no_grad():
        out = model(t).cpu()[0].clamp(0,255)
    return cv2.cvtColor(out.permute(1,2,0).byte().numpy(), cv2.COLOR_RGB2BGR)

# Target resolution for processing
TARGET_WIDTH = 640
TARGET_HEIGHT = 480

# Open video source (file or camera)
if VIDEO_FILE:
    cap = cv2.VideoCapture(VIDEO_FILE)
    if not cap.isOpened():
        print(f"Error: Cannot open video file: {VIDEO_FILE}")
        exit(1)

    # Get video properties
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Video FPS: {source_fps}")
    print(f"Total frames: {total_frames}, Duration: {total_frames/source_fps:.1f}s")
    print(f"Original resolution: {orig_width}x{orig_height}, will resize to {TARGET_WIDTH}x{TARGET_HEIGHT} for processing")

    # Calculate frame skip based on VIDEO_FPS
    frame_skip = max(1, int(source_fps / VIDEO_FPS))
    print(f"Initial playback: {VIDEO_FPS} fps (processing every {frame_skip} frames)")
else:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_HEIGHT)
    frame_skip = 1  # Process every frame in camera mode

# Verify we can actually read frames
ret, test_frame = cap.read()
if not ret or test_frame is None:
    print("Error: Cannot read frames from source")
    exit(1)

print(f"Ready! Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"Frame shape: {test_frame.shape}")
print("\n=== CONTROLS ===")
print("Single Mode (default):")
print("  1-9,a: Select style (10 models available)")
print("\nDual Blend (press 'm' once):")
print("  a/s: Select models A/B (then 1-9,a)")
print("  [/]: Adjust blend ±5%")
print("  -/+: Adjust blend ±10%")
print("\nTriple Blend (press 'm' twice) - 3D CONTROL:")
print("  a/s/d: Select models A/B/C (then 1-9,a)")
print("  i/k: Increase/decrease A weight")
print("  j/l: Increase/decrease B weight")
print("  u/o: Increase/decrease C weight")
print("  (Weights auto-normalize to 100%)")
print("\nPulse Distortion:")
print("  p: Toggle pulse effect on/off")
print("  SPACE: Trigger wave (creates expanding distortion)")
print("  ,/.: Adjust wave speed")
print("  </> (shift+,/.): Adjust wave amplitude")
if VIDEO_FILE:
    print("\nVideo Playback:")
    print("  r/f: Decrease/increase playback FPS")
print("\n  m: Cycle blend modes (single→dual→triple)")
print("  q: Quit")
print(f"\nCurrent: {BASE_MODELS[current_model_key][1]}")

selecting_a = False
selecting_b = False
selecting_c = False

frame_idx = 0
last_styled_frame = None

while True:
    # For video mode, skip ahead to the next frame we want to process
    if VIDEO_FILE and frame_idx > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

    ret, frame = cap.read()
    if not ret:
        if VIDEO_FILE:
            # Loop video
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_idx = 0
            last_styled_frame = None
            continue
        else:
            print("Warning: Failed to read frame")
            continue

    # Resize video frames to target resolution for faster processing
    if VIDEO_FILE:
        frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))

    # Process the frame
    styled = stylize_frame(frame)
    last_styled_frame = styled

    # Advance frame index by skip amount for video, or by 1 for camera
    frame_idx += frame_skip

    # Apply pulse distortion if enabled
    styled = apply_pulse_distortion(styled)

    # Display style preview(s) in corner
    h, w = styled.shape[:2]
    margin = 10
    if blend_mode == 3:
        # Show all three model previews stacked vertically
        preview_keys = [model_a_key, model_b_key, model_c_key]
        colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]  # RGB colors for borders
        for i, (key, color) in enumerate(zip(preview_keys, colors)):
            if key in style_previews:
                preview = style_previews[key]
                x_offset = w - preview_size - margin
                y_offset = margin + i * (preview_size + 5)
                # Draw border
                cv2.rectangle(styled, (x_offset-2, y_offset-2),
                             (x_offset+preview_size+2, y_offset+preview_size+2), color, 2)
                # Place preview
                styled[y_offset:y_offset+preview_size, x_offset:x_offset+preview_size] = preview
    elif blend_mode == 2:
        # Show both model previews side by side
        preview_keys = [model_a_key, model_b_key]
        for i, key in enumerate(preview_keys):
            if key in style_previews:
                preview = style_previews[key]
                x_offset = w - (2 - i) * (preview_size + 5) - margin
                y_offset = margin
                # Draw border
                cv2.rectangle(styled, (x_offset-2, y_offset-2),
                             (x_offset+preview_size+2, y_offset+preview_size+2), (255, 255, 255), 2)
                # Place preview
                styled[y_offset:y_offset+preview_size, x_offset:x_offset+preview_size] = preview
    else:
        # Show single model preview
        if current_model_key in style_previews:
            preview = style_previews[current_model_key]
            x_offset = w - preview_size - margin
            y_offset = margin
            # Draw border
            cv2.rectangle(styled, (x_offset-2, y_offset-2),
                         (x_offset+preview_size+2, y_offset+preview_size+2), (255, 255, 255), 2)
            # Place preview
            styled[y_offset:y_offset+preview_size, x_offset:x_offset+preview_size] = preview

    # Display current mode on frame
    y_pos = 30
    if blend_mode == 3:
        # Triple blend - show all three with bar graph
        w1, w2, w3 = [int(w*100) for w in blend_weights]
        name_a = BASE_MODELS[model_a_key][1][:8]
        name_b = BASE_MODELS[model_b_key][1][:8]
        name_c = BASE_MODELS[model_c_key][1][:8]

        text = f"3D BLEND: {name_a}:{w1}% {name_b}:{w2}% {name_c}:{w3}%"
        cv2.putText(styled, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Visual bar for each model
        bar_y = y_pos + 30
        bar_width = 200
        cv2.rectangle(styled, (10, bar_y), (10 + int(bar_width * blend_weights[0]), bar_y + 10), (255, 100, 100), -1)
        cv2.rectangle(styled, (10, bar_y + 15), (10 + int(bar_width * blend_weights[1]), bar_y + 25), (100, 255, 100), -1)
        cv2.rectangle(styled, (10, bar_y + 30), (10 + int(bar_width * blend_weights[2]), bar_y + 40), (100, 100, 255), -1)

    elif blend_mode == 2:
        model_a_name = BASE_MODELS[model_a_key][1]
        model_b_name = BASE_MODELS[model_b_key][1]
        blend_pct = int(blend_alpha * 100)
        text = f"BLEND: {model_a_name} {100-blend_pct}% | {blend_pct}% {model_b_name}"
        cv2.putText(styled, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    else:
        cv2.putText(styled, f"Style: {BASE_MODELS[current_model_key][1]}", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Style Transfer", styled)

    key = cv2.waitKey(1) & 0xFF
    if key == 255:  # No key pressed
        continue

    if key == ord('q'):
        break
    elif key == ord('m'):
        blend_mode = (blend_mode + 1) % 4  # 0→1→2→3→0, but skip 1
        if blend_mode == 1:
            blend_mode = 2  # Skip to dual blend
        mode_names = {0: "SINGLE", 2: "DUAL BLEND", 3: "TRIPLE BLEND (3D)"}
        print(f"\n{mode_names[blend_mode]} MODE")
        if blend_mode == 2:
            print(f"A: {BASE_MODELS[model_a_key][1]}, B: {BASE_MODELS[model_b_key][1]}, Blend: {int(blend_alpha*100)}%")
        elif blend_mode == 3:
            w1, w2, w3 = [int(w*100) for w in blend_weights]
            print(f"A: {BASE_MODELS[model_a_key][1]} {w1}%")
            print(f"B: {BASE_MODELS[model_b_key][1]} {w2}%")
            print(f"C: {BASE_MODELS[model_c_key][1]} {w3}%")
        update_model()
    elif key == ord('a') and blend_mode > 0:
        selecting_a = True
        print("Select Model A (press 1-9,a):")
    elif key == ord('s') and blend_mode > 0:
        selecting_b = True
        print("Select Model B (press 1-9,a):")
    elif key == ord('d'):
        if blend_mode == 3:
            selecting_c = True
            print("Select Model C (press 1-9,a):")
    # 3D blend controls (model A/B/C weights)
    elif key == ord('i'):  # Increase A
        if blend_mode == 3:
            blend_weights[0] = min(1.0, blend_weights[0] + 0.05)
            print(f"Weights: A={int(blend_weights[0]*100)}% B={int(blend_weights[1]*100)}% C={int(blend_weights[2]*100)}%")
            update_model()
    elif key == ord('k'):  # Decrease A
        if blend_mode == 3:
            blend_weights[0] = max(0.0, blend_weights[0] - 0.05)
            print(f"Weights: A={int(blend_weights[0]*100)}% B={int(blend_weights[1]*100)}% C={int(blend_weights[2]*100)}%")
            update_model()
    elif key == ord('j'):  # Decrease B
        if blend_mode == 3:
            blend_weights[1] = max(0.0, blend_weights[1] - 0.05)
            print(f"Weights: A={int(blend_weights[0]*100)}% B={int(blend_weights[1]*100)}% C={int(blend_weights[2]*100)}%")
            update_model()
    elif key == ord('l'):  # Increase B
        if blend_mode == 3:
            blend_weights[1] = min(1.0, blend_weights[1] + 0.05)
            print(f"Weights: A={int(blend_weights[0]*100)}% B={int(blend_weights[1]*100)}% C={int(blend_weights[2]*100)}%")
            update_model()
    elif key == ord('u'):  # Decrease C
        if blend_mode == 3:
            blend_weights[2] = max(0.0, blend_weights[2] - 0.05)
            print(f"Weights: A={int(blend_weights[0]*100)}% B={int(blend_weights[1]*100)}% C={int(blend_weights[2]*100)}%")
            update_model()
    elif key == ord('o'):  # Increase C
        if blend_mode == 3:
            blend_weights[2] = min(1.0, blend_weights[2] + 0.05)
            print(f"Weights: A={int(blend_weights[0]*100)}% B={int(blend_weights[1]*100)}% C={int(blend_weights[2]*100)}%")
            update_model()
    # 2D blend controls
    elif key == ord('['):  # Decrease blend
        if blend_mode == 2:
            blend_alpha = max(0.0, blend_alpha - 0.05)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif key == ord(']'):  # Increase blend
        if blend_mode == 2:
            blend_alpha = min(1.0, blend_alpha + 0.05)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif key == ord('-') or key == ord('_'):  # Large decrease
        if blend_mode == 2:
            blend_alpha = max(0.0, blend_alpha - 0.1)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif key == ord('+') or key == ord('='):  # Large increase
        if blend_mode == 2:
            blend_alpha = min(1.0, blend_alpha + 0.1)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    # Pulse distortion controls
    elif key == ord('p'):
        pulse_enabled = not pulse_enabled
        if not pulse_enabled:
            active_waves.clear()
        print(f"Pulse distortion: {'ON' if pulse_enabled else 'OFF'}")
    elif key == ord(' '):  # Spacebar - trigger wave
        if pulse_enabled:
            trigger_wave()
    elif key == ord(','):  # Decrease speed
        pulse_speed = max(1, pulse_speed - 0.5)
        print(f"Wave speed: {pulse_speed}px/frame")
    elif key == ord('.'):  # Increase speed
        pulse_speed = min(50, pulse_speed + 0.5)
        print(f"Wave speed: {pulse_speed}px/frame")
    elif key == ord('<'):  # Decrease amplitude
        pulse_amplitude = max(5, pulse_amplitude - 2)
        print(f"Wave amplitude: {pulse_amplitude}px")
    elif key == ord('>'):  # Increase amplitude
        pulse_amplitude = min(50, pulse_amplitude + 2)
        print(f"Wave amplitude: {pulse_amplitude}px")
    # Video playback speed controls
    elif key == ord('r'):  # Decrease FPS
        if VIDEO_FILE:
            VIDEO_FPS = max(1, VIDEO_FPS - 1)
            frame_skip = max(1, int(source_fps / VIDEO_FPS))
            print(f"Playback FPS: {VIDEO_FPS} (processing every {frame_skip} frames)")
    elif key == ord('f'):  # Increase FPS
        if VIDEO_FILE:
            VIDEO_FPS = min(int(source_fps), VIDEO_FPS + 1)
            frame_skip = max(1, int(source_fps / VIDEO_FPS))
            print(f"Playback FPS: {VIDEO_FPS} (processing every {frame_skip} frames)")
    elif chr(key) in BASE_MODELS:
        if selecting_a:
            model_a_key = chr(key)
            print(f"Model A set to: {BASE_MODELS[model_a_key][1]}")
            selecting_a = False
            if blend_mode > 0:
                update_model()
        elif selecting_b:
            model_b_key = chr(key)
            print(f"Model B set to: {BASE_MODELS[model_b_key][1]}")
            selecting_b = False
            if blend_mode > 0:
                update_model()
        elif selecting_c:
            model_c_key = chr(key)
            print(f"Model C set to: {BASE_MODELS[model_c_key][1]}")
            selecting_c = False
            if blend_mode == 3:
                update_model()
        elif blend_mode == 0:
            current_model_key = chr(key)
            print(f"Switching to {BASE_MODELS[current_model_key][1]}...")
            update_model()
            print(f"Loaded {BASE_MODELS[current_model_key][1]}")

cap.release()
cv2.destroyAllWindows()
