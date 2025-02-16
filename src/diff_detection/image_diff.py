import cv2
import torch.nn as nn
import torch
from skimage.metrics import structural_similarity
from torchvision.models import resnet18  # 直接导入 resnet18 模型定义
from torchvision.models import ResNet18_Weights


class ImageComparator:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()

    def _load_model(self):
        # 直接使用 torchvision 中的 resnet18 模型定义
        model = resnet18(weights=ResNet18_Weights.DEFAULT)
        # 修改全连接层
        model.fc = nn.Linear(512, 1)
        # 初始化新层
        nn.init.xavier_uniform_(model.fc.weight)
        nn.init.constant_(model.fc.bias, 0)

        model.to(self.device)
        model.eval()
        return model

    def structural_compare(self, img1, img2):

        # 确保图像尺寸至少为 7x7
        min_side = min(img1.shape[0], img1.shape[1])
        if min_side < 7:
            raise ValueError(
                "图像尺寸过小，无法进行结构相似性计算。请确保图像尺寸至少为 7x7。"
            )

        # 动态设置 win_size
        win_size = min(7, min_side)

        # 增加颜色通道对比
        score, diff = structural_similarity(
            img1,
            img2,
            multichannel=True,
            full=True,
            win_size=win_size,
            channel_axis=2,  # 设置颜色通道轴为第 3 维
        )
        return (diff * 255).astype("uint8")

    def deep_compare(self, tensor1, tensor2):
        with torch.no_grad():
            diff = torch.abs(tensor1 - tensor2)
            output = self.model(diff.to(self.device))
            return output.sigmoid().item()


if __name__ == "__main__":
    # 测试代码
    comparator = ImageComparator()
    print(comparator.model)
    # 应输出包含"Linear(in_features=512, out_features=1)"的结构
