import json
import socket
import logging
from itertools import count
import base64

_LOGGER = logging.getLogger(__name__)


class BulbException(Exception):
    """Custom exception for bulb-related errors."""
    pass


class CubeMatrix:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self._cmd_id = count(1)
        self._music_mode = True
        self._last_properties = {}


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
                elif "params" in line:
                    self._last_properties.update(line["params"])
        return response


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
    

    def set_power_state(self, state):
        command = {
            "id": next(self._cmd_id),
            "method": "set_power",
            "params": [state, "smooth", 500]
        }
        self.send_command(command)


    def set_brightness(self, brightness):
        command = {
            "id": next(self._cmd_id),
            "method": "set_bright",
            "params": [brightness, "smooth", 500]
        }
        self.send_command(command)


    def set_fx_mode(self, mode):
        command = {
            "id": next(self._cmd_id),
            "method": "activate_fx_mode",
            "params": [{"mode": mode}]
        }
        self.send_command(command)


    def draw_matrices(self, rgb_data):
        command = {
            "id": next(self._cmd_id),
            "method": "update_leds",
            "params": [rgb_data]
        }
        self.send_command(command)


    @staticmethod
    def encode_hex_color(hex_color):
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        rgb_bytes = bytes(rgb)
        encoded = base64.b64encode(rgb_bytes).decode("ascii")
        return encoded