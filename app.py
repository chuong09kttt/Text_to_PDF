import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile

# ------------------- CONFIG -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]
ADMIN_PASSWORD = "admin123"

st.set_page_config(page_title="Text to PDF Converter", layout="wide", page_icon="📄")

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
    color: white; text-align: center; font-weight: 700; font-size: 2.8rem;
    margin-bottom: 2rem; text-shadow: 0px 2px 6px rgba(0,0,0,0.3);
}
.content-card {
    background: rgba(255,255,255,0.97);
    border-radius: 20px; padding: 2.5rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.stButton>button {
    background: linear-gradient(45deg, #36D1DC, #5B86E5);
    color: white; border: none; border-radius: 12px;
    padding: 0.8rem 2rem; font-weight: 600; font-size: 1.1rem;
    transition: all 0.3s ease; width: 100%;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(91,134,229,0.5);
}
.stTextArea textarea {
    border-radius: 14px; border: 2px solid #e0e0e0;
    font-family: 'Courier New', monospace; font-size: 16px;
}
.stTextArea textarea:focus {
    border-color: #5B86E5;
    box-shadow: 0 0 0 3px rgba(91,134,229,0.2);
}
.custom-view {
    width: 100%;
    border-radius: 14px;
    border: 2px solid #e74c3c;
    font-family: 'Courier New', monospace;
    padding: 10px;
    background: white;
    height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    font-size: 16px;
}
.error-line { background-color: #ffb3b3; }
</style>
""", unsafe_allow_html=True)

# ------------------- SIDEBAR -------------------
with st.sidebar:
    st.markdown("<h2 style='color:white; text-align:center;'>⚙️ Settings</h2>", unsafe_allow_html=True)
    paper_choice = st.selectbox("📄 Paper size", list(PAPER_SIZES.keys()), index=2)
    orientation_choice = st.selectbox("🔄 Orientation", ["Portrait", "Landscape"], index=1)
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
st.markdown("<h1 class='main-header'>📄 Text to PDF Converter</h1>", unsafe_allow_html=True)
st.markdown("<div class='content-card'>", unsafe_allow_html=True)
st.markdown("### ✍️ Enter Your Text")

text_input_key = "main_text"
text_input = st.text_area("", height=300, placeholder="Enter your text here...", key=text_input_key)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------- HELPER FUNCTIONS -------------------
def get_missing_chars(lines):
    missing = set()
    for line in lines:
        for ch in line:
            if ch != " ":
                if not any(os.path.exists(os.path.join(LETTERS_FOLDER, c))
                           for c in [f"{ch.upper()}.png", f"{ch.lower()}.png"]):
                    missing.add(ch)
    return missing

def check_line_width(line, page_w, letter_height_mm, margin_x=20*mm, space_width=15*mm):
    x = margin_x
    letter_height = letter_height_mm * mm
    for ch in line:
        if ch == " ":
            x += space_width
            continue
        candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
        img_path = next((os.path.join(LETTERS_FOLDER, c)
                         for c in candidates if os.path.exists(os.path.join(LETTERS_FOLDER, c))), None)
        if img_path:
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
                    x += letter_height * (w/h) + 5*mm
            except:
                x += 50*mm
        else:
            x += 50*mm
    return x > (page_w - margin_x)

def get_too_long_lines(lines, letter_height_mm):
    page_size = PAPER_SIZES[paper_choice]
    page_w, _ = landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    too_long = []
    for i, line in enumerate(lines):
        if check_line_width(line, page_w, letter_height_mm):
            too_long.append(i + 1)
    return too_long

def generate_pdf(lines, pdf_path, letter_height_mm):
    page_size = PAPER_SIZES[paper_choice]
    page_w, page_h = landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    letter_height = letter_height_mm * mm
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    margin_x, margin_y = 2*mm, 2*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height

    char_dimensions = {}
    for ch in set("".join(lines)):
        candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
        img_path = next((os.path.join(LETTERS_FOLDER, c))
                        for c in candidates if os.path.exists(os.path.join(LETTERS_FOLDER, c))), None)
        if img_path:
            with Image.open(img_path) as im:
                char_dimensions[ch] = im.size

    for line in lines:
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
        x = margin_x
        for ch in line:
            if ch == " ":
                x += 15*mm
                continue
            candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
            img_path = next((os.path.join(LETTERS_FOLDER, c))
                            for c in candidates if os.path.exists(os.path.join(LETTERS_FOLDER, c))), None)
            if img_path:
                w, h = char_dimensions[ch]
                c.drawImage(img_path, x, current_y, width=letter_height*w/h, height=letter_height, mask='auto')
                x += letter_height * (w/h) + 5*mm
        current_y -= (letter_height + line_spacing)
    c.save()

# ------------------- BUTTON -------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📥 Generate PDF", use_container_width=True):
        lines = [l.strip() for l in text_input.splitlines() if l.strip()]
        if not lines:
            st.error("⚠️ Please enter at least one line.")
            st.stop()

        missing = get_missing_chars(lines)
        too_long = get_too_long_lines(lines, letter_height_mm)

        # === NEW: hiển thị dòng lỗi ngay trong ô nhập ===
        if missing or too_long:
            html_lines = []
            for i, line in enumerate(lines, start=1):
                if i in too_long:
                    html_lines.append(f"<div class='error-line'>{line}</div>")
                else:
                    html_lines.append(f"<div>{line}</div>")
            st.markdown(
                "<div class='custom-view'>" + "".join(html_lines) + "</div>",
                unsafe_allow_html=True
            )

            if missing:
                st.error(f"❌ Missing PNG letters: {', '.join(sorted(missing))}")
            if too_long:
                st.error(f"❌ Lines too long: {', '.join(map(str, too_long))}")
            st.stop()

        # === Nếu không lỗi thì sinh PDF ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf_path = tmp_pdf.name
        try:
            generate_pdf(lines, pdf_path, letter_height_mm)
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            st.success("✅ PDF generated successfully!")
            st.download_button("💾 Save PDF", pdf_data, file_name="document.pdf", mime="application/pdf")
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
