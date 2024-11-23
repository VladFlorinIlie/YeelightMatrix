from PIL import Image

def process_image(image_path, width, height, flip):
    img = Image.open(image_path)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    if flip:
        img = img.rotate(180)
    return img


def image_to_matrix(img):
    matrix = []
    for pixel in img.getdata():
        matrix.append("#{:02x}{:02x}{:02x}".format(*pixel[:3])) # Added # here for consistency
    return matrix