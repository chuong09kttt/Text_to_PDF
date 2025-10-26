import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ================= CẤU HÌNH =================
PAGE_WIDTH, PAGE_HEIGHT = A4
FONT_SIZE = 12
MAX_CHAR_PER_LINE = int((PAGE_WIDTH - 100) / (FONT_SIZE * 0.55))  # Ước lượng độ dài ký tự

st.set_page_config(page_title="Smart PDF Generator", page_icon="📄", layout="centered")

st.markdown("""
    <style>
    .error-line {
        background-color: rgba(255, 100, 100, 0.3);
        border-radius: 4px;
        padding: 2px 6px;
        display: inline-block;
        width: 100%;
    }
    textarea {
        font-family: "Consolas", monospace !important;
        font-size: 15px !important;
    }
    .success-box {
        background-color: #e6ffed;
        padding: 10px;
        border-radius: 6px;
        color: #006600;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎨 Smart PDF Generator")
st.write("Nhập nội dung của bạn bên dưới. Mỗi dòng quá dài sẽ được tô **đỏ** và hiển thị số ký tự giới hạn.")

# ================= NHẬP NỘI DUNG =================
text_input = st.text_area("Nhập nội dung", height=250, placeholder="Nhập từng dòng...")

lines = text_input.split("\n")
error_lines = []
preview_html = ""

for idx, line in enumerate(lines, start=1):
    length = len(line)
    if length > MAX_CHAR_PER_LINE:
        error_lines.append(idx)
        preview_html += f'<div class="error-line">{idx:02d}. {line} &nbsp;<span style="color:red;">({length}/{MAX_CHAR_PER_LINE})</span></div>'
    else:
        preview_html += f'<div>{idx:02d}. {line} <span style="color:gray;">({length}/{MAX_CHAR_PER_LINE})</span></div>'

st.markdown(preview_html, unsafe_allow_html=True)

# ================= NÚT XUẤT PDF =================
if st.button("📄 Generate PDF"):
    if error_lines:
        st.error(f"⚠️ Không thể xuất PDF! Các dòng {error_lines} vượt quá giới hạn {MAX_CHAR_PER_LINE} ký tự.")
    else:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setFont("Helvetica", FONT_SIZE)
        x, y = 50, PAGE_HEIGHT - 50

        for line in lines:
            c.drawString(x, y, line)
            y -= FONT_SIZE + 4
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", FONT_SIZE)
                y = PAGE_HEIGHT - 50

        c.save()
        buffer.seek(0)
        st.download_button(
            label="💾 Lưu PDF",
            data=buffer,
            file_name="output.pdf",
            mime="application/pdf"
        )
        st.markdown('<div class="success-box">✅ PDF đã sẵn sàng để lưu!</div>', unsafe_allow_html=True)

# ================= GỢI Ý =================
st.markdown("---")
st.caption(f"📏 Giới hạn hiện tại: {MAX_CHAR_PER_LINE} ký tự mỗi dòng (tương ứng cỡ chữ {FONT_SIZE} trên khổ A4).")
