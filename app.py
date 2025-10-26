import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
from pathlib import Path

# -------------------
# Config
# -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTERS_FOLDER = Path(__file__).parent / "ABC"
LETTERS_FOLDER.mkdir(exist_ok=True)

# Admin password for uploading PNG
ADMIN_PASSWORD = "admin123"

# -------------------
# Sidebar Settings
# -------------------
st.sidebar.title("Settings")

# Admin upload
st.sidebar.subheader("Admin Upload")
admin_pass = st.sidebar.text_input("Enter admin password to upload PNGs:", type="password")
if admin_pass == ADMIN_PASSWORD:
    uploaded_files = st.sidebar.file_uploader("Upload PNG letters", type=["png", "PNG"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            save_path = LETTERS_FOLDER / file.name
            with open(save_path, "wb") as f:
                f.write(file.getbuffer())
        st.sidebar.success(f"{len(uploaded_files)} file(s) uploaded successfully!")

# Paper and orientation
paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox("Letter height (mm)", [50, 75, 100, 150], index=2)
letter_height = letter_height_mm * mm

# -------------------
# Text input
# -------------------
st.header("Text to PDF")
text_input = st.text_area("Enter lines of text:", height=300, placeholder="Line 1\nLine 2\nLine 3...")

# -------------------
# Helper functions
# -------------------
def get_png_path(letter):
    """Return path of PNG file for a letter, case-insensitive, .png/.PNG"""
    letter = letter.upper()
    for ext in [".png", ".PNG"]:
        candidate = LETTERS_FOLDER / f"{letter}{ext}"
        if candidate.exists():
            return candidate
    return None

def check_missing_chars(lines):
    missing_chars = set()
    for line in lines:
        for ch in line.upper():
            if ch != " " and not get_png_path(ch):
                missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm):
    x = margin_x
    for ch in line.upper():
        if ch == " ":
            x += space_width
            continue
        img_path = get_png_path(ch)
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

def generate_pdf(lines, pdf_path):
    page_size = PAPER_SIZES[paper_choice]
    if orientation_choice == "Landscape":
        page_w, page_h = landscape(page_size)
    else:
        page_w, page_h = portrait(page_size)

    c = canvas.Canvas(str(pdf_path), pagesize=(page_w, page_h))
    margin_x = 20*mm
    margin_y = 10*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height

    # Preload char dimensions
    char_dimensions = {}
    unique_chars = set("".join(lines).upper().replace(" ", ""))
    for ch in unique_chars:
        img_path = get_png_path(ch)
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

        # Red border 2mm
        c.setStrokeColorRGB(1,0,0)
        c.setLineWidth(2)
        c.rect(2*mm, 2*mm, page_w-4*mm, page_h-4*mm)

        # 1 line top & bottom 10mm
        c.setStrokeColorRGB(0,0,0)
        c.setLineWidth(0.5)
        c.line(margin_x, current_y + letter_height + 10*mm, page_w - margin_x, current_y + letter_height + 10*mm)
        c.line(margin_x, current_y - 10*mm, page_w - margin_x, current_y - 10*mm)

        # Draw letters
        x = margin_x
        for ch in line.upper():
            if ch == " ":
                x += 15*mm
                continue
            img_path = get_png_path(ch)
            if img_path:
                w, h = char_dimensions[ch]
                letter_width = letter_height * w / h
                c.drawImage(str(img_path), x, current_y, width=letter_width, height=letter_height, mask='auto')
                x += letter_width + 5*mm
            else:
                x += 50*mm

        # Footer
        c.setFont("Helvetica", 10)
        footer_text = f"Page {page_num}/{total_pages} - {paper_choice} - NCC"
        c.drawCentredString(page_w/2, 5*mm, footer_text)

        current_y -= (letter_height + line_spacing)

    c.save()

# -------------------
# Generate PDF
# -------------------
if st.button("Generate PDF"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.warning("Please enter at least one line.")
    else:
        page_w = PAPER_SIZES[paper_choice][0] if orientation_choice=="Portrait" else PAPER_SIZES[paper_choice][1]
        long_lines = [i+1 for i, line in enumerate(lines) if check_line_width(line, page_w)]
        missing_chars = check_missing_chars(lines)

        if long_lines:
            st.warning(f"Lines too long: {long_lines}")
        if missing_chars:
            st.warning(f"Missing PNG letters: {', '.join(sorted(missing_chars))}")

        tmp_pdf = Path(tempfile.gettempdir()) / "output.pdf"
        generate_pdf(lines, tmp_pdf)
        st.success("PDF generated!")

        # Preview PDF using iframe
        st.subheader("Preview PDF")
        st.components.v1.iframe(str(tmp_pdf.resolve()), width=900, height=600)

        # Download PDF
        with open(tmp_pdf, "rb") as f:
            st.download_button("Download PDF", f, file_name="output.pdf")
