import os
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image

# ------------------- CONFIG -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTERS_FOLDER = "letters"  # thư mục chứa ảnh ký tự
paper_choice = "A3"
orientation_choice = "Portrait"
letter_height_mm = 15  # chiều cao chữ (mm)


# ------------------- MAIN FUNCTION -------------------
def generate_pdf_from_images(lines, pdf_path):
    page_size = PAPER_SIZES[paper_choice]
    page_w, page_h = (
        landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    )
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))

    # --- Cấu hình ---
    top_margin = 20 * mm           # dòng đầu cách mép trên 20mm
    side_margin = 20 * mm          # căn trái 20mm
    border_margin = 2 * mm
    footer_y = 15 * mm
    line_gap = 20 * mm             # khoảng cách giữa hai dòng
    line_height = letter_height_mm * mm
    separator_pos = line_gap / 2   # vị trí line ngang giữa hai dòng

    # --- Tính số dòng mỗi trang ---
    usable_height = page_h - top_margin - 60 * mm
    lines_per_page = int(usable_height // line_gap)
    total_pages = math.ceil(len(lines) / lines_per_page)

    page_number = 1
    y = page_h - top_margin  # vị trí dòng đầu tiên

    for i, line in enumerate(lines, start=1):
        x = side_margin

        # --- Vẽ ký tự ---
        for ch in line:
            if ch == " ":
                x += 8 * mm
                continue
            for candidate in [f"{ch.upper()}.png", f"{ch.lower()}.png"]:
                img_path = os.path.join(LETTERS_FOLDER, candidate)
                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        w, h = img.size
                        aspect = w / h
                        draw_h = line_height
                        draw_w = draw_h * aspect
                        c.drawImage(img_path, x, y - draw_h, width=draw_w, height=draw_h, mask='auto')
                        x += draw_w
                    break

        # --- Vẽ line ngang giữa hai dòng ---
        mid_y = y - separator_pos
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.line(side_margin, mid_y, page_w - side_margin, mid_y)

        # --- Dòng tiếp theo ---
        y -= line_gap

        # --- Nếu hết trang hoặc hết dữ liệu ---
        if (i % lines_per_page == 0) or (i == len(lines)):
            # Viền đỏ
            c.setStrokeColorRGB(1, 0, 0)
            c.setLineWidth(1)
            c.rect(border_margin, border_margin, page_w - 2 * border_margin, page_h - 2 * border_margin)

            # Footer
            c.setFont("Helvetica", 10)
            footer_text = f"Page {page_number}/{total_pages} - {paper_choice} - NCC"
            text_width = c.stringWidth(footer_text, "Helvetica", 10)
            c.drawString((page_w - text_width) / 2, footer_y, footer_text)

            # Trang mới
            if i != len(lines):
                c.showPage()
                y = page_h - top_margin
                page_number += 1

    c.save()


# ------------------- DEMO -------------------
if __name__ == "__main__":
    lines = [
        "HELLO WORLD",
        "PYTHON PDF TEST",
        "THIS IS LINE 3",
        "TESTING 20MM GAP",
        "LINE ALIGNMENT CHECK",
        "END OF PAGE TEST"
    ]
    generate_pdf_from_images(lines, "output.pdf")
    print("✅ PDF generated successfully: output.pdf")
