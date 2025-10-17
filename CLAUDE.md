# Claude AI Assistant Guide

## Project Overview

**Untamed** is a real-time neural style transfer application built with PyTorch. It allows users to apply artistic styles to live camera feeds or video files using pre-trained neural networks, with advanced features like model blending, person isolation, and visual effects.

### Core Technologies
- **PyTorch** - Deep learning framework for neural style transfer
- **OpenCV** - Video capture, processing, and display
- **MediaPipe** - Person segmentation for isolation effects
- **MPS (Metal Performance Shaders)** - Hardware acceleration on macOS

### Key Components
- `style_transfer.py` - Interactive real-time application with camera/video playback
- `video_style_transfer.py` - Batch video processing script
- `examples/fast_neural_style/` - PyTorch fast neural style implementation (external dependency)
- Pre-trained models in `saved_models/` (4 base styles) and custom models in `models/` (6 custom styles)

### Architecture Highlights
- **Model Blending**: Supports interpolating 2-3 neural style models by blending their learned weights
- **Person Isolation**: Uses MediaPipe's selfie segmentation to apply styles only to detected people
- **Pulse Distortion**: Radial wave effects that expand from center with configurable speed/amplitude
- **Dual Processing Modes**: Real-time camera mode and video playback with adjustable FPS

## Dependency Management

### CRITICAL: Keep requirements.txt Updated

Whenever you install, update, or remove a Python package in this project, you **MUST** immediately update `/Users/nikolay/src/untamed/requirements.txt`.

#### Process for Adding Dependencies

1. Install the package in the virtual environment:
   ```bash
   source venv/bin/activate
   pip install <package-name>
   ```

2. **Immediately** update `requirements.txt` with the minimum required version:
   ```txt
   # Add a comment explaining why this dependency is needed
   <package-name>>=<major.minor.0>
   ```

3. Test that the requirements file works:
   ```bash
   deactivate
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Process for Removing Dependencies

1. Remove the package:
   ```bash
   pip uninstall <package-name>
   ```

2. **Immediately** remove the line from `requirements.txt`

3. Check for any unused transitive dependencies and consider removing them too

#### Guidelines for requirements.txt

- **Use minimum version constraints** (`>=`) rather than exact versions (`==`) for flexibility
- **Group dependencies** by purpose with comments
- **Include optional dependencies** with clear comments marking them as optional
- **Use major.minor.0** version format (avoid patch versions unless critical)
- **Keep it minimal** - only include direct dependencies, not transitive ones

#### Example Format
```txt
# Core dependencies for neural style transfer
torch>=2.5.0
torchvision>=0.20.0

# Video processing and display
opencv-python>=4.12.0

