import pdfplumber
import fitz
from difflib import Differ, ndiff


class TextProcessor:
    def __init__(self):
        self.differ = Differ()

    def extract_text(self, pdf_path):
        full_text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(x_tolerance=1, y_tolerance=1)
                    if text:
                        full_text.append(text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"Text extraction failed: {e}")
            return ""

    def compare_text(self, text1, text2):
        diff = ndiff(text1.splitlines(), text2.splitlines())
        return self._parse_diff(diff)

    def _parse_diff(self, diff):
        results = []
        for line in diff:
            code = line[0]
            content = line[2:]
            if code == " ":
                continue
            results.append(
                {
                    "type": "added" if code == "+" else "removed",
                    "content": content,
                    "position": None,  # 可添加位置信息
                }
            )
        return results

    def get_page_diffs(self, pdf_path1, pdf_path2):
        """获取每页的文本差异及其位置信息"""
        diffs = []
        with pdfplumber.open(pdf_path1) as pdf1, pdfplumber.open(pdf_path2) as pdf2:
            for page1, page2 in zip(pdf1.pages, pdf2.pages):
                text1 = page1.extract_text(x_tolerance=1, y_tolerance=1) or ""
                text2 = page2.extract_text(x_tolerance=1, y_tolerance=1) or ""
                diff = self.compare_text(text1, text2)
                page_diffs = self._extract_diff_positions(diff, page2)
                diffs.append(page_diffs)
        return diffs

    def _extract_diff_positions(self, diff, page):
        """提取差异位置信息"""
        page_diffs = []
        for line in diff:
            if line["type"] == "added":
                # 查找新增内容在页面中的位置
                positions = self._find_text_positions(line["content"], page)
                for pos in positions:
                    page_diffs.append({"bbox": pos, "type": line["type"]})
        return page_diffs

    def _find_text_positions(self, text, page):
        """在页面中查找文本的位置"""
        positions = []
        for char in page.chars:
            if text in char["text"]:
                positions.append((char["x0"], char["y0"], char["x1"], char["y1"]))
        return positions

    def get_text_positions(self, pdf_path1, pdf_path2):
        """获取精确的文本差异位置信息"""
        diffs = []
        with pdfplumber.open(pdf_path1) as pdf1, pdfplumber.open(pdf_path2) as pdf2:
            for page_num, (page1, page2) in enumerate(zip(pdf1.pages, pdf2.pages)):
                text1 = page1.extract_text() or ""
                text2 = page2.extract_text() or ""
                diff = self.compare_text(text1, text2)

                page_diffs = []
                for d in diff:
                    # 仅处理新增内容
                    if d["type"] == "added":
                        # 使用精确单词匹配
                        words = page2.extract_words(
                            keep_blank_chars=True, x_tolerance=1
                        )
                        target_word = d["content"].strip()

                        # 查找完全匹配的单词
                        matched_words = [
                            w for w in words if w["text"].strip() == target_word
                        ]

                        for word in matched_words:
                            # 坐标转换：pdfplumber坐标系 -> PyMuPDF坐标系
                            rect = fitz.Rect(
                                word["x0"], word["top"], word["x1"], word["bottom"]
                            )
                            page_diffs.append(
                                {"rects": [rect], "color": (1, 1, 0)}  # 黄色高亮
                            )
                diffs.append(page_diffs)
        return diffs


if __name__ == "__main__":
    # 测试代码
    text1 = "Line1\nLine2\nLine3"
    text2 = "Line1\nModified\nLine3"
    processor = TextProcessor()
    mapping = processor._get_line_positions(text1, text2)
    print(mapping)
    # 期望输出: {'added': [1], 'removed': [1]}
