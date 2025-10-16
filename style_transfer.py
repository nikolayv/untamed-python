import cv2, torch, sys, time
from torchvision import transforms
from PIL import Image
sys.path.insert(0, 'examples/fast_neural_style')
from neural_style.transformer_net import TransformerNet

device = "mps" if torch.backends.mps.is_available() else "cpu"

# Available style models
MODELS = {
    '1': ('mosaic.pth', 'Mosaic'),
    '2': ('candy.pth', 'Candy'),
    '3': ('rain_princess.pth', 'Rain Princess'),
    '4': ('udnie.pth', 'Udnie'),
    '5': ('epoch_2_2025-10-15_19-13-34_100000.0_10000000000.0.model', 'Custom Pattern')
}

def load_model(model_file):
    model = TransformerNet()
    # Check if it's a custom trained model or pre-trained model
    if model_file.endswith('.model'):
        model_path = f"examples/fast_neural_style/models/{model_file}"
    else:
        model_path = f"examples/fast_neural_style/saved_models/{model_file}"

    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    # Remove running_mean and running_var from old InstanceNorm2d layers
    state_dict = {k: v for k, v in state_dict.items() if not ('running_mean' in k or 'running_var' in k)}
    model.load_state_dict(state_dict, strict=False)
    return model.to(device).eval()

# Load initial model
current_model_key = '1'
model = load_model(MODELS[current_model_key][0])

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
print("\nControls:")
print("  1 - Mosaic style")
print("  2 - Candy style")
print("  3 - Rain Princess style")
print("  4 - Udnie style")
print("  5 - Custom Pattern style (your trained model!)")
print("  q - Quit")
print(f"\nCurrent style: {MODELS[current_model_key][1]}")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Warning: Failed to read frame")
        continue

    styled = stylize_frame(frame)

    # Add current style name to the frame
    cv2.putText(styled, f"Style: {MODELS[current_model_key][1]}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Style Transfer", styled)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif chr(key) in MODELS:
        new_key = chr(key)
        if new_key != current_model_key:
            current_model_key = new_key
            print(f"Switching to {MODELS[current_model_key][1]}...")
            model = load_model(MODELS[current_model_key][0])
            print(f"Loaded {MODELS[current_model_key][1]}")

cap.release()
cv2.destroyAllWindows()
