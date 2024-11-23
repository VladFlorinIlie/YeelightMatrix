from module import Module
from image_utils import image_to_matrices, get_image_from_file, get_image_from_colors, rotate_image

class Layout:
    def __init__(self, layout_orientation, base, device_layout=[]):
        self.layout_orientation = layout_orientation
        self.base = base
        self.device_layout = device_layout

        if self.layout_orientation == "vertical":
            if self.base == "bottom":
                self.rotation_degrees = 180
                self.image_draw_flipped = True
            else:
                self.rotation_degrees = 0
                self.image_draw_flipped = False
        else:
            if self.base == "left":
                self.rotation_degrees = 90
                self.image_draw_flipped = False
            else:
                self.rotation_degrees = 270
                self.image_draw_flipped = True


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
        size = 1 if module.type == "1x1" else 5
        img = get_image_from_colors(colors, size, size)
        img = rotate_image(img, self.rotation_degrees)
        processed_colors = image_to_matrices(img, size, size)[0]
        module.set_colors(processed_colors)


    def set_image(self, path, start, max=None):
        start_module = 0
        found_target = False

        if (self.image_draw_flipped):
            enum = reversed(list(enumerate(self.device_layout)))
        else:
            enum = enumerate(self.device_layout)

        for i, module in enum:
            if module.type == "5x5_clear" and not module.is_used():
                if i >= start and self.image_draw_flipped or i <= start and not self.image_draw_flipped:
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
        if (self.image_draw_flipped):
            layout = list(reversed(self.device_layout))
        else:
            layout = self.device_layout

        for module in layout[start_module:]:
            if module.type == "5x5_clear" and not module.is_used() and cnt < max:
                if self.layout_orientation == "vertical":
                    img_height += 5
                else:
                    img_width += 5
                cnt += 1
            else:
                break

        print(start_module)
        print(img_height)

        try:
            img = get_image_from_file(path, img_width, img_height)
            img = rotate_image(img, self.rotation_degrees)
            matrices = image_to_matrices(img, img_width, img_height)

            for i, module in enumerate(layout[start_module:]):
                if i >= cnt:
                    break
                module.set_data(matrices[i])

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
