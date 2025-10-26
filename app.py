import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile

# -------------------
# Config
# -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]
ADMIN_PASSWORD = "admin123"

st.set_page_config(page_title="Text to PDF", layout="wide")

# -------------------
# CSS for alerts
# -------------------
st.markdown("""
<style>
.stAlert {border-radius: 10px; padding: 15px; font-weight: bold; font-size:16px; margin-bottom:10px;}
.alert-success {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
.alert-warning {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
.alert-error {background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;}
</style>
""", unsafe_allow_html=True)

# -------------------
# Sidebar
# -------------------
st.sidebar.title("Settings")
paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox("Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=2)

# -------------------
# Admin upload letters
# -------------------
st.sidebar.subheader("Admin Upload")
password = st.sidebar.text_input("Enter admin password", type="password")
if password == ADMIN_PASSWORD:
    uploaded_files = st.sidebar.file_uploader("Upload PNG letters", type=["png","PNG"], accept_multiple_files=True)
    if uploaded_files:
        LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
        os.makedirs(LETTERS_FOLDER, exist_ok=True)
        for file in uploaded_files:
            with open(os.path.join(LETTERS_FOLDER, file.name), "wb") as f:
                f.write(file.getbuffer())
        st.sidebar.success(f"{len(uploaded_files)} files uploaded to ABC folder.")
else:
    LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
    if not os.path.exists(LETTERS_FOLDER):
        st.error(f"Folder {LETTERS_FOLDER} not found. Please ask admin to upload letter PNG files.")
        st.stop()

# -------------------
# Text input
# -------------------
st.header("Text to PDF")
text_input = st.text_area("Enter lines of text:", height=300, placeholder="Line 1\nLine 2\nLine 3...")

# -------------------
# Helper functions
# -------------------
def check_missing_chars(lines):
    missing_chars = set()
    for line in lines:
        for ch in line:
            if ch != " ":
                # check both lower and upper
                candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
                if not any(os.path.exists(os.path.join(LETTERS_FOLDER, c)) for c in candidates):
                    missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm, letter_height=100*mm):
    x = margin_x
    for ch in line:
        if ch == " ":
            x += space_width
            continue
        candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
        img_path = next((os.path.join(LETTERS_FOLDER, c) for c in candidates if os.path.exists(os.path.join(LETTERS_FOLDER, c))), None)
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

def generate_pdf(lines, pdf_path, letter_height_mm):
    page_size = PAPER_SIZES[paper_choice]
    if orientation_choice == "Landscape":
        page_w, page_h = landscape(page_size)
    else:
        page_w, page_h = portrait(page_size)

    letter_height = letter_height_mm * mm
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    margin_x = 5*mm
    margin_y = 5*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height

    # Preload char dimensions
    char_dimensions = {}
    unique_chars = set("".join(lines))
    for ch in unique_chars:
        candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
        img_path = next((os.path.join(LETTERS_FOLDER, c) for c in candidates if os.path.exists(os.path.join(LETTERS_FOLDER, c))), None)
        if img_path:
            with Image.open(img_path) as im:
                char_dimensions[ch] = im.size

    page_num = 1
    lines_per_page = max(1, int((page_h - 2*margin_y) // (letter_height + line_spacing)))
    total_pages = (len(lines) + lines_per_page - 1) // lines_per_page

    for idx, line in enumerate(lines):
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
            page_num +=1

        # Red border 5mm
        c.setStrokeColorRGB(1,0,0)
        c.setLineWidth(2)
        c.rect(margin_x, margin_y, page_w-2*margin_x, page_h-2*margin_y)

        # Draw letters
        x = margin_x
        for ch in line:
            if ch == " ":
                x += 15*mm
                continue
            candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
            img_path = next((os.path.join(LETTERS_FOLDER, c) for c in candidates if os.path.exists(os.path.join(LETTERS_FOLDER, c))), None)
            if img_path:
                w, h = char_dimensions[ch]
                letter_width = letter_height * w / h
                c.drawImage(img_path, x, current_y, width=letter_width, height=letter_height, mask='auto')
                x += letter_width + 5*mm
            else:
                x += 50*mm

        # Footer
        c.setFont("Helvetica", 10)
        footer_text = f"Page {page_num} - {paper_choice} - NCC"
        c.drawCentredString(page_w/2, 5*mm, footer_text)

        current_y -= (letter_height + line_spacing)

    c.save()

# -------------------
# Generate PDF
# -------------------
if st.button("Generate PDF"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.markdown('<div class="stAlert alert-warning">⚠️ Please enter at least one line.</div>', unsafe_allow_html=True)
    else:
        missing_chars = check_missing_chars(lines)
        long_lines = [i+1 for i, line in enumerate(lines) if check_line_width(line, PAPER_SIZES[paper_choice][0], letter_height=letter_height_mm)]
        if missing_chars:
            st.markdown(f'<div class="stAlert alert-error">❌ Missing PNG letters: {", ".join(sorted(missing_chars))}</div>', unsafe_allow_html=True)
        if long_lines:
            st.markdown(f'<div class="stAlert alert-warning">⚠️ Lines too long: {long_lines}</div>', unsafe_allow_html=True)

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()

        generate_pdf(lines, tmp_path, letter_height_mm)
        st.markdown('<div class="stAlert alert-success">✅ PDF generated successfully!</div>', unsafe_allow_html=True)

        # Download button
        with open(tmp_path, "rb") as f:
            st.download_button(
                label="📥 Download PDF",
                data=f,
                file_name="output.pdf",
                mime="application/pdf"
            )
