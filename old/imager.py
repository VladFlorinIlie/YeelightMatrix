import numpy as np
from PIL import Image

def split_image_vertical(image_path):
    """
    Splits a 20x5 (portrait) PNG image into four 5x5 matrices.

    Args:
        image_path: Path to the PNG image.

    Returns:
        A list of four 5x5 NumPy arrays, or None if the image 
        is not 20x5 or an error occurs.
    """
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")  # Handle different image modes

        if img.size != (5, 20):
            print("Error: Image must be 20x5 pixels (portrait).")
            return None

        img = img.rotate(180)  
        img_array = np.array(img)

        matrices = []
        for i in range(4):
            start_row = i * 5
            end_row = start_row + 5
            matrix = img_array[start_row:end_row, :, :]  # Slice rows
            matrices.append(matrix)

        return matrices

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def rgb_to_hex(rgb):
    """Converts an RGB tuple to a hex string."""
    return '#%02x%02x%02x' % rgb


# Example usage (assuming you have the split_image_vertical function):
image_path = "art.png"
matrices = split_image_vertical(image_path)

if matrices:
    all_matrices_hex = []
    for matrix in matrices:
        matrix_hex = []
        for row in matrix:
            hex_row = [rgb_to_hex(tuple(pixel)) for pixel in row]
            matrix_hex.append(hex_row)
        all_matrices_hex.append(matrix_hex)

    # Flatten the list of lists of lists into a list of lists
    flat_list = [row for matrix in all_matrices_hex for row in matrix]

    print(flat_list)