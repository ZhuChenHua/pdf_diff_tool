import pdfplumber
from difflib import Differ


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
        diff = list(self.differ.compare(text1.splitlines(), text2.splitlines()))
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
