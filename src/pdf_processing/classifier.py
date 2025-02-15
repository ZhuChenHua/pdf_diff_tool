# classifier.py
import logging
from pathlib import Path
from typing import Optional, Union

import pdfplumber
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms
from pdf2image import convert_from_path

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFClassifier:
    """PDF文档分类器，用于区分文本型PDF和图像型PDF

    特性：
    - 混合检测策略：结合启发式规则和深度学习模型
    - 多页面采样分析
    - 支持GPU加速
    - 可配置的分类阈值

    参数：
    text_threshold (float): 文本页面的判定阈值 (默认: 0.6)
    model_path (str): 预训练模型路径 (默认: None使用内置模型)
    sample_pages (int): 采样的页面数量 (默认: 5)
    device (str): 计算设备 ('cuda' 或 'cpu') (默认: auto)
    """

    def __init__(
        self,
        text_threshold: float = 0.6,
        model_path: Optional[Union[str, Path]] = None,
        sample_pages: int = 5,
        device: Optional[str] = None,
    ):
        self.text_threshold = text_threshold
        self.sample_pages = sample_pages
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # 初始化模型
        self.model = self._init_model(model_path)
        self.preprocess = transforms.Compose(
            [
                transforms.Resize(224),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def _init_model(self, model_path: Optional[Union[str, Path]]) -> nn.Module:
        """初始化并加载预训练模型"""
        model = models.resnet18(pretrained=True)
        model.fc = nn.Linear(512, 2)  # 修改最后的全连接层

        if model_path:
            try:
                state_dict = torch.load(model_path, map_location=self.device)
                model.load_state_dict(state_dict)
                logger.info(f"成功加载自定义模型: {model_path}")
            except Exception as e:
                logger.warning(f"无法加载自定义模型: {e}，使用默认初始化")
        else:
            logger.info("使用未经微调的预训练ResNet18")

        model = model.to(self.device)
        model.eval()
        return model

    def _is_text_based(self, pdf_path: Union[str, Path]) -> bool:
        """启发式文本检测策略

        参数：
        pdf_path: PDF文件路径

        返回：
        bool: 如果检测为文本型PDF返回True
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                sampled_pages = pdf.pages[: self.sample_pages]

                text_pages = 0
                for page in sampled_pages:
                    text = page.extract_text(x_tolerance=1, y_tolerance=1)
                    if text and len(text.strip()) > 100:  # 排除空白页面
                        text_pages += 1

                ratio = text_pages / len(sampled_pages)
                logger.debug(f"文本页面比例: {ratio:.2f}")
                return ratio >= self.text_threshold

        except Exception as e:
            logger.error(f"文本检测失败: {e}")
            return False

    def _preprocess_pdf(self, pdf_path: Union[str, Path]) -> torch.Tensor:
        """预处理PDF文件为模型输入"""
        try:
            # 转换PDF为图像
            images = convert_from_path(
                pdf_path, first_page=1, last_page=1
            )  # 仅处理第一页
            if not images:
                raise ValueError("无法转换PDF为图像")

            # 预处理图像
            image_tensor = self.preprocess(images[0]).unsqueeze(0)
            return image_tensor.to(self.device)

        except Exception as e:
            logger.error(f"PDF预处理失败: {e}")
            raise

    def classify(self, pdf_path: Union[str, Path]) -> str:
        """分类PDF文件类型

        参数：
        pdf_path: PDF文件路径

        返回：
        str: 'text' 或 'image'
        """
        # 第一阶段：快速启发式检测
        if self._is_text_based(pdf_path):
            logger.info("启发式检测为文本型PDF")
            return "text"

        try:
            # 第二阶段：深度学习验证
            input_tensor = self._preprocess_pdf(pdf_path)

            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                image_prob = probabilities[0][1].item()

            logger.info(f"图像型概率: {image_prob:.2f}")
            return "image" if image_prob > 0.5 else "text"

        except Exception as e:
            logger.error(f"分类失败: {e}，默认返回image")
            return "image"


# 使用示例
if __name__ == "__main__":
    classifier = PDFClassifier(text_threshold=0.5)
    result = classifier.classify("sample.pdf")
    print(f"分类结果: {result}")
