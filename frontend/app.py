import sys
import os
import base64
import asyncio
import streamlit as st

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
        render_side_by_side(file1, file2)

    with tab2:
        render_diff_details(result)


def render_side_by_side(file1, file2):
    """并排对比视图"""
    col1, col2 = st.columns(2)
    with col1:
        render_pdf_preview(file1, "原始文件")
    with col2:
        render_pdf_preview(file2, "对比文件")


def render_pdf_preview(file, title):
    """PDF预览组件"""
    st.markdown(f"**{title}**")
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
    if result.get("type") == "text":
        render_text_diff(result)
    elif result.get("type") == "image":
        render_image_diff(result)


def render_text_diff(result):
    """文本差异渲染"""
    st.subheader("📝 文本差异")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**删除内容**")
        for diff in result.get("removed", []):
            st.markdown(
                f'<div class="highlight-removed">❌ {diff["content"]}</div>',
                unsafe_allow_html=True,
            )

    with cols[1]:
        st.markdown("**新增内容**")
        for diff in result.get("added", []):
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
        st.image(result["original"], use_column_width=True)

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

    # 转换颜色空间
    original_np = np.array(original)
    diff_np = np.array(diff_mask)

    # 创建红色半透明覆盖层
    overlay = original_np.copy()
    overlay[diff_np > 0] = [0, 0, 255]  # BGR格式

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
