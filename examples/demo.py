"""Minimal end-to-end example for the Yeelight Cube Matrix library."""

import logging

from yeelight_matrix import CubeMatrix, Layout

logging.basicConfig(level=logging.INFO)

IP = "192.168.0.34"
PORT = 55443


def main() -> None:
    cube = CubeMatrix(IP, PORT)
    cube.set_fx_mode("direct")
    cube.bulb.set_brightness(100)

    # A bottom-based vertical stack: four 5x5 panels and a spotlight on top.
    layout = Layout(
        "vertical",
        "bottom",
        ["5x5_blur", "5x5_clear", "5x5_clear", "5x5_clear", "5x5_clear", "1x1"],
    )

    # Fill a whole module, light a single dot, and draw an image across panels.
    layout.set_module_colors(0, "#0000ff")        # whole blur panel blue
    layout.set_pixel(1, 2, 2, "#ffffff")          # one centre dot white
    layout.set_module_colors(5, "#ff0000")        # spotlight red
    layout.set_image("assets/art.png", start_module=2, max_modules=4)

    cube.update_leds(layout.render_frame())
    print("Layout sent successfully!")


if __name__ == "__main__":
    main()
