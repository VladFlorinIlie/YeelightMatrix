import json
import socket
import logging
import base64
from itertools import count

_LOGGER = logging.getLogger(__name__)


class BulbException(Exception):
    """Custom exception for bulb-related errors."""
    pass


class YeelightBulb:
    def __init__(self, ip, port):
        self.ASCII_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        self.ip = ip
        self.port = port
        self._cmd_id = count(1)
        self._music_mode = False
        self._last_properties = {}

    def _encode_color_to_ascii(self, color):
        """Encodes a color integer to Yeelight's ASCII format."""
        total_bytes = color // 64
        color = color % 64
        encoded_data = self.ASCII_TABLE[total_bytes // 4096]
        total_bytes %= 4096
        encoded_data += self.ASCII_TABLE[total_bytes // 64]
        total_bytes %= 64
        encoded_data += self.ASCII_TABLE[total_bytes]
        encoded_data += self.ASCII_TABLE[color]
        return encoded_data
    
    def _encode_color_to_base64(self, color):
        """Encodes a color integer to Base64 format."""

        rgb = [(color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF] # Extract RGB components
        rgb_bytes = bytes(rgb) # Convert to bytes
        encoded = base64.b64encode(rgb_bytes).decode('ascii') # Base64 encode
        return encoded

    def _hex_to_rgb(self, hex_color):
        """Converts a hex color code to an RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def set_matrices(self, matrices):
        """Combines multiple matrices into a single command if provided.
        """
        combined_rgb_data = ""
        for matrix in matrices:  # Process each matrix
            rgb_data = "".join(
                self._encode_color_to_base64((r * 65536) + (g * 256) + b)
                for color in matrix
                for r, g, b in [self._hex_to_rgb(color)]
            )
            combined_rgb_data += rgb_data  # Append RGB data


        command = {
            "id": next(self._cmd_id),
            "method": "update_leds",
            "params": [combined_rgb_data]  # Use combined data
        }
        self.send_command(command)

    def set_fx_mode(self, mode):
        command = {
            "id": 1,
            "method": "activate_fx_mode",
            "params": [{"mode": mode}]
        }
        self.send_command(command)

    def send_command(self, command):
        """Sends a command to the bulb."""
        try:
            with socket.create_connection((self.ip, self.port), 5) as sock:
                _LOGGER.debug(f"Sending to {self.ip}:{self.port}: {command}")
                try:
                    sock.sendall((json.dumps(command) + "\r\n").encode("utf8"))
                except socket.error as ex:
                    raise BulbException(f"Socket error sending command: {ex}")

                if self._music_mode:
                    return {"result": ["ok"]}

                response = self._receive_response(sock)
        except (socket.timeout, OSError) as err:
            raise BulbException(f"Connection error to {self.ip}:{self.port}: {err}")

        if isinstance(response, dict) and "error" in response:
            raise BulbException(response["error"])
        return response

    def _receive_response(self, sock):
        response = None
        while response is None:
            try:
                data = sock.recv(16 * 1024)
            except socket.error:
                response = {"error": "Bulb closed the connection."}
                break
            if not data:
                response = {"error": "No more data."}
                break

            for line in data.split(b"\r\n"):
                if not line:
                    continue
                try:
                    line = json.loads(line.decode("utf8"))
                    _LOGGER.debug(f"Received: {line}")
                except (ValueError, UnicodeDecodeError):
                    _LOGGER.warning("Invalid JSON or Unicode error received.")
                    line = {"result": ["invalid command"]}

                if line.get("method") != "props":
                    response = line
                elif "params" in line:  # Only update if "params" exists.
                    self._last_properties.update(line["params"])
        return response


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    ip = "192.168.0.34"
    port = 55443
    bulb = YeelightBulb(ip, port)

    colors = [
        "#FF0000",  # Red
        "#00FF00",  # Green
        "#0000FF",  # Blue
        "#FFFF00",  # Yellow
        "#FFA500",  # Orange
        "#800080",  # Purple
    ]

    # matrices = []
    # for color in colors:
    #     matrices.append([color] * 25)

    matrices = [["#000000"] * 25]
    matrices += [['#000000', '#000000', '#ed1c24', '#000000', '#000000'], ['#000000', '#ed1c24', '#000000', '#ed1c24', '#000000'], ['#ed1c24', '#000000', '#000000', '#000000', '#ed1c24'], ['#ed1c24', '#000000', '#000000', '#000000', '#ed1c24'], ['#ed1c24', '#000000', '#000000', '#000000', '#ed1c24'], ['#ed1c24', '#000000', '#ed1c24', '#000000', '#ed1c24'], ['#000000', '#ed1c24', '#000000', '#ed1c24', '#000000'], ['#000000', '#000000', '#000000', '#000000', '#000000'], ['#000000', '#000000', '#000000', '#000000', '#000000'], ['#000000', '#000000', '#000000', '#a8e61d', '#000000'], ['#000000', '#000000', '#a8e61d', '#a8e61d', '#000000'], ['#000000', '#000000', '#a8e61d', '#000000', '#000000'], ['#000000', '#000000', '#a8e61d', '#a8e61d', '#000000'], ['#000000', '#000000', '#a8e61d', '#a8e61d', '#a8e61d'], ['#000000', '#000000', '#a8e61d', '#000000', '#000000'], ['#000000', '#000000', '#ed1c24', '#000000', '#000000'], ['#000000', '#ed1c24', '#fff200', '#ed1c24', '#000000'], ['#ed1c24', '#fff200', '#fff200', '#fff200', '#ed1c24'], ['#000000', '#ed1c24', '#fff200', '#ed1c24', '#000000'], ['#000000', '#000000', '#ed1c24', '#000000', '#000000']]
    matrices.append(["#000000"])
    print(matrices)

    try:
        bulb.set_fx_mode("direct")
        bulb.set_matrices(matrices)
        print("Colors set successfully!")
    except BulbException as e:
        print(f"Error communicating with bulb: {e}")