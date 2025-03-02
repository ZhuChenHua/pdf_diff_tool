import asyncio
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import os

from ..pdf_processing.image_processor import ImageProcessor
from ..pdf_processing.text_processor import TextProcessor
from ..pdf_processing.classifier import PDFClassifier
from ..diff_detection.image_diff import ImageComparator
from ..pdf_processing.pdf_annotation import PDFAnnotator

executor = ThreadPoolExecutor(max_workers=2)


async def async_compare(file1, file2):
    loop = asyncio.get_event_loop()

    # 获取项目根目录路径
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    temp_dir = os.path.join(project_root, "data\\temp")

    # 检查并创建 temp 目录
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # 构建文件的绝对路径
    file1_path = os.path.join(temp_dir, file1.name)
    file2_path = os.path.join(temp_dir, file2.name)

    try:
        # 保存上传文件
        with open(file1_path, "wb") as f:
            f.write(file1.getbuffer())
        with open(file2_path, "wb") as f:
            f.write(file2.getbuffer())
    except Exception as e:
        print(f"文件保存失败: {e}")
        return {"type": "error", "message": f"文件保存失败: {e}"}

    # 分类处理
    classifier = PDFClassifier()
    file_type = classifier.classify(file1_path)

    # 统一定义：output_path
    output_path = os.path.join(temp_dir, "annotated.pdf")

    if file_type == "text":
        processor = TextProcessor()
        # 获取精确的差异位置
        diffs = processor.get_text_positions(file1_path, file2_path)

        # # 生成标注PDF
        # output_path = os.path.join(temp_dir, "annotated.pdf")

        # 获取文本差异详情
        test1 = await loop.run_in_executor(executor, processor.extract_text, file1_path)
        test2 = await loop.run_in_executor(executor, processor.extract_text, file2_path)
        details = processor.compare_text(test1, test2)

        try:
            PDFAnnotator.highlight_text_diffs(file2_path, diffs, output_path)
        except Exception as e:
            print(f"PDF标注失败: {str(e)}")
            return {"type": "error", "message": "文本差异标注失败"}

        return {
            "type": "text",
            "annotated_pdf": output_path,
            "original_pdf": file1_path,
            "details": details,  # 添加文本差异详情
        }
    else:
        processor = ImageProcessor()
        images1 = await loop.run_in_executor(
            executor, processor.pdf_to_images, file1_path
        )
        images2 = await loop.run_in_executor(
            executor, processor.pdf_to_images, file2_path
        )
        comparator = ImageComparator()
        diff_img = await loop.run_in_executor(
            executor,
            comparator.structural_compare,
            np.array(images1[0]),
            np.array(images2[0]),
        )

        # 新增原始图像和差异图像数据
        return {
            "type": "image",
            "original": np.array(images1[0]),  # 原始图像数据
            "modified": np.array(images2[0]),  # 对比文件图像
            "diff": diff_img,  # 差异掩膜
            "annotated_pdf": output_path,  # 标注后的PDF路径
        }
