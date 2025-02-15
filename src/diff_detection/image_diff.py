import cv2
import torch.nn as nn
import torch
from skimage.metrics import structural_similarity
from torchvision.models import resnet18  # 直接导入 resnet18 模型定义


class ImageComparator:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()

    def _load_model(self):
        # 直接使用 torchvision 中的 resnet18 模型定义
        model = resnet18(pretrained=False)
        model.fc = nn.Linear(512, 1)
        try:
            model.load_state_dict(torch.load("models_path/resnet18-f37072fd.pth"))
        except Exception as e:
            print(f"无法加载本地模型：{e}")
        model.to(self.device)
        model.eval()
        return model

    def structural_compare(self, img1, img2):
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        score, diff = structural_similarity(gray1, gray2, full=True)
        diff = (diff * 255).astype("uint8")
        return diff

    def deep_compare(self, tensor1, tensor2):
        with torch.no_grad():
            diff = torch.abs(tensor1 - tensor2)
            output = self.model(diff.to(self.device))
            return output.sigmoid().item()
