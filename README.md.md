项目概述
本项目是一个用于分析两个 PDF 文件差异的工具，支持文本型和图像型 PDF 文件的比较。它结合了启发式规则和深度学习模型，能够高效准确地检测出两个 PDF 文件之间的差异。

技术解析
整体架构
项目主要分为前端和后端两部分：

前端：使用 Streamlit 构建用户界面，提供文件上传和结果展示功能。
后端：包含多个模块，负责 PDF 文件的分类、文本提取、图像转换和差异比较等任务。
核心模块

1. PDF 分类器 (src/pdf_processing/classifier.py)
   功能：区分文本型和图像型 PDF 文件。
   技术实现：
   启发式规则：通过提取 PDF 前几页的文本内容，计算文本页面的比例，若比例超过设定阈值，则判定为文本型 PDF。
   深度学习模型：使用预训练的 ResNet18 模型，对 PDF 的第一页进行图像分类，根据分类结果进一步确认文件类型。
2. 文本处理器 (src/pdf_processing/text_processor.py)
   功能：提取 PDF 文件中的文本内容，并比较两个文本内容的差异。
   技术实现：
   文本提取：使用 pdfplumber 库逐页提取 PDF 中的文本。
   差异比较：使用 difflib.Differ 比较两个文本的差异，并将结果整理成易于展示的格式。
3. 图像处理处理器 (src/pdf_processing/image_processor.py)
   功能：将 PDF 文件转换为图像，并对图像进行预处理。
   技术实现：
   PDF 转图像：使用 pdf2image 库将 PDF 文件转换为图像。
   图像预处理：使用 OpenCV 和 torchvision 对图像进行颜色转换、缩放和归一化处理。
4. 异步处理工具 (src/utils/async_utils.py)
   功能：异步处理文件比较任务，提高处理效率。
   技术实现：使用 asyncio 和 ThreadPoolExecutor 实现异步文件处理和比较。
   前端界面 (frontend/app.py)
   功能：提供用户界面，允许用户上传两个 PDF 文件，并展示比较结果。
   技术实现：使用 Streamlit 构建交互式界面，通过 asyncio 异步调用后端处理函数。
   项目运行方案
   环境准备
   安装 Anaconda 或 Miniconda。
   创建并激活虚拟环境：

bash
conda create -n pdf_diff_tool python=3.10
conda activate pdf_diff_tool
安装项目依赖：

bash
pip install -r requirements.txt
运行项目
确保项目根目录下的 requirements.txt 文件中的所有依赖都已正确安装。
在终端中运行以下命令启动 Streamlit 应用：

bash
streamlit run frontend/app.py
打开浏览器，访问 http://localhost:8501，即可看到项目界面。
上传两个 PDF 文件，点击“开始比较”按钮，等待比较结果。
注意事项
确保系统中已安装 Poppler 库，用于 pdf2image 库的 PDF 转图像功能。
若使用 GPU 加速，请确保系统中已正确安装 CUDA 和 cuDNN。
贡献与反馈
如果你对本项目有任何建议或发现了问题，请在项目的 GitHub 仓库中提交 issue 或 pull request。

许可证
本项目采用 MIT 许可证。
