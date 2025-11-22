import numpy as np
import os
from readpicture import read_picture
import cv2

for name in ['training', 'test']:
    picture_path = os.path.join("DRIVE", name, "images")
    label_path = os.path.join("DRIVE", name, "1st_manual")

    picturenames = os.listdir(picture_path)
    labelnames = os.listdir(label_path)

    data = []
    label = []

    for d, l in zip(picturenames, labelnames):
        dp = os.path.join(picture_path, d)
        lp = os.path.join(label_path, l)
        p = cv2.resize(read_picture(dp), (512, 512)).transpose(2, 0, 1)
        l = cv2.resize(read_picture(lp), (512, 512)).reshape(1, 512, 512)
        p = (p - np.min(p)) / (np.max(p) - np.min(p))
        l = (l - np.min(l)) / (np.max(l) - np.min(l))
        data.append(p)
        label.append(l)

    dataset = np.array([i for i in zip(data, label)])

    # 这个代码需要支持不规则数组保存的numpy 不然会报错
    np.save(f"pre/{name}dataset", dataset)

