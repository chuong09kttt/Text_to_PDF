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
.warn-line {
    background-color: #fff5cc;
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
        uploaded_files = st.file_uploader("📤 Upload PNG letters (A.png, a.png ...)", type=["png"], accept_multiple_files=True)
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

# ------------------- HÀM HỖ TRỢ -------------------
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
    page_w, _ = landscape(page_size) if orientation == "Landscape" else portrait(page_size)
    usable_width = page_w - 40 * mm  # lề 20mm hai bên
    avg_char_width = (letter_height_mm * 0.7) * mm
    return math.floor(usable_width / avg_char_width)

def line_pixel_width_mm(line, letter_height_mm, space_width_ratio=0.5):
    """
    Tính tổng chiều ngang (mm) của 1 dòng khi ghép ảnh.
    Nếu ký tự không có ảnh, cộng một giá trị lớn (để báo lỗi).
    """
    total_mm = 0.0
    for ch in line:
        if ch == " ":
            total_mm += letter_height_mm * space_width_ratio
            continue
        img_path = None
        for name in (f"{ch.upper()}.png", f"{ch.lower()}.png"):
            candidate = os.path.join(LETTERS_FOLDER, name)
            if os.path.exists(candidate):
                img_path = candidate
                break
        if img_path:
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
                    aspect = w / h
                    width_mm = letter_height_mm * aspect
                    total_mm += width_mm + 1  # +1mm khoảng cách giữa ký tự
            except:
                total_mm += letter_height_mm * 0.9  # fallback
        else:
            # không có ảnh ký tự -> coi là lỗi rất lớn để không cho xuất
            total_mm += (letter_height_mm * 2)
    return total_mm

def get_too_wide_lines(lines, page_size, orientation, letter_height_mm):
    page_w, _ = landscape(page_size) if orientation == "Landscape" else portrait(page_size)
    usable_width_mm = (page_w - 40 * mm) / mm  # convert to mm number
    too_wide = []
    for i, line in enumerate(lines):
        width_mm = line_pixel_width_mm(line, letter_height_mm)  # mm
        if width_mm > usable_width_mm:
            too_wide.append((i + 1, width_mm, usable_width_mm))
    return too_wide

# ------------------- XỬ LÝ NỘI DUNG -------------------
lines = [l.rstrip() for l in text_input.splitlines()]
max_chars = estimate_max_chars(PAPER_SIZES[paper_choice], orientation_choice, letter_height_mm)

# Kiểm tra lỗi cơ bản
missing_chars = get_missing_chars(lines)
too_long_by_chars = [i+1 for i,l in enumerate(lines) if len(l) > max_chars]
too_wide_info = get_too_wide_lines(lines, PAPER_SIZES[paper_choice], orientation_choice, letter_height_mm)
too_wide_lines = [t[0] for t in too_wide_info]

# Chuẩn bị preview: nếu lỗi (ký tự/chiều ngang) tô đỏ
preview_html = ""
for i, line in enumerate(lines, start=1):
    length = len(line)
    note = f"<span class='char-count'>({length}/{max_chars})</span>"
    if i in too_long_by_chars and i in too_wide_lines:
        preview_html += f"<div class='error-line'>{i:02d}. {line} &nbsp;<strong style='color:#900;'>(Vượt cả ký tự & chiều ngang)</strong> {note}</div>"
    elif i in too_long_by_chars:
        preview_html += f"<div class='warn-line'>{i:02d}. {line} &nbsp;<strong style='color:#a65;'>(Vượt ký tự)</strong> {note}</div>"
    elif i in too_wide_lines:
        # thêm chiều rộng thực tế
        info = next((t for t in too_wide_info if t[0] == i), None)
        if info:
            preview_html += f"<div class='warn-line'>{i:02d}. {line} &nbsp;<strong style='color:#a65;'>(Chiều ngang: {info[1]:.1f}mm / {info[2]:.1f}mm)</strong> {note}</div>"
        else:
            preview_html += f"<div class='warn-line'>{i:02d}. {line} &nbsp;<strong style='color:#a65;'>(Chiều ngang vượt)</strong> {note}</div>"
    else:
        preview_html += f"<div>{i:02d}. {line} {note}</div>"

st.markdown(preview_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------- SINH PDF BẰNG ẢNH -------------------
def generate_pdf_with_images(lines, pdf_path):
    page_size = PAPER_SIZES[paper_choice]
    page_w, page_h = landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))

    y = page_h - letter_height_mm * mm - 20
    for line in lines:
        x = 20*mm
        for ch in line:
            if ch == " ":
                x += letter_height_mm * 0.5 * mm
                continue
            # tìm file ảnh
            img_path = None
            for name in (f"{ch.upper()}.png", f"{ch.lower()}.png"):
                candidate = os.path.join(LETTERS_FOLDER, name)
                if os.path.exists(candidate):
                    img_path = candidate
                    break
            if not img_path:
                # bỏ qua ký tự không có ảnh (không nên xảy ra vì đã check trước)
                continue

            img = Image.open(img_path)
            w, h = img.size
            aspect = w / h
            new_w = letter_height_mm * aspect * mm
            new_h = letter_height_mm * mm

            # nếu sắp vượt giới hạn trang theo chiều ngang -> xuống dòng
            if x + new_w > (page_w - 20*mm):
                y -= new_h + 5*mm
                x = 20*mm

            c.drawImage(img_path, x, y, width=new_w, height=new_h, mask='auto')
            x += new_w + 1*mm  # khoảng cách nhỏ giữa ký tự

        y -= letter_height_mm * 1.2 * mm
        if y < 50*mm:
            c.showPage()
            y = page_h - letter_height_mm * mm - 20*mm
    c.save()

# ------------------- BUTTON -------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📥 Generate PDF", use_container_width=True):
        # re-check trước khi sinh
        if not text_input.strip():
            st.error("⚠️ Please enter at least one line.")
            st.stop()

        missing_chars = get_missing_chars(lines)
        too_long_by_chars = [i+1 for i,l in enumerate(lines) if len(l) > max_chars]
        too_wide_info = get_too_wide_lines(lines, PAPER_SIZES[paper_choice], orientation_choice, letter_height_mm)
        too_wide_lines = [t[0] for t in too_wide_info]

        errors = []
        if missing_chars:
            errors.append(f"❌ Missing PNG letters: {', '.join(sorted(missing_chars))}")
        if too_long_by_chars:
            errors.append(f"❌ Lines too long by char count: {', '.join(map(str, too_long_by_chars))} (max {max_chars})")
        if too_wide_info:
            errors.append("❌ Lines too wide for selected paper (by image widths): " +
                          ", ".join(f"{t[0]} ({t[1]:.1f}mm > {t[2]:.1f}mm)" for t in too_wide_info))

        if errors:
            # hiển thị lỗi chi tiết và preview đã tô
            for e in errors:
                st.error(e)
            st.stop()

        # nếu không có lỗi thì sinh PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf_path = tmp_pdf.name
        try:
            generate_pdf_with_images(lines, pdf_path)
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            st.markdown("<div class='success-msg'>✅ PDF generated successfully!</div>", unsafe_allow_html=True)
            st.download_button("💾 Save PDF", pdf_data, file_name="output.pdf", mime="application/pdf")
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

st.markdown(f"<p style='color:white;text-align:center;'>📏 Limit: {max_chars} chars/line (Paper: {paper_choice}, Height: {letter_height_mm}mm)</p>", unsafe_allow_html=True)
