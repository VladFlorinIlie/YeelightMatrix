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

Install via **HACS** (add this repo as a custom repository, category
*Integration*) or by copying `custom_components/yeelight_matrix` into your Home
Assistant `config/custom_components` directory. Restart Home Assistant, then add
the integration from **Settings → Devices & Services**. See
[docs/HOME_ASSISTANT.md](docs/HOME_ASSISTANT.md) for full steps. You
provide the IP/port, the orientation and base, and the comma-separated module
list (e.g. `5x5_clear,5x5_clear,1x1`). Tick **Create a light entity for every
individual dot** if you want one toggleable light per LED.

### Entities

- A whole-device light for power, brightness and colour.
- Optionally, one light per dot (`Module N dot x,y`) so you can colour
  individual LEDs straight from the dashboard.

### Services

All services target the Yeelight Matrix light entity.

| Service | Purpose |
| --- | --- |
| `yeelight_matrix.set_pixel` | Colour one dot (`module_index`, `x`, `y`, `color`). |
| `yeelight_matrix.set_pixels` | Batch many dots in one frame (used by the card). |
| `yeelight_matrix.set_module_color` | Fill a module with one colour. |
| `yeelight_matrix.set_module_colors` | Set a module's full 25-colour grid. |
| `yeelight_matrix.set_image` | Draw pixel art from `image_path` or base64 `image_data`. |
| `yeelight_matrix.clear` | Turn every dot off. |
| `yeelight_matrix.set_fx_mode` | Activate a device effect mode. |

Uploading pixel art from an automation:

```yaml
service: yeelight_matrix.set_image
target:
  entity_id: light.yeelight_matrix
data:
  image_data: "{{ states('input_text.my_base64_png') }}"
  start_module: 0
  max_modules: 2
```

### Painter card (tap a dot to colour it)

`custom_components/yeelight_matrix/www/yeelight-matrix-card.js` is a custom
Lovelace card that renders the matrix as a grid you can paint by tapping or
dragging — like the Yeelight app. Register it as a dashboard resource
(`/local/yeelight-matrix-card.js` if you copy it into `config/www`, or via the
served `www` folder) and add:

```yaml
type: custom:yeelight-matrix-card
entity: light.yeelight_matrix
```

## Desktop GUI

`src/gui/gui.py` is a Tkinter tool for defining a layout and painting modules.

## Examples

See `examples/demo.py`.
```bash
cd examples/
python demo.py
```
