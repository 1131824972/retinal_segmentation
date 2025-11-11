import cv2
import numpy as np
import os


def create_test_images():
    """创建测试用的眼底图像"""
    os.makedirs('demo_images', exist_ok=True)

    # 创建几个不同尺寸的测试图像
    sizes = [(256, 256), (512, 512), (1024, 768)]

    for i, size in enumerate(sizes):
        # 创建模拟眼底图像
        image = np.zeros((size[1], size[0], 3), dtype=np.uint8)

        # 添加眼底特征
        center = (size[0] // 2, size[1] // 2)
        cv2.circle(image, center, min(size) // 4, (100, 100, 100), -1)  # 视盘

        # 添加血管状结构
        for j in range(8):
            angle = j * 45
            end_x = center[0] + int(np.cos(np.radians(angle)) * min(size) // 3)
            end_y = center[1] + int(np.sin(np.radians(angle)) * min(size) // 3)
            cv2.line(image, center, (end_x, end_y), (120, 120, 120), 3)

        filename = f'demo_images/retina_test_{size[0]}x{size[1]}.png'
        cv2.imwrite(filename, image)
        print(f"创建测试图像: {filename}")

    print("✅ 测试图像创建完成")


if __name__ == "__main__":
    create_test_images()