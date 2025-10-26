import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
import shutil
import streamlit.components.v1 as components

# -------------------
# Config
# -------------------
PAPER_SIZE = A3
DEFAULT_ORIENTATION = "Landscape"
DEFAULT_LETTER_HEIGHT = 100  # mm
LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")

# Ensure folder exists
if not os.path.exists(LETTERS_FOLDER):
    os.makedirs(LETTERS_FOLDER)

# -------------------
# Sidebar / Controls
# -------------------
st.sidebar.title("Settings")
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox(
    "Letter height (mm)", [50, 75, 100, 150], index=2
)
letter_height = letter_height_mm * mm

# -------------------
# Admin: Upload letters
# -------------------
st.sidebar.subheader("Admin: Upload PNG letters")
uploaded_files = st.sidebar.file_uploader(
    "Upload PNG letters", type=["png", "PNG"], accept_multiple_files=True
)
if uploaded_files:
    for file in uploaded_files:
        save_path = os.path.join(LETTERS_FOLDER, file.name)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
    st.sidebar.success(f"Uploaded {len(uploaded_files)} files.")

# -------------------
# Text input
# -------------------
st.header("Text to PDF")
text_input = st.text_area(
    "Enter lines of text:", height=300, placeholder="Line 1\nLine 2\nLine 3..."
)

# -------------------
# Helper functions
# -------------------
def find_letter_file(ch):
    """Find letter PNG ignoring case and extension"""
    ch = ch.upper()
    for fname in os.listdir(LETTERS_FOLDER):
        name, ext = os.path.splitext(fname)
        if name.upper() == ch and ext.lower() == ".png":
            return os.path.join(LETTERS_FOLDER, fname)
    return None

def check_missing_chars(lines):
    missing = set()
    for line in lines:
        for ch in line:
            if ch == " ":
                continue
            if not find_letter_file(ch):
                missing.add(ch.upper())
    return missing

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm):
    x = margin_x
    for ch in line:
        if ch == " ":
            x += space_width
            continue
        file = find_letter_file(ch)
        if file:
            with Image.open(file) as im:
                w, h = im.size
                x += letter_height * (w/h) + 5*mm
        else:
            x += 50*mm
    return x > (page_w - margin_x)

def generate_pdf(lines, pdf_path):
    if orientation_choice == "Landscape":
        page_w, page_h = landscape(PAPER_SIZE)
    else:
        page_w, page_h = portrait(PAPER_SIZE)

    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    margin_x = 20*mm
    margin_y = 10*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height

    # Preload char dimensions
    char_dimensions = {}
    unique_chars = set("".join(lines).replace(" ", ""))
    for ch in unique_chars:
        file = find_letter_file(ch)
        if file:
            with Image.open(file) as im:
                char_dimensions[ch.upper()] = im.size

    page_num = 1
    lines_per_page = max(1, int((page_h - 2*margin_y) // (letter_height + line_spacing)))
    total_pages = (len(lines) + lines_per_page - 1) // lines_per_page

    for idx, line in enumerate(lines):
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
            page_num += 1

        # Red border 2mm
        c.setStrokeColorRGB(1,0,0)
        c.setLineWidth(2)
        c.rect(2*mm, 2*mm, page_w-4*mm, page_h-4*mm)

        # Draw line
        x = margin_x
        for ch in line:
            if ch == " ":
                x += 15*mm
                continue
            file = find_letter_file(ch)
            if file:
                w, h = char_dimensions[ch.upper()]
                letter_w = letter_height * w / h
                c.drawImage(file, x, current_y, width=letter_w, height=letter_height, mask='auto')
                x += letter_w + 5*mm
            else:
                x += 50*mm

        # Footer
        c.setFont("Helvetica", 10)
        footer_text = f"Page {page_num}/{total_pages} - A3 - NCC"
        c.drawCentredString(page_w/2, 5*mm, footer_text)

        current_y -= (letter_height + line_spacing)

    c.save()

# -------------------
# Generate & Preview
# -------------------
if st.button("Generate PDF"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.warning("Please enter at least one line.")
    else:
        missing_chars = check_missing_chars(lines)
        if missing_chars:
            st.warning(f"Missing PNG letters: {', '.join(sorted(missing_chars))}")

        # Generate PDF
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()
        generate_pdf(lines, tmp_path)
        st.success("PDF generated!")

        # Preview PDF using PDF.js
        viewer_path = "https://mozilla.github.io/pdf.js/web/viewer.html"
        pdf_url = tmp_path.replace("\\","/")  # normalize path
        iframe_code = f"""
        <iframe src="{viewer_path}?file={pdf_url}" width="100%" height="700" style="border:none;"></iframe>
        """
        components.html(iframe_code, height=700)

        # Download button
        with open(tmp_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="output.pdf")
