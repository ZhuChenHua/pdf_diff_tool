import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import os

from ..pdf_processing.image_processor import ImageProcessor
from ..pdf_processing.text_processor import TextProcessor
from ..pdf_processing.classifier import PDFClassifier
from ..diff_detection.image_diff import ImageComparator

executor = ThreadPoolExecutor(max_workers=3)


async def async_compare(file1, file2):
    loop = asyncio.get_event_loop()

    # 获取项目根目录路径
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    # 构建 temp 目录的绝对路径
    temp_dir = os.path.join(project_root, "temp")

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

    if file_type == "text":
        processor = TextProcessor()
        text1 = await loop.run_in_executor(executor, processor.extract_text, file1_path)
        text2 = await loop.run_in_executor(executor, processor.extract_text, file2_path)
        result = await loop.run_in_executor(
            executor, processor.compare_text, text1, text2
        )
        return {"type": "text", "details": result}
    else:
        processor = ImageProcessor()
        images1 = await loop.run_in_executor(
            executor, processor.pdf_to_images, file1_path
        )
        images2 = await loop.run_in_executor(
            executor, processor.pdf_to_images, file2_path
        )
        comparator = ImageComparator()
        # 比较第一页作为示例
        diff_img = await loop.run_in_executor(
            executor,
            comparator.structural_compare,
            np.array(images1[0]),
            np.array(images2[0]),
        )
        return {"type": "image", "diff": diff_img}
