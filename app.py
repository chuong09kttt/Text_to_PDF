import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
import base64

# -----------------------
# Config
# -----------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]

LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
if not os.path.exists(LETTERS_FOLDER):
    os.makedirs(LETTERS_FOLDER)

ADMIN_PASSWORD = "admin123"  # Change this password

# -----------------------
# Sidebar / Admin Upload
# -----------------------
st.sidebar.title("Settings")

# Admin login for uploading letters
password_input = st.sidebar.text_input("Admin password (to upload PNG)", type="password")
if password_input == ADMIN_PASSWORD:
    st.sidebar.subheader("Upload PNG letters")
    uploaded_files = st.sidebar.file_uploader("Choose PNG files", type=["png", "PNG"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            save_path = os.path.join(LETTERS_FOLDER, file.name)
            with open(save_path, "wb") as f:
                f.write(file.getbuffer())
        st.sidebar.success(f"{len(uploaded_files)} file(s) uploaded successfully.")

# Paper & Letter settings
paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox("Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=2)
letter_height = letter_height_mm * mm

# -----------------------
# Text Input
# -----------------------
st.header("Text to PDF")
text_input = st.text_area("Enter lines of text:", height=300, placeholder="Line 1\nLine 2\nLine 3...")

# -----------------------
# Helper Functions
# -----------------------
def get_available_letters():
    letters = {}
    for fname in os.listdir(LETTERS_FOLDER):
        if fname.lower().endswith(".png"):
            letters[fname.split(".")[0].upper()] = os.path.join(LETTERS_FOLDER, fname)
    return letters

def check_missing_chars(lines):
    available = get_available_letters()
    missing_chars = set()
    for line in lines:
        for ch in line.upper():
            if ch != " " and ch not in available:
                missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm):
    available = get_available_letters()
    x = margin_x
    for ch in line.upper():
        if ch == " ":
            x += space_width
            continue
        img_path = available.get(ch)
        if img_path:
            with Image.open(img_path) as im:
                w, h = im.size
                x += letter_height * w / h + 5*mm
        else:
            x += 50*mm
    return x > (page_w - margin_x)

def generate_pdf(lines, pdf_path):
    page_size = PAPER_SIZES[paper_choice]
    if orientation_choice == "Landscape":
        page_w, page_h = landscape(page_size)
    else:
        page_w, page_h = portrait(page_size)

    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    margin_x = 20*mm
    margin_y = 10*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height

    available = get_available_letters()
    char_dimensions = {}
    for ch, path in available.items():
        with Image.open(path) as im:
            char_dimensions[ch] = im.size

    page_num = 1
    lines_per_page = max(1, int((page_h - 2*margin_y) // (letter_height + line_spacing)))
    total_pages = (len(lines) + lines_per_page - 1) // lines_per_page

    for idx, line in enumerate(lines):
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
            page_num += 1

        # Red border 5mm
        c.setStrokeColorRGB(1, 0, 0)
        c.setLineWidth(2)
        c.rect(5*mm, 5*mm, page_w-10*mm, page_h-10*mm)

        # Draw letters
        x = margin_x
        for ch in line.upper():
            if ch == " ":
                x += 15*mm
                continue
            img_path = available.get(ch)
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

def pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# -----------------------
# Generate & Preview PDF
# -----------------------
if st.button("Generate PDF"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.warning("Please enter at least one line.")
    else:
        page_w = PAPER_SIZES[paper_choice][0]
        long_lines = [i+1 for i, line in enumerate(lines) if check_line_width(line, page_w)]
        missing_chars = check_missing_chars(lines)

        if long_lines:
            st.warning(f"Lines too long: {long_lines}")
        if missing_chars:
            st.warning(f"Missing PNG letters: {', '.join(sorted(missing_chars))}")

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()

        generate_pdf(lines, tmp_path)
        st.success("PDF generated successfully!")

        # Embed PDF with PDF.js
        pdf_b64 = pdf_to_base64(tmp_path)
        pdf_html = f"""
        <iframe
            src="https://mozilla.github.io/pdf.js/web/viewer.html?file=data:application/pdf;base64,{pdf_b64}"
            width="100%"
            height="800"
            style="border:1px solid #666;">
        </iframe>
        """
        st.markdown(pdf_html, unsafe_allow_html=True)

        # Download button
        with open(tmp_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="output.pdf")
