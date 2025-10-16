# Visual Effects Architecture

## Current Implementation

The current system uses a simple **mode-based approach** where effects are selected via `effect_mode` integer:

```python
effect_mode = 0  # 0=none, 1=ripple, 2=pulse
```

### Effect Categories

1. **Overlay Effects** (draw on top)
   - Ripple circles
   - Grids, text, particles
   - No pixel distortion

2. **Distortion Effects** (warp pixels)
   - Pulse distortion (radial)
   - Lens effects, vortex, waves
   - Uses `cv2.remap()`

3. **Color/Filter Effects** (per-pixel color manipulation)
   - HSV shifts, color grading
   - Bloom, vignette, chromatic aberration
   - Direct array operations

## Extensible Architecture Options

### Option 1: Simple Function Registry (Current + Registry)
**Best for: Quick prototyping, 5-10 effects**

```python
# Effect registry
EFFECTS = {
    'none': lambda frame, params: frame,
    'ripple': draw_ripples,
    'pulse': apply_pulse_distortion,
    'vortex': apply_vortex,
    'kaleidoscope': apply_kaleidoscope
}

# Parameters per effect
EFFECT_PARAMS = {
    'ripple': {'spacing': 30, 'speed': 2, 'opacity': 0.3},
    'pulse': {'frequency': 3, 'amplitude': 10, 'speed': 0.1},
    'vortex': {'strength': 0.5, 'radius': 200}
}

def apply_effects(frame):
    effect_name = list(EFFECTS.keys())[effect_mode]
    params = EFFECT_PARAMS.get(effect_name, {})
    return EFFECTS[effect_name](frame, params)
```

### Option 2: Class-Based Effects
**Best for: Complex effects with state, 10+ effects**

```python
class Effect:
    def __init__(self):
        self.params = {}
        self.state = {}

    def apply(self, frame):
        raise NotImplementedError

    def adjust_param(self, param_name, delta):
        """Generic parameter adjustment"""
        pass

class PulseDistortion(Effect):
    def __init__(self):
        self.params = {
            'frequency': 3,
            'amplitude': 10,
            'speed': 0.1
        }
        self.state = {'phase': 0}

    def apply(self, frame):
        # Distortion logic here
        self.state['phase'] += self.params['speed']
        return distorted_frame

# Effect manager
effects = [NoEffect(), RippleOverlay(), PulseDistortion(), VortexEffect()]
current_effect = effects[effect_mode]
styled = current_effect.apply(styled)
```

### Option 3: Pipeline/Chain Architecture
**Best for: Combining multiple effects, advanced use**

```python
class EffectPipeline:
    def __init__(self):
        self.effects = []

    def add_effect(self, effect, enabled=True):
        self.effects.append({'effect': effect, 'enabled': enabled})

    def apply(self, frame):
        result = frame
        for item in self.effects:
            if item['enabled']:
                result = item['effect'].apply(result)
        return result

# Usage
pipeline = EffectPipeline()
pipeline.add_effect(PulseDistortion())
pipeline.add_effect(ColorGrading())
pipeline.add_effect(RippleOverlay())
styled = pipeline.apply(styled)
```

## Adding New Effects

### Example 1: Vortex/Swirl Effect

```python
def apply_vortex(frame):
    """Twist pixels around center point."""
    global vortex_angle

    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    y, x = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    dx, dy = x - cx, y - cy
    distance = np.sqrt(dx**2 + dy**2)

    # Twist amount decreases with distance
    max_dist = np.sqrt(cx**2 + cy**2)
    twist = vortex_strength * (1 - distance / max_dist) + vortex_angle

    # Rotate coordinates
    angle = np.arctan2(dy, dx) + twist
    map_x = (cx + distance * np.cos(angle)).astype(np.float32)
    map_y = (cy + distance * np.sin(angle)).astype(np.float32)

    result = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
    vortex_angle += 0.02  # Animate
    return result
```

### Example 2: Kaleidoscope Effect

```python
def apply_kaleidoscope(frame, segments=6):
    """Create kaleidoscope by mirroring wedges."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    y, x = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    dx, dy = x - cx, y - cy

    angle = np.arctan2(dy, dx)
    distance = np.sqrt(dx**2 + dy**2)

    # Map all angles to first segment and mirror
    segment_angle = 2 * np.pi / segments
    angle_mod = np.mod(angle, segment_angle)
    mirror = (np.floor(angle / segment_angle) % 2).astype(bool)
    angle_mod[mirror] = segment_angle - angle_mod[mirror]

    map_x = (cx + distance * np.cos(angle_mod)).astype(np.float32)
    map_y = (cy + distance * np.sin(angle_mod)).astype(np.float32)

    return cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
```

### Example 3: Chromatic Aberration

```python
def apply_chromatic_aberration(frame, offset=5):
    """Split RGB channels with radial offset."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    b, g, r = cv2.split(frame)

    # Red channel: expand outward
    y, x = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    dx, dy = x - cx, y - cy
    distance = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx)

    # Offset red outward, blue inward
    map_x_r = (x + offset * np.cos(angle)).astype(np.float32)
    map_y_r = (y + offset * np.sin(angle)).astype(np.float32)
    map_x_b = (x - offset * np.cos(angle)).astype(np.float32)
    map_y_b = (y - offset * np.sin(angle)).astype(np.float32)

    r_shifted = cv2.remap(r, map_x_r, map_y_r, cv2.INTER_LINEAR)
    b_shifted = cv2.remap(b, map_x_b, map_y_b, cv2.INTER_LINEAR)

    return cv2.merge([b_shifted, g, r_shifted])
```

## Performance Considerations

1. **Pre-compute maps**: For static distortions, compute remap coordinates once
2. **Resolution**: Apply effects at lower resolution, then upscale
3. **GPU acceleration**: Use `cv2.cuda` for remap operations
4. **Caching**: Reuse displacement maps when parameters unchanged

## Recommended Next Steps

1. **Immediate**: Stick with current mode-based approach (easy to understand)
2. **5-10 effects**: Move to function registry (Option 1)
3. **10+ effects or UI**: Implement class-based system (Option 2)
4. **Advanced compositing**: Build effect pipeline (Option 3)

## Integration Points

Current integration:
```python
styled = stylize_frame(frame)  # Neural style transfer
styled = apply_effects(styled)  # Post-processing effects
cv2.imshow("Style Transfer", styled)
```

Alternative: Pre-processing effects (before style transfer):
```python
preprocessed = apply_effects(frame)
styled = stylize_frame(preprocessed)
```

Or both:
```python
preprocessed = apply_pre_effects(frame)
styled = stylize_frame(preprocessed)
styled = apply_post_effects(styled)
```
