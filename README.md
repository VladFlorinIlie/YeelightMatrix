# Yeelight Cube Matrix Controller (WIP)

This library provides a Python interface for controlling Yeelight cube matrix devices, allowing you to set colors, display images, and manage complex modular layouts.

## Installation

```bash
cd src/
pip install -e .
```

## API Reference

### `CubeMatrix` Class

*   **`CubeMatrix(ip, port)`:** Creates a `CubeMatrix` object to represent your Yeelight device.  `ip` is the IP address of the device, and `port` is the port number (usually 55443).

*   **`draw_matrices(raw_rgb_data)`:** Sends raw RGB data to control the LEDs.

*   **`set_power_state(state)`:** Turns the device on or off. `state` should be either `"on"` or `"off"`.

*   **`set_brightness(brightness)`:** Sets the overall brightness of the device. `brightness` should be an integer between 0 and 100.

*   **`set_fx_mode(mode)`:** Activates a specific effect mode. For direct control of LEDs using `draw_matrices()`, `mode` should be set to `"direct"`.  Other effect modes might be available depending on your device; consult the Yeelight API documentation for 

### `Layout` Class

*   **`Layout(layout_orientation, base_posiiton)`:** Creates a `Layout` object to represent the arrangement of your modules. `layout_orientation` should be either `"vertical"` or `"horizontal"`.`base_position` is `"top"` or `"bottom"` for vertical and `"left"` or `"right"` for horizontal.

*   **`add_modules_list(modules)`:** Adds a list of module types to the layout. `modules` should be a list of strings, where each string is either `"5x5_clear"`, `"5x5_blur"`, or `"1x1"`.

*   **`add_module(module_type)`:** Adds a single module of the specified `module_type` to the layout.  Use this to dynamically add modules after initial layout setup.

*   **`set_module_colors(module_index, colors)`:** Sets the colors for the module at the specified `module_index`.  `colors` should be a list of hex color codes. For 5x5 modules, it should be a list of 25 colors; for 1x1 modules, it should be a list containing a single color.

*   **`set_image(image_path, start_module, max_modules)`:**  Loads an image from `image_path` and displays it on the layout, starting at `start_module` and spanning at most `max_modules` clear modules.

*   **`get_raw_rgb_data()`:** Returns a string containing the encoded RGB data for the entire layout, ready to be sent to the `CubeMatrix` using `draw_matrices()`

## GUI (gui.py)
WIP


## Examples
Check the demo code from examples directory.