# Optional: Person segmentation/isolation
mediapipe>=0.10.0
```

### Current Dependencies

As of last update:
- `torch>=2.5.0` - Neural network framework
- `torchvision>=0.20.0` - Pre-trained models and transforms
- `numpy>=1.26.0` - Numerical operations
- `opencv-python>=4.12.0` - Video/camera capture and display
- `Pillow>=11.0.0` - Image loading and processing
- `mediapipe>=0.10.0` - Person segmentation (optional)
- `matplotlib>=3.10.0` - Training visualization and utilities

## Development Workflow

### Setting Up Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
Currently no automated tests exist. Manual testing workflow:
1. Test camera mode: `python style_transfer.py`
2. Test video mode: `python style_transfer.py <video_file>`
3. Test model switching (keys 1-9, a)
4. Test blend modes (press 'm' to cycle through modes)
5. Test effects (p for pulse, h for person isolation)

### Training Custom Models

The project uses PyTorch's fast neural style implementation to train custom style transfer models.

#### Training Overview

**Location**: `examples/fast_neural_style/`
**Training Script**: `train_batch.sh` - Batch trains multiple styles sequentially
**Content Dataset**: `data/train_15k/val2014/` - 15,000 COCO images
**Output**: Models saved to `examples/fast_neural_style/models/` as `.model` files

#### Training Configuration

- **Epochs**: 2 (configured in `train_batch.sh`)
- **Style Size**: 512px
- **Log Interval**: 100 batches
- **Device**: MPS (Metal Performance Shaders) on macOS, CPU fallback
- **Checkpoints**: Saved to `models/checkpoints/` during training

#### How to Train New Models

1. **Add style images** to `examples/fast_neural_style/images/style-images/`
   - Supported formats: JPG, PNG
   - Recommended: High quality, clear pattern/texture images
   - Naming convention: `{animal}_{type}.{ext}` (e.g., `zebra_fur.jpg`, `tiger_whole.jpg`)

2. **Update `train_batch.sh`** with your style image paths:
   ```bash
   STYLES=(
       "images/style-images/your_style_1.jpg"
       "images/style-images/your_style_2.png"
       # ... add more
   )
   ```

3. **Run training**:
   ```bash
   cd examples/fast_neural_style
   ./train_batch.sh
   ```

4. **Monitor progress**: Training logs are saved as `training_{style_name}.log`
   ```bash
   tail -f training_zebra_fur.jpg.log
   ```

#### Training Duration

- **Per model**: ~30-60 minutes (2 epochs on 15k images with MPS)
- **Batch training**: Multiply by number of styles (runs sequentially)
- **Example**: 10 models = ~5-10 hours total

#### After Training

1. **Trained models** are saved as: `epoch_2_{timestamp}_{params}.model`
2. **Add to application**: Update `BASE_MODELS` dict in `style_transfer.py`:
   ```python
   BASE_MODELS = {
       'b': ('epoch_2_2025-10-17_13-43-24_100000.0_10000000000.0.model', 'Zebra Fur', 'images/style-images/zebra_fur.jpg'),
       # key, model_file, display_name, preview_image
   }
   ```

#### Training Tips

- **Pattern vs Whole**: Train both closeup patterns and whole animals for variety
  - Pattern (e.g., `zebra_fur.jpg`): Applies texture/pattern more abstractly
  - Whole (e.g., `zebra_nature.jpg`): Transfers overall colors and composition
- **Image Quality**: Higher quality input = better style transfer results
- **Multiple Variations**: Train 2-3 variations per animal for blending options
- **Style Image Selection**: Choose images with clear, distinctive patterns/colors

#### Troubleshooting Training

- **Out of memory**: Reduce `--style-size` in `train_batch.sh` (default: 512)
- **Slow training**: Check device is using MPS, not CPU
- **Poor results**: Try different style images or increase epochs
- **Model too large**: Models are ~6-7MB each, normal size

## Code Organization

### style_transfer.py Structure
- Lines 1-41: Imports, device setup, model definitions
- Lines 42-66: Style preview image loading
- Lines 67-91: State management (blend mode, effects, segmentation)
- Lines 93-153: Model loading and blending functions
- Lines 155-174: Model update logic
- Lines 176-242: Pulse distortion implementation
- Lines 244-267: Person isolation using MediaPipe
- Lines 269-275: Style transfer core function
- Lines 277-353: Video/camera setup and initialization
- Lines 355-606: Main event loop with keyboard controls

### Key Functions
- `load_model(model_file)` - Load single style transfer model
- `blend_models(file1, file2, alpha)` - 2-model interpolation
- `blend_three_models(file1, file2, file3, weights)` - 3-model barycentric blend
- `stylize_frame(frame)` - Apply neural style transfer to frame
- `apply_pulse_distortion(frame)` - Radial wave effect
- `isolate_person(frame)` - Extract person mask

## Common Tasks

### Adding a New Style Model
1. Train or download a `.pth` or `.model` file
2. Place in `examples/fast_neural_style/saved_models/` or `models/`
3. Add entry to `BASE_MODELS` dict in `style_transfer.py`
4. Add preview image to `examples/fast_neural_style/images/style-images/`

### Adding a New Visual Effect
1. Create function following pattern of `apply_pulse_distortion(frame)`
2. Add toggle state variable (e.g., `effect_enabled = False`)
3. Add keyboard control in main loop
4. Apply effect in rendering pipeline (after stylization)
5. Document in README.md and print controls on startup

### Modifying Model Blending
- 2-model blend: Adjust in `blend_models()` function
- 3-model blend: Adjust in `blend_three_models()` function
- Blend weights are interpolated linearly across all model parameters

## Performance Considerations

- **MPS Device**: Code defaults to Metal Performance Shaders on macOS for GPU acceleration
- **Frame Resolution**: Lower resolution = faster processing. Default is 640x480
- **Model Complexity**: Custom trained models may have different performance characteristics
- **Video Mode**: `PROCESS_EVERY_N_FRAMES` in `video_style_transfer.py` controls batch processing speed

## Important Notes

- **Large Files**: Model files (`.pth`, `.model`) should NOT be committed to git (see `.gitignore`)
- **Person Isolation**: Requires MediaPipe; gracefully degrades if not installed
- **MPS vs CPU**: Code auto-detects and falls back to CPU if MPS unavailable
- **Model Architecture**: Uses `TransformerNet` from fast_neural_style implementation

## Resources

- Fast Neural Style: https://github.com/pytorch/examples/tree/main/fast_neural_style
- MediaPipe Segmentation: https://google.github.io/mediapipe/solutions/selfie_segmentation
- PyTorch MPS: https://pytorch.org/docs/stable/notes/mps.html

---

**Last Updated**: 2025-10-16
**Maintained by**: Human + Claude AI
