from io import BytesIO
import sys
import os
import base64
import asyncio
import streamlit as st
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

# 设置页面配置
st.set_page_config(layout="wide", page_title="PDF差异分析工具")

# 配置项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.async_utils import async_compare
from src.utils.timer import Timer

# 自定义CSS样式
st.markdown(
    """
<style>
    .st-emotion-cache-1y4p8pa { padding: 2rem 1rem; }
    .highlight-added {
        background: #e6ffe6;
        border-left: 4px solid #4CAF50;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .highlight-removed {
        background: #ffe6e6;
        border-left: 4px solid #FF5252;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .diff-image-container {
        border: 2px solid #FF5252;
        border-radius: 8px;
        padding: 10px;
        margin: 1rem 0;
    }
    .pdf-preview {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""",
    unsafe_allow_html=True,
)


async def main():
    """主应用逻辑"""
    st.title("📑 PDF智能差异分析系统")

    # 文件上传区域
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("上传原始文件", type="pdf")
    with col2:
        file2 = st.file_uploader("上传对比文件", type="pdf")

    if st.button("开始分析", type="primary") and file1 and file2:
        with st.status("分析进行中...", expanded=True) as status:
            with Timer() as timer:
                result = await async_compare(file1, file2)
            status.update(
                label=f"分析完成（耗时 {timer.elapsed:.2f}s）", state="complete"
            )

            # 显示分析结果
            render_comparison_result(file1, file2, result)


def render_comparison_result(file1, file2, result):
    """渲染对比结果"""
    st.subheader("🔍 分析结果")

    # 创建标签页布局
    tab1, tab2 = st.tabs(["并排对比", "差异详情"])

    with tab1:
        render_side_by_side(file1, file2, result)

    with tab2:
        render_diff_details(result)


def render_side_by_side(file1, file2, result=None):
    col1, col2 = st.columns(2)
    with col1:
        show_pdf(file1.getvalue(), "原始文件")
    with col2:
        if result and isinstance(result, dict):  # 添加类型检查
            if "annotated_pdf" in result and os.path.exists(result["annotated_pdf"]):
                try:
                    with open(result["annotated_pdf"], "rb") as f:
                        show_pdf(f.read(), "对比文件（差异标注）")
                except Exception as e:
                    st.error(f"加载标注文件失败: {str(e)}")
            else:
                show_pdf(file2.getvalue(), "对比文件")
        else:
            show_pdf(file2.getvalue(), "对比文件")


def show_pdf(pdf_bytes, title):
    """通用PDF展示组件"""
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f"""
    <div class="pdf-preview">
        <embed src="data:application/pdf;base64,{base64_pdf}" 
             width="100%" 
             height="800px" 
             type="application/pdf">
    </div>"""
    st.markdown(f"**{title}**")
    st.markdown(pdf_display, unsafe_allow_html=True)


def render_annotated_pdf(file, result):
    """在 PDF 中高亮显示差异"""
    st.markdown("**对比文件（差异高亮）**")
    annotated_pdf = highlight_differences(file, result)
    render_pdf_preview(annotated_pdf, "高亮后的PDF")


def highlight_differences(file, result):
    """在 PDF 页面上高亮显示差异"""
    from reportlab.lib.units import inch

    # 打开源 PDF 文件
    source_pdf = PdfReader(file)
    output_pdf = PdfWriter()
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    with pdfplumber.open(file) as pdf:
        for page_num, page in enumerate(pdf.pages):
            if page_num >= len(result["diffs"]):
                break
            diffs = result["diffs"][page_num]
            for diff in diffs:
                x0, y0, x1, y1 = diff["bbox"]
                can.setFillColorRGB(1, 0, 0, alpha=0.3)  # 红色半透明
                can.rect(
                    x0 * inch,
                    (page.height - y1) * inch,
                    (x1 - x0) * inch,
                    (y1 - y0) * inch,
                    fill=1,
                )
            can.showPage()  # 为每一页结束添加页面

    can.save()

    # 将高亮内容合并到原始 PDF
    packet.seek(0)
    highlight_pdf = PdfReader(packet)

    for page_num in range(len(source_pdf.pages)):
        source_page = source_pdf.pages[page_num]
        if page_num < len(highlight_pdf.pages):
            highlight_page = highlight_pdf.pages[page_num]
            source_page.merge_page(highlight_page)
        output_pdf.add_page(source_page)

    # 返回合并后的 PDF 内容
    output_stream = BytesIO()
    output_pdf.write(output_stream)
    output_stream.seek(0)
    return output_stream


def render_pdf_preview(file, title):
    """PDF预览组件"""
    st.markdown(f"**{title}**")
    if isinstance(file, BytesIO):
        base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
    else:
        base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
    pdf_display = f"""
    <div class="pdf-preview">
        <embed src="data:application/pdf;base64,{base64_pdf}" 
             width="100%" 
             height="800px" 
             type="application/pdf">
    </div>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)


def render_diff_details(result):
    """差异详情渲染"""
    if "type" not in result:
        st.error("无效的分析结果")
        return

    try:
        if result["type"] == "text":
            # 验证文本结果结构
            if "details" not in result:
                raise KeyError("缺少文本差异详情数据")
            render_text_diff(result)

        elif result["type"] == "image":
            # 验证图像结果结构
            required_keys = ["original", "diff"]
            for key in required_keys:
                if key not in result:
                    raise KeyError(f"缺失必要字段: {key}")
            render_image_diff(result)

    except KeyError as e:
        st.error(f"数据格式错误: {str(e)}")
    except Exception as e:
        st.error(f"渲染失败: {str(e)}")


def render_text_diff(result):
    st.subheader("📝 文本差异")

    # 从details中分离不同类型
    removed = [d for d in result["details"] if d["type"] == "removed"]
    added = [d for d in result["details"] if d["type"] == "added"]

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**删除内容**")
        for diff in removed:
            st.markdown(
                f'<div class="highlight-removed">❌ {diff["content"]}</div>',
                unsafe_allow_html=True,
            )

    with cols[1]:
        st.markdown("**新增内容**")
        for diff in added:
            st.markdown(
                f'<div class="highlight-added">✅ {diff["content"]}</div>',
                unsafe_allow_html=True,
            )


def render_image_diff(result):
    """图像差异渲染"""
    st.subheader("🖼️ 图像差异")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**原始图像**")
        st.image(result["original"], use_column_width=True)  # 使用原始图像数据

    with col2:
        st.markdown("**差异标记**")
        st.markdown('<div class="diff-image-container">', unsafe_allow_html=True)
        annotated_img = annotate_diff_image(result["original"], result["diff"])
        st.image(annotated_img, use_column_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def annotate_diff_image(original, diff_mask):
    """图像差异标注"""
    import cv2
    import numpy as np

    original_np = np.array(original)
    diff_np = np.array(diff_mask)

    # 创建红色半透明覆盖层
    overlay = original_np.copy()
    # 使用广播机制确保赋值的输入值数量与布尔掩码为 True 的位置数量匹配
    overlay[diff_np > 0] = np.array([0, 0, 255])

    # 混合图像
    alpha = 0.3
    cv2.addWeighted(overlay, alpha, original_np, 1 - alpha, 0, original_np)

    # 绘制边界框
    contours, _ = cv2.findContours(diff_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(original_np, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return original_np


if __name__ == "__main__":
    asyncio.run(main())
