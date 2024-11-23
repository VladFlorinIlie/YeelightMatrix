from module import Module
from image_utils import process_image, image_to_matrix

class Layout:
    def __init__(self, layout_orientation, base, device_layout=[]):
        self.layout_orientation = layout_orientation
        if base == "bottom" or base == "right":
            self.flip = True
        else:
            self.flip = False
        self.device_layout = device_layout


    def _rotate_data(self, data):
        if self.flip and len(data) > 1:
            rotated_matrix = []
            for i in range(4, -1, -1):
                for j in range(4, -1, -1):
                    index = i * 5 + j
                    rotated_matrix.append(data[index])
            return rotated_matrix

        return data


    def get_modules(self):
        return self.device_layout


    def add_modules_list(self, modules, clear=True):
        if clear:
            self.device_layout = []

        for module in modules:
            self.device_layout.append(Module(module))


    def add_module(self, module, index=-1):
        self.device_layout.insert(index, Module(module))


    def set_module_colors(self, index, colors):
        module = self.device_layout[index]
        if module.is_used():
            raise ValueError("Module already set!")
        module.set_colors(self._rotate_data(colors))


    def set_image(self, path, start=0, max=None):
        start_module = 0
        found_target = False
        for i, module in enumerate(self.device_layout):
            if module.type == "5x5_clear" and not module.is_used() and i >= start:
                found_target = True
                start_module = i
                break

        if not found_target:
            raise IndexError("Requested start module could not be found or used!")
        
        if self.layout_orientation == "vertical":
            img_height = 0
            img_width = 5
        else:
            img_height = 5
            img_width = 0

        cnt = 0
        for module in self.device_layout[start_module:]:
            if module.type == "5x5_clear" and not module.is_used() and cnt < max:
                if self.layout_orientation == "vertical":
                    img_height += 5
                else:
                    img_width += 5
                cnt += 1
            else:
                break

        try:
            resized_img = process_image(path, img_width, img_height, self.flip)
            matrix = image_to_matrix(resized_img)

            if self.layout_orientation == "vertical":
                split_matrices = [matrix[i : i + 25] for i in range(0, len(matrix), 25)]
                for i, split_matrix in enumerate(split_matrices):
                    self.device_layout[start_module + i].set_data(split_matrix)
            else: 
                temp_matrices = [[] for _ in range(img_width // 5)]
                for j in range(25):
                    for i in range(img_width // 5):
                        temp_matrices[i].append(matrix[j * (img_width // 5) + i])
                for i, split_matrix in enumerate(temp_matrices):
                    self.device_layout[start_module + i].set_data(split_matrix)

        except IndexError:
            print("Image could not be drawn (likely not enough space)")
            return None
        except FileNotFoundError:
            print(f"Error: Image file not found: {path}")
            return None


    def get_raw_rgb_data(self):
        combined_rgb_data = ""

        for module in self.device_layout:
            combined_rgb_data += module.get_rgb_data()

        return combined_rgb_data
