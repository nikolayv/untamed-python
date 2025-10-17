#!/usr/bin/env python3
"""
Convert PyTorch style transfer models to ONNX format for use in JavaScript.

ONNX can then be used with:
- ONNX.js for browser inference
- TensorFlow.js (after further conversion with onnx-tf)
"""

import torch
import sys
import argparse

sys.path.insert(0, 'examples/fast_neural_style')
from neural_style.transformer_net import TransformerNet


def export_to_onnx(model_path, output_path, image_size=256):
    """
    Export a PyTorch model to ONNX format.

    Args:
        model_path: Path to .pth or .model file
        output_path: Path for output .onnx file
        image_size: Input image size (default 256x256)
    """
    print(f"Loading model: {model_path}")

    # Load model
    model = TransformerNet()
    if model_path.endswith('.model'):
        full_path = f"examples/fast_neural_style/models/{model_path}"
    else:
        full_path = f"examples/fast_neural_style/saved_models/{model_path}"

    state_dict = torch.load(full_path, map_location='cpu', weights_only=True)

    # Remove running_mean and running_var (not needed for inference)
    state_dict = {k: v for k, v in state_dict.items()
                  if not ('running_mean' in k or 'running_var' in k)}

    model.load_state_dict(state_dict, strict=False)
    model.eval()

    print(f"Model loaded. Exporting to ONNX...")

    # Create dummy input (batch_size=1, channels=3, height, width)
    dummy_input = torch.randn(1, 3, image_size, image_size)

    # Export to ONNX
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size', 2: 'height', 3: 'width'},
            'output': {0: 'batch_size', 2: 'height', 3: 'width'}
        }
    )

    print(f"✓ Exported to: {output_path}")

    # Print file size
    import os
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Size: {size_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description='Convert PyTorch model to ONNX')
    parser.add_argument('model', help='Model filename (e.g., candy.pth or epoch_2_*.model)')
    parser.add_argument('-o', '--output', help='Output ONNX path (default: model_name.onnx)')
    parser.add_argument('--size', type=int, default=256, help='Image size (default: 256)')

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        import os
        base_name = os.path.splitext(os.path.basename(args.model))[0]
        output_path = f"{base_name}.onnx"

    export_to_onnx(args.model, output_path, args.size)

    print("\nNext steps:")
    print("1. Use ONNX.js directly in browser:")
    print("   https://github.com/microsoft/onnxjs")
    print("2. Or convert to TensorFlow.js:")
    print("   pip install onnx-tf")
    print("   onnx-tf convert -i model.onnx -o tfjs_model/")


if __name__ == '__main__':
    main()
