import torch
import lpips
import cv2
import numpy as np
import sys
import os

class JewelryMatcher:
    def __init__(self):
        self.lpips_model = lpips.LPIPS(net='alex')  # No `model_path` needed


    def _preprocess_image(self, img_path):
        """Preprocess: Convert to RGB & Normalize for LPIPS"""
        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (256, 256))  # Resize for LPIPS
        img = img.astype(np.float32) / 255.0  # Normalize
        return torch.tensor(img).permute(2, 0, 1).unsqueeze(0)  # Convert to PyTorch tensor

    def compare(self, img1_path, img2_path):
        """Compare images using LPIPS deep similarity"""
        img1 = self._preprocess_image(img1_path)
        img2 = self._preprocess_image(img2_path)

        with torch.no_grad():
            similarity = 1 - self.lpips_model(img1, img2).item()  # LPIPS outputs distance, so invert

        return similarity  # 1 = same, 0 = completely different
