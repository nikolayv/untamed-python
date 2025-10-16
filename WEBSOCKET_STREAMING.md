# WebSocket Streaming Setup

This document describes how to stream styled video from the Python application to a web client (Next.js/React) for display on a canvas via Three.js or standard HTML5 video elements.

## Overview

The streaming system consists of:
1. **Python WebSocket Server** (`websocket_stream.py`) - Captures video, applies neural style transfer, and streams JPEG frames
2. **Web Client** (React/Next.js) - Connects via WebSocket and displays frames

## Architecture

```
┌─────────────────────┐        WebSocket         ┌──────────────────┐
│  Python Server      │◄──────────────────────────┤  Web Client      │
│  websocket_stream.py│                           │  (Next.js/React) │
│                     │    JSON + Base64 JPEG     │                  │
│  - Video Capture    ├──────────────────────────►│  - Display       │
│  - Style Transfer   │                           │  - Three.js      │
│  - JPEG Encoding    │                           │    or <img>      │
└─────────────────────┘                           └──────────────────┘
```

## Python Server Setup

### 1. Install Dependencies

```bash
source venv/bin/activate
pip install websockets
# Or install all dependencies:
pip install -r requirements.txt
```

### 2. Run the Server

**Stream from camera (default):**
```bash
python websocket_stream.py --fps 10
```

**Stream from video file:**
```bash
python websocket_stream.py path/to/video.mp4 --fps 5
```

**Custom configuration:**
```bash
python websocket_stream.py \
  --host 0.0.0.0 \
  --port 8765 \
  --fps 10 \
  --style 7 \
  --width 640 \
  --height 480 \
  --quality 80
```

### 3. Server Options

| Option | Description | Default |
|--------|-------------|---------|
| `video` | Video file path (omit for camera) | Camera |
| `--host` | Server host address | localhost |
| `--port` | WebSocket port | 8765 |
| `--fps` | Target frame rate | 10 |
| `--style` | Style key (1-9, a) | 7 (Cave Painting) |
| `--width` | Output frame width | 640 |
| `--height` | Output frame height | 480 |
| `--quality` | JPEG quality (1-100) | 80 |

### 4. Available Styles

| Key | Style Name |
|-----|------------|
| 1 | Mosaic |
| 2 | Candy |
| 3 | Rain Princess |
| 4 | Udnie |
| 5 | Autumn Forest |
| 6 | Kuker Ritual |
| 7 | Cave Painting |
| 8 | Krampus |
| 9 | Storm King |
| a | Purple Swirl |

## Web Client Setup (Next.js/React)

### 1. Copy Client Code

Copy `client_example.tsx` to your Next.js project:
```bash
cp client_example.tsx /path/to/nextjs-app/components/VideoStream.tsx
```

### 2. Basic Usage (HTML5 Image)

```tsx
// app/stream/page.tsx
'use client'

import { VideoStream } from '@/components/VideoStream'

export default function StreamPage() {
  return (
    <div className="container">
      <h1>Neural Style Transfer Stream</h1>
      <VideoStream
        wsUrl="ws://localhost:8765"
        width={640}
        height={480}
      />
    </div>
  )
}
```

### 3. Three.js Canvas Integration

```tsx
'use client'

import { ThreeJsVideoStream } from '@/components/VideoStream'

export default function ThreeJsPage() {
  return (
    <div className="container">
      <h1>Three.js Video Stream</h1>
      <ThreeJsVideoStream
        wsUrl="ws://localhost:8765"
        width={640}
        height={480}
      />
    </div>
  )
}
```

### 4. Install Three.js (if using ThreeJsVideoStream)

```bash
npm install three
npm install --save-dev @types/three
```

## WebSocket Protocol

### Message Types

#### 1. Connected (Server → Client)
Sent when client first connects.

```json
{
  "type": "connected",
  "message": "WebSocket connection established",
  "fps": 10,
  "resolution": {
    "width": 640,
    "height": 480
  },
  "style": "Cave Painting"
}
```

#### 2. Frame (Server → Client)
Sent for each video frame.

```json
{
  "type": "frame",
  "data": "<base64-encoded-jpeg>",
  "timestamp": 1697856123.456,
  "frameNumber": 42
}
```

The `data` field contains a base64-encoded JPEG image that can be displayed with:
```javascript
<img src={`data:image/jpeg;base64,${data}`} />
```

