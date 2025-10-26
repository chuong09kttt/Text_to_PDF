import os
import math
import tempfile
from PIL import Image
from reportlab.lib.pagesizes import A4, A3, A2, A1, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import streamlit as st

# ---------------- CONFIG ----------------
PAPER_SIZES = {
    "A1": A1, "A2": A2, "A3": A3, "A4": A4
}

st.set_page_config(page_title="PDF Generator", page_icon="🧾", layout="centered")

# ---------------- UI ----------------
st.markdown(
    """
    <h2 style='text-align:center; color:#1E88E5;'>📄 PDF Generator Tool</h2>
    """, unsafe_allow_html=True
)

paper_size = st.selectbox("Chọn khổ giấy:", list(PAPER_SIZES.keys()), index=3)
orientation = st.radio("Hướng giấy:", ["Dọc (Portrait)", "Ngang (Landscape)"])
text_color = st.color_picker("Màu chữ:", "#000000")
bg_color = st.color_picker("Màu nền:", "#FFFFFF")

st.write("---")

input_text = st.text_area("Nhập nội dung (mỗi dòng sẽ cách nhau 20mm):", height=250)

uploaded_image = st.file_uploader("Tùy chọn: Chèn hình ảnh (PNG/JPG)", type=["png", "jpg", "jpeg"])

# ---------------- VALIDATION ----------------
if st.button("🖨️ Generate PDF"):
    if not input_text.strip():
        st.error("❌ Vui lòng nhập nội dung trước khi tạo PDF.")
    else:
        lines = input_text.split("\n")
        too_long_lines = [line for line in lines if len(line) > 100]

        if too_long_lines:
            st.error("❌ Một số dòng quá dài (>100 ký tự). Hãy xuống dòng hoặc rút ngắn lại.")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                pdf_path = tmp_file.name

            # Tạo PDF
            page_size = PAPER_SIZES[paper_size]
            if "Ngang" in orientation:
                page_size = landscape(page_size)
            else:
                page_size = portrait(page_size)

            c = canvas.Canvas(pdf_path, pagesize=page_size)

            width, height = page_size
            margin_left = 20 * mm
            top_margin = 20 * mm
            line_spacing = 20 * mm

            # Nền
            c.setFillColor(bg_color)
            c.rect(0, 0, width, height, fill=True, stroke=False)

            # Màu chữ
            c.setFillColor(text_color)
            c.setFont("Helvetica", 12)

            # Dòng đầu tiên cách mép trên 20mm
            y = height - top_margin

            for line in lines:
                if y < 20 * mm:
                    c.showPage()
                    c.setFillColor(bg_color)
                    c.rect(0, 0, width, height, fill=True, stroke=False)
                    c.setFillColor(text_color)
                    c.setFont("Helvetica", 12)
                    y = height - top_margin

                c.drawString(margin_left, y, line)
                y -= line_spacing  # Cách đều 20mm giữa các dòng

            # Đường ngang chính giữa trang
            middle_y = height / 2
            c.setStrokeColor("#999999")
            c.setLineWidth(0.5)
            c.line(0, middle_y, width, middle_y)

            # Hình ảnh (nếu có)
            if uploaded_image:
                image = Image.open(uploaded_image)
                img_width, img_height = image.size
                aspect = img_height / img_width
                display_width = width / 3
                display_height = display_width * aspect
                img_x = width - display_width - 20 * mm
                img_y = 20 * mm
                image_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                image.save(image_path)
                c.drawImage(image_path, img_x, img_y, display_width, display_height)
                os.remove(image_path)

            c.save()

            st.success("✅ PDF đã được tạo thành công!")
            with open(pdf_path, "rb") as f:
                st.download_button("💾 Lưu PDF", f, file_name="output.pdf", mime="application/pdf")
