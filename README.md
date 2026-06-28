# Yeelight Cube Matrix Controller

A Python library and Home Assistant integration for controlling the **Yeelight
Cube Matrix** — stackable LED cubes that come in three module types: a 5x5
matrix (`5x5_clear`), a 5x5 diffused matrix (`5x5_blur`), and a single-LED
spotlight (`1x1`). Every dot of a 5x5 module is individually addressable.

## Installation

```bash
cd src/
pip install -e .
```

## Library quick start

```python
from yeelight_matrix import CubeMatrix, Layout

cube = CubeMatrix("192.168.0.34")      # connects and enables music mode
cube.set_fx_mode("direct")             # required for per-LED control

# Describe how the modules are physically stacked.
layout = Layout("vertical", "bottom", ["5x5_clear", "5x5_clear", "1x1"])

layout.set_module_colors(0, "#0000ff")     # fill a whole module
layout.set_pixel(0, 2, 2, "#ffffff")       # light a single dot (col, row)
layout.set_image("art.png", start_module=0, max_modules=2)  # pixel art

cube.update_leds(layout.render_frame())    # push one frame to the device
```

Colours may be given as hex strings (`"#ff0000"`) or `(r, g, b)` tuples
throughout.

## API reference

### `CubeMatrix(ip, port=55443, music_mode=True)`

- `set_fx_mode(mode="direct")` — activate an effect mode; `"direct"` is needed
  for per-LED control.
- `update_leds(rgb_data)` — push a full base64 frame (from `Layout.render_frame`).
- `set_pixels(colors)` — encode and push an ordered colour sequence directly.
- `bulb` — the underlying [`yeelight.Bulb`](https://yeelight.readthedocs.io) for
  power, brightness and colour.

### `Layout(orientation, base, modules=None)`

`orientation` is `"vertical"` or `"horizontal"`; `base` is `"top"`/`"bottom"`
(vertical) or `"left"`/`"right"` (horizontal). `modules` is a list of module
type strings. Modules are addressed by **logical index** (0 = first module);
rotation for the mounting position is applied automatically at render time.

- `set_pixel(module_index, x, y, color)` — set one dot of a 5x5 module.
- `set_module_colors(index, colors)` — a single colour fills the module, or pass
  a row-major list (25 for a 5x5 module).
- `set_image(path, start_module=0, max_modules=None)` — map a picture across
  consecutive 5x5 modules.
- `fill(color)` / `clear()` — fill or blank the whole layout.
- `render_frame()` — return the base64 frame for `CubeMatrix.update_leds`.
- `modules` — the modules in logical order.

## Home Assistant integration

Full step-by-step guide: [docs/HOME_ASSISTANT.md](docs/HOME_ASSISTANT.md).

### Install

1. **HACS → ⋮ → Custom repositories** → add this repository, category
   **Integration** → open it → **Download**. (Or copy
   `custom_components/yeelight_matrix` into `config/custom_components`.)
2. **Restart Home Assistant.** It installs the `YeelightMatrix` PyPI requirement
   on startup, and registers the painter card automatically (no manual resource
   needed).

### Configure

**Settings → Devices & Services → Add Integration → "Yeelight Matrix".**

- IP address and port (usually `55443`).
- Orientation (`vertical`/`horizontal`) and base position
  (`top`/`bottom` or `left`/`right`).
- Modules, comma-separated, in order — e.g.
  `5x5_blur,5x5_clear,5x5_clear,1x1`.
- Optional: tick **Create a light entity for every individual dot** to get one
  light per LED (otherwise control dots via the card or services).

Use the **Power** toggle on the card (or the `set_power` service) to turn the
matrix on — that powers it on and switches it to `direct` mode, ready for
drawing — or off. Drawing itself no longer changes power or mode.

### Entities

- A whole-device light (power, brightness, colour).
- Optionally one light per dot (`Module N dot x,y`).

### Painter card (tap a dot to colour it)

The integration serves and registers the card for you. Add it to a dashboard
(Add Card → **Manual**):

```yaml
type: custom:yeelight-matrix-card
entity: light.yeelight_matrix
# reverse: true       # optional override; by default the order is taken from
#                     # the base position so the on-screen order matches the cubes
max_dot_size: 30      # optional px upper bound per dot
min_dot_size: 12      # optional px; below this the grid scrolls
```

The module order is derived automatically from the base position (base on the
right/bottom is shown reversed so module 0 sits on the base side), so it matches
your physical cubes without configuration. Set `reverse` only to override it.

Flip **Power** to turn the cubes on (direct mode) or off. Pick a colour (full
picker or a swatch) and **click a dot** to colour it. **Upload art** maps an
image across the clear modules, and **Clear** blanks everything. The grid
restores from the device when it loads.

### Services

All services target the Yeelight Matrix light entity.

| Service | Purpose |
| --- | --- |
| `yeelight_matrix.set_pixel` | Colour one dot (`module_index`, `x`, `y`, `color`). |
| `yeelight_matrix.set_pixels` | Set many dots in one frame. |
| `yeelight_matrix.set_module_color` | Fill a module with one colour. |
| `yeelight_matrix.set_module_colors` | Set a module's full 25-colour grid. |
| `yeelight_matrix.set_image` | Draw pixel art from `image_path` or base64 `image_data`. |
| `yeelight_matrix.clear` | Turn every dot off. |
| `yeelight_matrix.set_power` | Turn the matrix on (direct mode) or off. |
| `yeelight_matrix.set_fx_mode` | Activate a device effect mode. |

Example — draw a single dot:

```yaml
action: yeelight_matrix.set_pixel
target:
  entity_id: light.yeelight_matrix
data: { module_index: 1, x: 2, y: 2, color: "#ff0000" }
```

## Desktop GUI

`src/gui/gui.py` is a Tkinter tool for defining a layout and painting modules.

## Examples

See `examples/demo.py`.
```bash
cd examples/
python demo.py
```
