import os
import math
import tempfile
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QMessageBox, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import sys


class PDFGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Creator - Premium Version")
        self.setGeometry(200, 100, 950, 700)
        self.setStyleSheet("""
            QWidget {background-color: #20242c; color: white;}
            QTextEdit {background-color: #2b2f38; color: #f8f8f2; border: 2px solid #444; border-radius: 10px; padding: 10px;}
            QPushButton {
                background-color: #0078d7; border: none; color: white;
                padding: 10px 20px; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover {background-color: #005a9e;}
            QLabel {color: #cccccc;}
        """)

        layout = QVBoxLayout()
        self.label = QLabel("✏️ Nhập nội dung cần in ra PDF (mỗi dòng = 1 mục):")
        self.label.setFont(QFont("Arial", 11))
        layout.addWidget(self.label)

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 11))
        layout.addWidget(self.text_edit)

        self.button_layout = QHBoxLayout()
        self.generate_button = QPushButton("📄 Generate PDF")
        self.generate_button.clicked.connect(self.generate_pdf)
        self.button_layout.addWidget(self.generate_button)
        layout.addLayout(self.button_layout)

        self.setLayout(layout)

    def generate_pdf(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Thiếu dữ liệu", "Vui lòng nhập nội dung trước khi tạo PDF.")
            return

        # Tách dòng
        lines = text.split("\n")

        # Kiểm tra độ dài từng dòng
        long_lines = [line for line in lines if len(line) > 120]
        if long_lines:
            QMessageBox.warning(
                self, "Phát hiện lỗi",
                f"Có {len(long_lines)} dòng vượt quá 120 ký tự:\n\n" +
                "\n".join(f"- {l[:100]}..." for l in long_lines) +
                "\n\nHãy rút ngắn lại để tránh tràn lề."
            )
            return

        # Chọn nơi lưu file
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        # Tạo PDF tạm thời
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(tmp_pdf.name, pagesize=landscape(A3))
        width, height = landscape(A3)

        # Cấu hình lề và font
        top_margin = 20 * mm
        left_margin = 20 * mm
        line_height = 10 * mm
        usable_height = height - 40 * mm  # trừ lề trên + dưới
        lines_per_page = math.floor(usable_height / line_height)

        total_pages = math.ceil(len(lines) / lines_per_page)
        c.setFont("Helvetica", 11)

        for i, line in enumerate(lines):
            page_num = i // lines_per_page + 1
            line_y = height - top_margin - ((i % lines_per_page) * line_height)
            c.drawString(left_margin, line_y, line)

            # Vẽ đường line dưới mỗi dòng
            c.setStrokeColorRGB(0.3, 0.3, 0.3)
            c.setLineWidth(0.3)
            c.line(left_margin, line_y - 2, width - left_margin, line_y - 2)

            # Khi hết trang, chuyển sang trang mới
            if (i + 1) % lines_per_page == 0 and (i + 1) < len(lines):
                # Thêm footer trang trước khi sang trang mới
                footer = f"Page {page_num}/{total_pages} - A3 - NCC"
                c.setFont("Helvetica-Oblique", 9)
                c.drawRightString(width - left_margin, 15 * mm, footer)
                c.showPage()
                c.setFont("Helvetica", 11)

        # Footer cho trang cuối
        footer = f"Page {total_pages}/{total_pages} - A3 - NCC"
        c.setFont("Helvetica-Oblique", 9)
        c.drawRightString(width - left_margin, 15 * mm, footer)

        c.save()
        os.replace(tmp_pdf.name, file_path)

        QMessageBox.information(self, "✅ Thành công", f"Tạo PDF hoàn tất!\nĐã lưu tại:\n{file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PDFGenerator()
    win.show()
    sys.exit(app.exec())
