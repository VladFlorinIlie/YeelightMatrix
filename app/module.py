from cube_matrix import CubeMatrix

class Module:
    def __init__(self, type="5x5_clear", data=None):
        self.type = type
        self.data = data
        if self.data is None:
            if self.type == "1x1":
                self.data = ["#000000"]
            else:
                self.data = ["#000000"] * 25
        self.used = False


    def set_data(self, data):
        if self.type == "5x5_clear" and not (isinstance(data, list) and len(data) == 25): # Fixed some typos and validations
            raise ValueError("Invalid data for 5x5_clear module")
        elif self.type == "5x5_blur" and not (isinstance(data, list) and len(data) == 25):
            raise ValueError("Invalid data for 5x5_blur module")
        elif self.type == "1x1" and not isinstance(data, str): # 1x1 is a string hex code.
          raise ValueError("Invalid data for 1x1 module")
        self.data = data
        self.used = True


    def set_colors(self, colors):
        if self.type == "1x1":
            if len(colors) != 1:
                raise ValueError("1x1 module takes only one color")
        elif self.type.startswith("5x5"):
            if len(colors) != 25:
                raise ValueError(f"5x5 module requires 25 colors, but received {len(colors)}")
        self.data = colors
        self.used = True


    def get_colors(self):
        return self.data


    def get_rgb_data(self):
        if self.type == "5x5_clear" or self.type == "5x5_blur":
            return "".join(
                CubeMatrix.encode_hex_color(color)
                for color in self.data
            )

        elif self.type == "1x1":
            return CubeMatrix.encode_hex_color(self.data[0])


    def is_used(self):
        return self.used    