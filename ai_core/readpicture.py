from PIL import Image
import numpy as np
def read_picture(file_path):
    with Image.open(file_path) as img:
        return np.array(img)

if __name__ == "__main__":
    gif_path = r"DRIVE/training\images\21_training.tif" #改成自己的路径
    img = read_picture(gif_path)
    print(img.shape)
