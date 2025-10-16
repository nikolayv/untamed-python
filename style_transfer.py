import cv2, torch, sys, time
from torchvision import transforms
from PIL import Image
sys.path.insert(0, 'examples/fast_neural_style')
from neural_style.transformer_net import TransformerNet

device = "mps" if torch.backends.mps.is_available() else "cpu"

# Available style models (single models only for base selection)
BASE_MODELS = {
    '1': ('mosaic.pth', 'Mosaic'),
    '2': ('candy.pth', 'Candy'),
    '3': ('rain_princess.pth', 'Rain Princess'),
    '4': ('udnie.pth', 'Udnie'),
    '5': ('epoch_2_2025-10-15_19-13-34_100000.0_10000000000.0.model', 'Custom Pattern')
}

# Blending state
blend_mode = False
model_a_key = '1'
model_b_key = '2'
blend_alpha = 0.5  # 0.0 = 100% model A, 1.0 = 100% model B

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
    global model
    if blend_mode:
        model = blend_models(BASE_MODELS[model_a_key][0], BASE_MODELS[model_b_key][0], blend_alpha)
    else:
        model = load_model(BASE_MODELS[current_model_key][0])

to_tensor = transforms.ToTensor()
def stylize_frame(frame):
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    t = to_tensor(img).unsqueeze(0).to(device) * 255
    with torch.no_grad():
        out = model(t).cpu()[0].clamp(0,255)
    return cv2.cvtColor(out.permute(1,2,0).byte().numpy(), cv2.COLOR_RGB2BGR)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Verify we can actually read frames
ret, test_frame = cap.read()
if not ret or test_frame is None:
    print("Error: Camera opened but cannot read frames")
    exit(1)

print(f"Camera ready! Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"Actual frame shape: {test_frame.shape}")
print("\n=== CONTROLS ===")
print("Single Mode:")
print("  1-5: Select style (Mosaic/Candy/Rain/Udnie/Custom)")
print("\nBlend Mode:")
print("  b: Toggle blend mode")
print("  a: Select model A (then press 1-5)")
print("  s: Select model B (then press 1-5)")
print("  [/]: Decrease/increase blend (Model A ← → Model B)")
print("  -/+: Large steps (-10%/+10%)")
print("\n  q: Quit")
print(f"\nCurrent: {BASE_MODELS[current_model_key][1]}")

selecting_a = False
selecting_b = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("Warning: Failed to read frame")
        continue

    styled = stylize_frame(frame)

    # Display current mode on frame
    y_pos = 30
    if blend_mode:
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
    elif key == ord('b'):
        blend_mode = not blend_mode
        print(f"\n{'BLEND' if blend_mode else 'SINGLE'} MODE")
        if blend_mode:
            print(f"Model A: {BASE_MODELS[model_a_key][1]}, Model B: {BASE_MODELS[model_b_key][1]}, Blend: {int(blend_alpha*100)}%")
        update_model()
    elif key == ord('a'):
        selecting_a = True
        print("Select Model A (press 1-5):")
    elif key == ord('s'):
        selecting_b = True
        print("Select Model B (press 1-5):")
    elif key == ord('['):  # Decrease blend
        if blend_mode:
            blend_alpha = max(0.0, blend_alpha - 0.05)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif key == ord(']'):  # Increase blend
        if blend_mode:
            blend_alpha = min(1.0, blend_alpha + 0.05)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif key == ord('-') or key == ord('_'):  # Large decrease
        if blend_mode:
            blend_alpha = max(0.0, blend_alpha - 0.1)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif key == ord('+') or key == ord('='):  # Large increase
        if blend_mode:
            blend_alpha = min(1.0, blend_alpha + 0.1)
            print(f"Blend: {int((1-blend_alpha)*100)}% A / {int(blend_alpha*100)}% B")
            update_model()
    elif chr(key) in BASE_MODELS:
        if selecting_a:
            model_a_key = chr(key)
            print(f"Model A set to: {BASE_MODELS[model_a_key][1]}")
            selecting_a = False
            if blend_mode:
                update_model()
        elif selecting_b:
            model_b_key = chr(key)
            print(f"Model B set to: {BASE_MODELS[model_b_key][1]}")
            selecting_b = False
            if blend_mode:
                update_model()
        elif not blend_mode:
            current_model_key = chr(key)
            print(f"Switching to {BASE_MODELS[current_model_key][1]}...")
            update_model()
            print(f"Loaded {BASE_MODELS[current_model_key][1]}")

cap.release()
cv2.destroyAllWindows()
