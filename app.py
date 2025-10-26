import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
import math

# ------------------- CONFIG -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]
ADMIN_PASSWORD = "admin123"

st.set_page_config(page_title="Smart Text to PDF", layout="wide", page_icon="📄")

# ------------------- CSS -------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
}
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #141E30 0%, #243B55 100%);
}
.main-header {
    color: white; text-align: center; font-weight: 700; font-size: 2.6rem;
    margin-bottom: 2rem; text-shadow: 0px 2px 8px rgba(0,0,0,0.4);
}
.content-card {
    background: rgba(255,255,255,0.98);
    border-radius: 20px; padding: 2rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}
.error-line {
    background-color: #ffcccc;
    border-radius: 6px;
    padding: 3px 6px;
}
.success-msg {
    background: #e8ffe8;
    padding: 10px;
    border-radius: 10px;
    color: #006600;
    font-weight: 600;
}
.char-count {
    color: #888;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.markdown("<h2 style='color:white; text-align:center;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    paper_choice = st.selectbox("📄 Paper size", list(PAPER_SIZES.keys()), index=3)
    orientation_choice = st.selectbox("🔄 Orientation", ["Portrait", "Landscape"], index=0)
    letter_height_mm = st.selectbox("📏 Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=2)

    st.markdown("---")
    st.markdown("<h3 style='color:white;'>🔒 Admin Panel</h3>", unsafe_allow_html=True)
    password = st.text_input("Enter admin password", type="password")

    if password == ADMIN_PASSWORD:
        uploaded_files = st.file_uploader("📤 Upload PNG letters", type=["png"], accept_multiple_files=True)
        if uploaded_files:
            LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
            os.makedirs(LETTERS_FOLDER, exist_ok=True)
            for file in uploaded_files:
                with open(os.path.join(LETTERS_FOLDER, file.name), "wb") as f:
                    f.write(file.getbuffer())
            st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
    else:
        LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
        if not os.path.exists(LETTERS_FOLDER):
            st.error("📁 Letter folder not found. Please contact administrator.")

# ------------------- MAIN UI -------------------
st.markdown("<h1 class='main-header'>🧠 Smart Text-to-PDF Converter</h1>", unsafe_allow_html=True)
st.markdown("<div class='content-card'>", unsafe_allow_html=True)
st.markdown("### ✍️ Enter Your Text")

text_input = st.text_area("", height=300, placeholder="Enter your text here...")

# ------------------- HÀM KIỂM TRA -------------------
def get_missing_chars(lines):
    missing = set()
    for line in lines:
        for ch in line:
            if ch != " ":
                if not any(os.path.exists(os.path.join(LETTERS_FOLDER, c))
                           for c in [f"{ch.upper()}.png", f"{ch.lower()}.png"]):
                    missing.add(ch)
    return missing

def estimate_max_chars(page_size, orientation, letter_height_mm):
    """Ước lượng số ký tự tối đa trong một dòng dựa trên khổ giấy & chiều cao ký tự."""
    page_w, _ = landscape(page_size) if orientation == "Landscape" else portrait(page_size)
    # Mỗi ký tự ~ tỷ lệ 0.7 * chiều cao
    usable_width = page_w - 40 * mm
    avg_char_width = (letter_height_mm * 0.7) * mm
    return math.floor(usable_width / avg_char_width)

def get_too_long_lines(lines, max_chars):
    too_long = []
    for i, line in enumerate(lines):
        if len(line) > max_chars:
            too_long.append(i + 1)
    return too_long

# ------------------- XỬ LÝ NỘI DUNG -------------------
lines = [l.rstrip() for l in text_input.splitlines()]
max_chars = estimate_max_chars(PAPER_SIZES[paper_choice], orientation_choice, letter_height_mm)

preview_html = ""
too_long = []
for i, line in enumerate(lines, start=1):
    length = len(line)
    if length > max_chars:
        too_long.append(i)
        preview_html += f"<div class='error-line'>{i:02d}. {line} <span class='char-count'>({length}/{max_chars})</span></div>"
    else:
        preview_html += f"<div>{i:02d}. {line} <span class='char-count'>({length}/{max_chars})</span></div>"

st.markdown(preview_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------- SINH PDF -------------------
def generate_pdf(lines, pdf_path):
    page_size = PAPER_SIZES[paper_choice]
    page_w, page_h = landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    c.setFont("Helvetica", 12)
    x, y = 50, page_h - 50
    for line in lines:
        c.drawString(x, y, line)
        y -= 18
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = page_h - 50
    c.save()

# ------------------- BUTTON -------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📥 Generate PDF", use_container_width=True):
        if not text_input.strip():
            st.error("⚠️ Please enter at least one line.")
            st.stop()
        if too_long:
            st.error(f"❌ Lines too long: {', '.join(map(str, too_long))} (Max {max_chars} chars)")
            st.stop()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf_path = tmp_pdf.name
        try:
            generate_pdf(lines, pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            st.markdown("<div class='success-msg'>✅ PDF generated successfully!</div>", unsafe_allow_html=True)
            st.download_button("💾 Save PDF", pdf_data, file_name="output.pdf", mime="application/pdf")
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

st.markdown(f"<p style='color:white;text-align:center;'>📏 Limit: {max_chars} chars/line (Paper: {paper_choice}, Height: {letter_height_mm}mm)</p>", unsafe_allow_html=True)
