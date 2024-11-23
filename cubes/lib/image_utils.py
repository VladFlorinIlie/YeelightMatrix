from PIL import Image

def get_image_from_file(image_path, width, height, sub_width, sub_height):
    img = Image.open(image_path)
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    if width > height:
        parts = width // sub_width
        dir = True
    elif width < height:
        parts = height // sub_height
        dir = False
    else:
        return [img]

    sub_images = []
    for i in range(parts):
        if dir:
            left = i * sub_width
            top = 0
            right = (i + 1) * sub_width
            bottom = sub_height
        else:
            left = 0
            top = i * sub_height
            right = sub_width
            bottom = (i + 1) * sub_height
        
        bbox = (left, top, right, bottom)
        sub_img = img.crop(bbox)
        sub_images.append(sub_img)

    return sub_images


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


def image_to_matrix(img):
    matrix = []

    for pixel in img.getdata():
        color = "#{:02x}{:02x}{:02x}".format(*pixel[:3])
        matrix.append(color)

    return matrix