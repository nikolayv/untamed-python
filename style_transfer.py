import cv2, torch
from torchvision import transforms
from PIL import Image

device = "mps" if torch.backends.mps.is_available() else "cpu"
model = torch.jit.load("saved_models/mosaic.pth", map_location=device).to(device).eval()

to_tensor = transforms.ToTensor()
def stylize_frame(frame):
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    t = to_tensor(img).unsqueeze(0).to(device) * 255
    with torch.no_grad():
        out = model(t).cpu()[0].clamp(0,255)
    return cv2.cvtColor(out.permute(1,2,0).byte().numpy(), cv2.COLOR_RGB2BGR)

cap = cv2.VideoCapture(0)
cap.set(3, 640); cap.set(4, 480)
while True:
    ret, frame = cap.read()
    if not ret: break
    styled = stylize_frame(frame)
    cv2.imshow("Stylized", styled)
    if cv2.waitKey(1) & 0xFF == ord('q'): break
cap.release(); cv2.destroyAllWindows()
