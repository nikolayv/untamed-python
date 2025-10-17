# Converting Models to JavaScript

This guide explains how to convert PyTorch style transfer models to formats usable in JavaScript/browser environments.

## Quick Start

Convert any model to ONNX format:

```bash
# Convert base models
python3 convert_to_onnx.py candy.pth
python3 convert_to_onnx.py mosaic.pth

# Convert custom trained models
python3 convert_to_onnx.py epoch_2_2025-10-17_15-09-22_100000.0_10000000000.0.model
```

Output: `candy.onnx` (6.5 MB)

## Model Format Details

**PyTorch Model:**
- Architecture: TransformerNet CNN
- Parameters: 92 layers
- Weights: 1.68 million
- Size: 6.4 MB (.pth/.model)

**ONNX Model:**
- Same architecture, converted to ONNX format
- Size: 6.5 MB (.onnx)
- Opset version: 11
- Dynamic input/output dimensions

## Using ONNX Models in JavaScript

### Option 1: ONNX Runtime Web (Recommended)

ONNX Runtime Web provides WebAssembly and WebGL backends for fast inference:

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/ort.min.js"></script>
</head>
<body>
  <canvas id="input"></canvas>
  <canvas id="output"></canvas>

  <script>
    async function runModel() {
      // Load model
      const session = await ort.InferenceSession.create('candy.onnx');

      // Prepare input (1, 3, 256, 256) - NCHW format
      const canvas = document.getElementById('input');
      const ctx = canvas.getContext('2d');
      const imageData = ctx.getImageData(0, 0, 256, 256);

      // Convert RGBA to RGB and normalize to [0, 255]
      const input = new Float32Array(1 * 3 * 256 * 256);
      for (let i = 0; i < 256 * 256; i++) {
        input[i] = imageData.data[i * 4];           // R
        input[i + 256*256] = imageData.data[i * 4 + 1];     // G
        input[i + 256*256*2] = imageData.data[i * 4 + 2];   // B
      }

      // Run inference
      const tensor = new ort.Tensor('float32', input, [1, 3, 256, 256]);
      const results = await session.run({ input: tensor });

      // Process output
      const output = results.output.data;

      // Convert back to canvas (clamp to 0-255)
      const outputData = new Uint8ClampedArray(256 * 256 * 4);
      for (let i = 0; i < 256 * 256; i++) {
        outputData[i * 4] = output[i];                  // R
        outputData[i * 4 + 1] = output[i + 256*256];    // G
        outputData[i * 4 + 2] = output[i + 256*256*2];  // B
        outputData[i * 4 + 3] = 255;                    // A
      }

      const outCanvas = document.getElementById('output');
      const outCtx = outCanvas.getContext('2d');
      outCtx.putImageData(new ImageData(outputData, 256, 256), 0, 0);
    }

    runModel();
  </script>
</body>
</html>
```

### Option 2: TensorFlow.js

Convert ONNX to TensorFlow.js format:

```bash
# Install converter
pip install onnx-tf tensorflow

# Convert to TensorFlow SavedModel
onnx-tf convert -i candy.onnx -o candy_tf/

# Convert to TensorFlow.js
pip install tensorflowjs
tensorflowjs_converter --input_format=tf_saved_model \
  candy_tf/ \
  candy_tfjs/
```

Then use in JavaScript:

```javascript
import * as tf from '@tensorflow/tfjs';

// Load model
const model = await tf.loadGraphModel('candy_tfjs/model.json');

// Prepare input (1, 256, 256, 3) - NHWC format for TF.js
const img = tf.browser.fromPixels(imageElement);
const input = img.expandDims(0);

// Run inference
const output = model.predict(input);

// Display
tf.browser.toPixels(output.squeeze(), canvas);
```

## Performance Considerations

**Browser Performance:**
- WebGL backend: ~30-60ms per frame (256x256) on modern GPUs
- WebAssembly: ~200-500ms per frame (CPU fallback)
- Model size: 6.5 MB (one-time download, cacheable)

**Optimization Tips:**
1. Use WebGL/WebGPU backend when available
2. Process video at lower resolution (256x256 or 512x512)
3. Cache model weights in browser storage
4. Consider quantization for smaller models

## Model Input/Output

**Input:**
- Shape: `(batch, 3, height, width)` - NCHW format for ONNX
- Type: Float32
- Range: [0, 255] (pixel values, not normalized)
- Channels: RGB order

**Output:**
- Shape: `(batch, 3, height, width)` - NCHW format for ONNX
- Type: Float32
- Range: [0, 255] (clip values outside this range)
- Channels: RGB order

## Troubleshooting

**Issue: Model too large for browser**
- Try quantization: `python3 -m onnxruntime.quantization.preprocess --input candy.onnx --output candy_quant.onnx`

**Issue: Slow inference**
- Use WebGL backend
- Reduce input resolution
- Use Web Workers for async processing

**Issue: Colors look wrong**
- Check RGB vs BGR ordering
- Verify normalization (should be [0, 255], not [0, 1])

## Resources

- ONNX Runtime Web: https://onnxruntime.ai/docs/tutorials/web/
- TensorFlow.js: https://www.tensorflow.org/js
- Example implementations: https://github.com/microsoft/onnxjs-demo

## Converting All Models

Convert all base models at once:

```bash
for model in examples/fast_neural_style/saved_models/*.pth; do
  python3 convert_to_onnx.py $(basename $model)
done
```

Convert all trained models:

```bash
for model in examples/fast_neural_style/models/*.model; do
  python3 convert_to_onnx.py $(basename $model) -o $(basename $model .model).onnx
done
```
