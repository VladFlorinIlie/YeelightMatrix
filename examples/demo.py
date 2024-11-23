import logging
from yeelight_matrix.cube_matrix import CubeMatrix
from yeelight_matrix.layout import Layout

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    ip = "192.168.0.34"
    port = 55443
    cube = CubeMatrix(ip, port)
    cube.set_fx_mode("direct")
    cube.get_bulb().set_brightness(100)

    device_layout = [
        "5x5_blur",
        "5x5_clear",
        "5x5_clear",
        "5x5_clear",
        "5x5_clear",
        "1x1"
    ]

    images_data = [
        ("assets/art.png", 4, 4)
    ]

    layout = Layout("vertical", "bottom")
    layout.add_modules_list(device_layout)
    layout.set_module_colors(0, ["#0000FF"] * 25)
    layout.set_module_colors(5, ["#FF0000"])

    for image_data in images_data:
        (path, start, max) = image_data
        layout.set_image(path, start, max)

    try:
        raw_rgb_data = layout.get_raw_rgb_data()
        cube.draw_matrices(raw_rgb_data)
        print("Layout set successfully!")
    except Exception as e:
        print(f"Error: {e}")