from pdf2image import convert_from_path
import cv2
import numpy as np
import torch


class ImageProcessor:
    def __init__(self, dpi=200):
        self.dpi = dpi

    def pdf_to_images(self, pdf_path):
        try:
            return convert_from_path(pdf_path, dpi=self.dpi)
        except Exception as e:
            print(f"PDF to image conversion failed: {e}")
            return []

    @staticmethod
    def preprocess(image):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        img = cv2.resize(img, (224, 224))
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        return img_tensor.unsqueeze(0)
