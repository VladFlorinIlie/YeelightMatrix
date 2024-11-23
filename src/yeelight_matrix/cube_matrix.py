import logging
import base64
from yeelight import Bulb

_LOGGER = logging.getLogger(__name__)


class CubeMatrixException(Exception):
    """Custom exception for cube matrix related errors."""
    pass


class CubeMatrix:
    def __init__(self, ip, port, music_mode=True):
        self.device = Bulb(ip, port)

        # the cube matrix is seen as being in "music mode" in the app
        # after the color matrices are applied
        # so we might as well put it in music mode from the start
        if music_mode:
            self.device.start_music()


    def get_bulb(self):
        return self.device


    def set_fx_mode(self, mode):
        self.device.send_command("activate_fx_mode", [{"mode": mode}])


    def draw_matrices(self, rgb_data):
        self.device.send_command("update_leds", [rgb_data])


    @staticmethod
    def encode_hex_color(hex_color):
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        rgb_bytes = bytes(rgb)
        encoded = base64.b64encode(rgb_bytes).decode("ascii")
        return encoded