## Performance Tuning

### For Low Bandwidth / Artistic Visualization

Recommended settings for artistic, low-frame-rate streaming:

```bash
python websocket_stream.py \
  --fps 5 \
  --width 320 \
  --height 240 \
  --quality 70
```

### For Smoother Playback

```bash
python websocket_stream.py \
  --fps 15 \
  --width 640 \
  --height 480 \
  --quality 85
```

### For High Quality

```bash
python websocket_stream.py \
  --fps 10 \
  --width 1280 \
  --height 720 \
  --quality 90
```

### Performance Factors

| Factor | Impact | Notes |
|--------|--------|-------|
| **FPS** | CPU/GPU usage | Lower = less processing |
| **Resolution** | CPU/GPU + bandwidth | Smaller = faster |
| **JPEG Quality** | Bandwidth | 70-80 is usually fine for artistic styles |
| **Style Model** | GPU usage | All models are similar complexity |

## Network Configuration

### Local Development
```bash
python websocket_stream.py --host localhost --port 8765
```
Client connects to: `ws://localhost:8765`

### LAN Access
```bash
python websocket_stream.py --host 0.0.0.0 --port 8765
```
Client connects to: `ws://<server-ip>:8765`

### Production / Secure WebSocket
For production, use WSS (WebSocket Secure) with a reverse proxy like nginx:

```nginx
location /ws {
    proxy_pass http://localhost:8765;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

Client connects to: `wss://yourdomain.com/ws`

## Troubleshooting

### Connection Issues

**Problem:** Client can't connect
- Check that Python server is running
- Verify host/port match between server and client
- Check firewall settings
- For LAN access, ensure `--host 0.0.0.0` is set

### Performance Issues

**Problem:** Low frame rate or lag
- Reduce FPS: `--fps 5`
- Reduce resolution: `--width 320 --height 240`
- Lower JPEG quality: `--quality 70`
- Check GPU availability (should see "Using device: mps" on macOS)

**Problem:** High CPU usage
- Lower FPS
- Use smaller resolution
- Ensure PyTorch is using GPU (mps on macOS, cuda on Linux/Windows)

### Quality Issues

**Problem:** Blocky or pixelated video
- Increase JPEG quality: `--quality 90`
- Increase resolution: `--width 1280 --height 720`
- Check network bandwidth

## Multiple Clients

The server supports multiple simultaneous clients. Each client receives the same video stream. The server logs when clients connect/disconnect:

```
Client connected: 140704567890123 (total: 1)
Client connected: 140704567890456 (total: 2)
Client disconnected: 140704567890123
Total clients: 1
```

## Advanced Usage

### Custom Style Blending

To add model blending support to the WebSocket server, modify `websocket_stream.py`:

```python
# Add to VideoStreamer.__init__()
if blend_mode:
    self.model = blend_models(
        BASE_MODELS[style_key_a][0],
        BASE_MODELS[style_key_b][0],
        alpha=0.5
    )
```

### Real-time Style Switching

To change styles without restarting the server, implement a control message handler:

```python
# In video_handler(), add:
async def handle_control(websocket):
    async for message in websocket:
        data = json.loads(message)
        if data['type'] == 'change_style':
            streamer.change_style(data['style_key'])
```

### Adding Effects

To add pulse distortion or person isolation from `style_transfer.py`:

1. Copy the effect functions to `websocket_stream.py`
2. Add to `VideoStreamer.get_next_frame()` before JPEG encoding:
   ```python
   styled = self.stylize_frame(frame)
   styled = apply_pulse_distortion(styled)  # Add effects
   ```

## Example: Running Multiple Streams

Run multiple servers with different styles/sources:

```bash
# Terminal 1: Cave painting style from camera
python websocket_stream.py --port 8765 --style 7 --fps 10

# Terminal 2: Autumn forest style from video
python websocket_stream.py --port 8766 --style 5 path/to/video.mp4 --fps 5

# Terminal 3: Krampus style at high quality
python websocket_stream.py --port 8767 --style 8 --quality 95 --fps 8
```

Connect clients to different ports to display multiple streams.

## See Also

- `style_transfer.py` - Interactive application with all effects
- `video_style_transfer.py` - Batch video processing
- `EFFECTS_ARCHITECTURE.md` - Details on visual effects implementation
- `client_example.tsx` - Full React/Three.js client implementation
