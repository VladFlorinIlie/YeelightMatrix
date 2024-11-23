from PIL import Image

def get_image_from_file(image_path, width, height):
    img = Image.open(image_path)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    return img


def get_image_from_colors(colors, width, height):
    img = Image.new("RGB", (width, height))

    i = 0
    for y in range(height):
        for x in range(width):
            img.putpixel((x, y), tuple(int(colors[i].lstrip("#")[j : j + 2], 16) for j in (0, 2, 4)))
            i += 1

    return img


def rotate_image(img, degrees):
    return img.rotate(degrees)


def image_to_matrices(img, sub_width, sub_height):
    matrices = []
    temp_matrix = []
    values = 0

    for pixel in img.getdata():
        color = "#{:02x}{:02x}{:02x}".format(*pixel[:3])
        temp_matrix.append(color)
        values += 1

        if values == sub_width * sub_height:
            matrices.append(temp_matrix)
            temp_matrix = []
            values = 0

    return matrices