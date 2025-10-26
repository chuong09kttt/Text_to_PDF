import os
import math
import tempfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, A4, A2, landscape, portrait
from reportlab.lib.units import mm
import streamlit as st

# ================= CONFIG =================
PAPER_SIZES = {"A2": A2, "A3": A3, "A4": A4}
LETTERS_FOLDER = "letters"  # thư mục chứa các ký tự PNG

# ================= PDF FUNCTION =================
def generate_pdf_from_images(lines, pdf_path, paper_choice, orientation_choice, letter_height_mm, footer_text):
    page_size = PAPER_SIZES[paper_choice]
    page_w, page_h = landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))

    margin_left = 20 * mm
    margin_top = 20 * mm
    line_spacing = 20 * mm
    y = page_h - margin_top
    page_number = 1

    all_lines = len(lines)
    line_count = 0

    for line in lines:
        line_count += 1
        x = margin_left

        # Tính chiều rộng dòng
        total_width = 0
        for ch in line:
            if ch == " ":
                total_width += 10 * mm
            else:
                img_path = None
                for candidate in [f"{ch.upper()}.png", f"{ch.lower()}.png"]:
                    p = os.path.join(LETTERS_FOLDER, candidate)
                    if os.path.exists(p):
                        img_path = p
                        break
                if img_path:
                    with Image.open(img_path) as img:
                        w, h = img.size
                        total_width += (letter_height_mm * mm) * (w / h)

        # Vẽ từng ký tự
        for ch in line:
            if ch == " ":
                x += 10 * mm
                continue
            img_path = None
            for candidate in [f"{ch.upper()}.png", f"{ch.lower()}.png"]:
                p = os.path.join(LETTERS_FOLDER, candidate)
                if os.path.exists(p):
                    img_path = p
                    break
            if img_path:
                with Image.open(img_path) as img:
                    w, h = img.size
                    aspect = w / h
                    draw_h = letter_height_mm * mm
                    draw_w = draw_h * aspect
                    c.drawImage(img_path, x, y - draw_h, width=draw_w, height=draw_h, mask='auto')
                    x += draw_w

        # Vẽ đường line giữa các dòng
        c.setStrokeColor("#999999")
        c.setLineWidth(0.5)
        c.line(margin_left, y - line_spacing / 2, page_w - margin_left, y - line_spacing / 2)

        # Dịch xuống dòng
        y -= line_spacing

        # Nếu hết trang
        if y < 40 * mm:
            c.setFont("Helvetica", 10)
            c.drawString(30 * mm, 15 * mm, f"Page {page_number}/{math.ceil(all_lines/20)} - {paper_choice} - {footer_text}")
            c.showPage()
            page_number += 1
            y = page_h - margin_top

    # Đường line ngang giữa trang
    mid_y = page_h / 2
    c.setStrokeColor("#666666")
    c.setLineWidth(1)
    c.line(0, mid_y, page_w, mid_y)

    # Footer cuối
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, 15 * mm, f"Page {page_number}/{math.ceil(all_lines/20)} - {paper_choice} - {footer_text}")
    c.save()

# ================= STREAMLIT UI =================
st.set_page_config(page_title="Smart Text-to-PDF", layout="centered")

st.title("🧠 Smart Text-to-PDF")
st.write("Ứng dụng tạo PDF từ hình chữ PNG, căn dòng chuẩn kỹ thuật, có đường line và footer tự động.")

st.markdown("---")

text_input = st.text_area("✏️ Nhập nội dung (mỗi dòng sẽ cách nhau 20 mm):", height=200)
paper_choice = st.selectbox("📄 Khổ giấy", list(PAPER_SIZES.keys()), index=1)
orientation_choice = st.radio("↔️ Hướng giấy", ["Portrait", "Landscape"], horizontal=True)
letter_height_mm = st.slider("🔠 Chiều cao ký tự (mm)", 5, 30, 10)
footer_text = st.text_input("🏷️ Thông tin thêm (sẽ hiện ở chân trang)", "NCC")

if st.button("📄 Generate PDF"):
    if not text_input.strip():
        st.warning("Vui lòng nhập nội dung trước khi tạo PDF.")
    else:
        lines = [l.strip() for l in text_input.split("\n") if l.strip()]
        missing = []
        for line in lines:
            for ch in line:
                if ch != " ":
                    found = any(os.path.exists(os.path.join(LETTERS_FOLDER, f"{ch.upper()}.png")) or
                                os.path.exists(os.path.join(LETTERS_FOLDER, f"{ch.lower()}.png")) for ch in line)
                    if not found:
                        missing.append(ch)
        if missing:
            st.error(f"Các ký tự sau không có ảnh PNG: {', '.join(set(missing))}")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                generate_pdf_from_images(lines, tmpfile.name, paper_choice, orientation_choice, letter_height_mm, footer_text)
                tmpfile.flush()
                st.success("✅ Tạo PDF thành công!")
                with open(tmpfile.name, "rb") as f:
                    st.download_button("⬇️ Tải về PDF", f, file_name="output.pdf", mime="application/pdf")

st.markdown("---")
st.caption("🧩 Designed by ChatGPT – Streamlit PDF Generator Pro v2")
