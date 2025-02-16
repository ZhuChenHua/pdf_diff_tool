import fitz
import cv2
import numpy as np


class PDFAnnotator:
    @staticmethod
    def highlight_text_diffs(pdf_path, diffs, output_path):
        """在PDF文本中标注差异"""
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            if page_num >= len(diffs):
                break
            for diff in diffs[page_num]:
                for rect in diff["rects"]:
                    annot = page.add_highlight_annot(rect)
                    annot.set_colors(stroke=diff["color"])
        doc.save(output_path)
        doc.close()

    @staticmethod
    def annotate_image_diffs(pdf_path, diff_mask, output_path):
        """在PDF图像页面标注差异"""
        doc = fitz.open(pdf_path)
        page = doc[0]
        img = cv2.imread(diff_mask)
        img_bytes = cv2.imencode(".png", img)[1].tobytes()
        rect = fitz.Rect(0, 0, page.rect.width, page.rect.height)
        page.insert_image(rect, stream=img_bytes, overlay=True)
        doc.save(output_path)
        doc.close()
