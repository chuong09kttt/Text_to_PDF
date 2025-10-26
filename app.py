import os
import tempfile
from reportlab.lib.pagesizes import A4, A3, A2, A1, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PIL import Image
import streamlit as st

# ---------------- CONFIG ----------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}

st.set_page_config(page_title="PDF Generator", page_icon="🧾", layout="centered")

# ---------------- UI ----------------
st.markdown("<h2 style='text-align:center; color:#2196F3;'>🧾 PDF Generator</h2>", unsafe_allow_html=True)
st.write("")

paper_size = st.selectbox("Chọn khổ giấy:", list(PAPER_SIZES.keys()), index=3)
orientation = st.radio("Hướng giấy:", ["Dọc (Portrait)", "Ngang (Landscape)"])
text_color = st.color_picker("Màu chữ:", "#000000")
bg_color = st.color_picker("Màu nền:", "#FFFFFF")

input_text = st.text_area("Nhập nội dung (mỗi dòng cách nhau 20mm):", height=250)
uploaded_image = st.file_uploader("Tùy chọn: chèn ảnh (PNG/JPG)", type=["png", "jpg", "jpeg"])

# ---------------- PROCESS ----------------
if st.button("🖨️ Generate PDF"):
    if not input_text.strip():
        st.error("❌ Vui lòng nhập nội dung trước khi tạo PDF.")
    else:
        # Kiểm tra dòng quá dài
        lines = input_text.split("\n")
        long_lines = [line for line in lines if len(line) > 100]
        if long_lines:
            st.error("❌ Một số dòng quá dài (>100 ký tự). Hãy xuống dòng hoặc rút ngắn lại.")
        else:
            # Tạo file tạm
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_path = tmp.name

            # Cấu hình PDF
            page_size = PAPER_SIZES[paper_size]
            if "Ngang" in orientation:
                page_size = landscape(page_size)
            else:
                page_size = portrait(page_size)

            c = canvas.Canvas(pdf_path, pagesize=page_size)
            width, height = page_size

            # Cấu hình lề
            margin_left = 20 * mm
            margin_top = 20 * mm
            line_spacing = 20 * mm

            # Vẽ nền
            c.setFillColor(bg_color)
            c.rect(0, 0, width, height, fill=True, stroke=False)

            # Vẽ chữ
            c.setFont("Helvetica", 12)
            c.setFillColor(text_color)

            y = height - margin_top  # Dòng đầu tiên cách mép trên 20 mm

            for line in lines:
                if y < margin_top:
                    # Sang trang mới nếu hết chỗ
                    c.showPage()
                    c.setFillColor(bg_color)
                    c.rect(0, 0, width, height, fill=True, stroke=False)
                    c.setFont("Helvetica", 12)
                    c.setFillColor(text_color)
                    y = height - margin_top

                c.drawString(margin_left, y, line)
                y -= line_spacing  # Giữ khoảng cách dòng đều 20 mm

            # Vẽ đường ngang chính giữa
            mid_y = height / 2
            c.setStrokeColor("#999999")
            c.setLineWidth(0.8)
            c.line(0, mid_y, width, mid_y)

            # Chèn ảnh nếu có
            if uploaded_image:
                img = Image.open(uploaded_image)
                img_w, img_h = img.size
                aspect = img_h / img_w
                display_w = width / 3
                display_h = display_w * aspect
                img_x = width - display_w - 20 * mm
                img_y = 20 * mm
                temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img.save(temp_img.name)
                c.drawImage(temp_img.name, img_x, img_y, display_w, display_h)
                os.remove(temp_img.name)

            c.save()

            # Hiển thị nút tải PDF
            st.success("✅ PDF đã tạo thành công!")
            with open(pdf_path, "rb") as f:
                st.download_button("💾 Tải PDF", f, file_name="output.pdf", mime="application/pdf")
