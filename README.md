# Untamed - Neural Style Transfer

Real-time neural style transfer application with camera/video support, featuring model blending, person isolation, and pulse distortion effects.

## Features

- **Real-time style transfer** using PyTorch neural style models
- **Dual & Triple model blending** - interpolate between 2-3 style models simultaneously
- **Person isolation** - apply styles only to detected people (requires MediaPipe)
- **Pulse distortion effects** - expanding wave distortions with spacebar trigger
- **Video playback mode** - process and stylize video files
- **10 pre-trained styles** including custom trained models (Autumn Forest, Kuker Ritual, Cave Painting, Krampus, Storm King, Purple Swirl)

## Requirements

- Python 3.11+
- macOS with Metal Performance Shaders (MPS) support, or CPU fallback
- Webcam (for camera mode)

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd untamed
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download pre-trained models (if not already present):
```bash
cd examples/fast_neural_style
python download_saved_models.py
cd ../..
```

## Usage

### Camera Mode (Real-time)
```bash
python style_transfer.py
```

### Video Playback Mode
```bash
python style_transfer.py path/to/video.mp4
```

### Video Processing (Batch)
Edit `video_style_transfer.py` to set input/output paths and style, then:
```bash
python video_style_transfer.py
```

## Controls

### Single Mode (Default)
- `1-9, a` - Select style model

### Dual Blend Mode (press `m` once)
- `a/s` - Select models A/B (then press `1-9, a`)
- `[/]` - Adjust blend ±5%
- `-/+` - Adjust blend ±10%

### Triple Blend Mode (press `m` twice)
- `a/s/d` - Select models A/B/C (then press `1-9, a`)
- `i/k` - Increase/decrease A weight
- `j/l` - Increase/decrease B weight
- `u/o` - Increase/decrease C weight

### Effects
- `p` - Toggle pulse distortion on/off
- `SPACE` - Trigger expanding wave
- `,/.` - Adjust wave speed
- `</>` - Adjust wave amplitude (Shift + `,/.`)
- `h` - Toggle person isolation (requires MediaPipe)

### Video Playback
- `r/f` - Decrease/increase playback FPS

### General
- `m` - Cycle blend modes (single → dual → triple)
- `q` - Quit

## Project Structure

```
untamed/
├── style_transfer.py          # Main interactive application
├── video_style_transfer.py    # Batch video processing script
├── requirements.txt            # Python dependencies
├── examples/
│   └── fast_neural_style/     # PyTorch fast neural style implementation
│       ├── saved_models/      # Pre-trained models (.pth files)
│       ├── models/            # Custom trained models (.model files)
│       └── neural_style/      # Model architecture
└── venv/                      # Virtual environment
```

## Training Custom Models

See `examples/fast_neural_style/README.md` for training instructions. Use `train_batch.sh` for batch training multiple styles.

## Architecture Notes

See `EFFECTS_ARCHITECTURE.md` for detailed information about the visual effects implementation (pulse distortions, person isolation, etc.).

## License

See `examples/fast_neural_style/LICENSE` for the neural style transfer implementation license.
