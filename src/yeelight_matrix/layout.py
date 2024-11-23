import logging
from yeelight_matrix.module import Module
from yeelight_matrix.image_utils import image_to_matrix, get_image_from_file, get_image_from_colors, rotate_image

_LOGGER = logging.getLogger(__name__)

class Layout:
    def __init__(self, layout_orientation, base, device_layout=[]):
        self.layout_orientation = layout_orientation
        self.base = base
        self.number_modules = len(device_layout)

        if self.layout_orientation == "vertical":
            if self.base == "bottom":
                self.rotation_degrees = 180
                self.image_draw_flipped = True
            else:
                self.rotation_degrees = 0
                self.image_draw_flipped = False
        else:
            if self.base == "left":
                self.rotation_degrees = 270
                self.image_draw_flipped = False
            else:
                self.rotation_degrees = 90
                self.image_draw_flipped = True

        self.device_layout = list(reversed(device_layout)) if self.image_draw_flipped else device_layout


    def _get_index(self, index):
        if self.image_draw_flipped:
            return self.number_modules - index - 1
        return index


    def get_modules(self):
        return list(reversed(self.device_layout)) if self.image_draw_flipped else self.device_layout


    def add_modules_list(self, modules, clear=True):
        if clear:
            self.device_layout = []

        modules = list(reversed(modules)) if self.image_draw_flipped else modules
        for module in modules:
            self.device_layout.append(Module(module))


    def add_module(self, module, index=None):
        index = self.number_modules if index is None else index
        self.device_layout.insert(max(0, self._get_index(index)), Module(module))


    def set_module_colors(self, index, colors):
        _LOGGER.debug(f"Setting colors {colors} on module at index {index}")
        module = self.device_layout[self._get_index(index)]
        size = 1 if module.type == "1x1" else 5
        img = get_image_from_colors(colors, size, size)
        img = rotate_image(img, self.rotation_degrees)
        processed_colors = image_to_matrix(img)
        module.set_colors(processed_colors)


    def set_image(self, path, start, max=None):
        _LOGGER.debug(f"Setting image from path {path} starting with module at index {start} and using a maximum on {max}")
        found_target = False

        start = self._get_index(start)
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
            if module.type == "5x5_clear" and not module.is_used() and cnt is not None and cnt < max:
                if self.layout_orientation == "vertical":
                    img_height += 5
                else:
                    img_width += 5
                cnt += 1
            else:
                break

        try:
            imgs = get_image_from_file(path, img_width, img_height, 5, 5)
            imgs = [rotate_image(img, self.rotation_degrees) for img in imgs]
            matrices = [image_to_matrix(img) for img in imgs]

            for i, module in enumerate(self.device_layout[start_module:]):
                if i >= cnt:
                    break
                module.set_data(matrices[i])

        except IndexError:
            raise(RuntimeError("Image could not be drawn"))
        except FileNotFoundError:
            raise(FileNotFoundError(f"Error: Image file not found: {path}"))


    def get_raw_rgb_data(self):
        combined_rgb_data = ""

        if self.image_draw_flipped:
            layout = reversed(list(self.device_layout))
        else:
            layout = self.device_layout

        for module in layout:
            combined_rgb_data += module.get_rgb_data()

        return combined_rgb_data
