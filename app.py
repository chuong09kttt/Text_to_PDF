import os
import tempfile
import platform
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
import streamlit as st

# -------------------------
# Config
# -------------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTERS_FOLDER = Path(__file__).parent / "ABC"
ADMIN_PASSWORD = "1234"  # mật khẩu admin

if not LETTERS_FOLDER.exists():
    LETTERS_FOLDER.mkdir()

# -------------------------
# Sidebar settings
# -------------------------
st.sidebar.title("Settings")

# Admin upload
st.sidebar.subheader("Admin Upload PNG")
password = st.sidebar.text_input("Admin password", type="password")
if password == ADMIN_PASSWORD:
    uploaded_files = st.sidebar.file_uploader(
        "Upload letter PNGs (A-Z, 0-9)", accept_multiple_files=True, type=["png", "PNG"]
    )
    if uploaded_files:
        for file in uploaded_files:
            file_path = LETTERS_FOLDER / file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        st.sidebar.success("Uploaded successfully!")
else:
    if password:
        st.sidebar.error("Incorrect password")

# Paper size and orientation
paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)

# Letter height
letter_height_mm = st.sidebar.selectbox(
    "Letter height (mm)", [50, 75, 100, 150], index=2
)
letter_height = letter_height_mm * mm

# -------------------------
# Text input
# -------------------------
st.header("Text to PDF")
text_input = st.text_area(
    "Enter lines of text:", height=300, placeholder="Line 1\nLine 2\nLine 3..."
)

# -------------------------
# Helper functions
# -------------------------
def check_missing_chars(lines):
    missing_chars = set()
    available_files = {f.stem.upper() for f in LETTERS_FOLDER.glob("*.[pP][nN][gG]")}
    for line in lines:
        for ch in line.upper():
            if ch != " " and ch not in available_files:
                missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm):
    x = margin_x
    for ch in line.upper():
        if ch == " ":
            x += space_width
            continue
        img_path = LETTERS_FOLDER / f"{ch}.png"
        if not img_path.exists():
            img_path = LETTERS_FOLDER / f"{ch}.PNG"
        if img_path.exists():
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

    # Preload letter images
    char_cache = {}
    for f in LETTERS_FOLDER.glob("*.[pP][nN][gG]"):
        ch = f.stem.upper()
        im = Image.open(f)
        char_cache[ch] = im.copy()
        im.close()

    page_num = 1
    lines_per_page = max(1, int((page_h - 2*margin_y) // (letter_height + line_spacing)))
    total_pages = (len(lines) + lines_per_page - 1) // lines_per_page

    for idx, line in enumerate(lines):
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
            page_num +=1

        # Draw letters
        x = margin_x
        for ch in line.upper():
            if ch == " ":
                x += 15*mm
                continue
            img = char_cache.get(ch)
            if img:
                w, h = img.size
                letter_width = letter_height * w / h
                c.drawInlineImage(img, x, current_y, width=letter_width, height=letter_height)
                x += letter_width + 5*mm
            else:
                x += 50*mm

        current_y -= (letter_height + line_spacing)

    c.save()

def open_pdf(pdf_path):
    if platform.system() == "Windows":
        os.startfile(pdf_path)
    elif platform.system() == "Darwin":
        os.system(f"open {pdf_path}")
    else:
        os.system(f"xdg-open {pdf_path}")

# -------------------------
# Generate PDF
# -------------------------
if st.button("Generate PDF"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.warning("Please enter at least one line.")
    else:
        # Check missing letters
        missing_chars = check_missing_chars(lines)
        if missing_chars:
            st.warning(f"Missing PNG letters: {', '.join(sorted(missing_chars))}")

        # Check line width
        page_size = PAPER_SIZES[paper_choice]
        page_w, page_h = landscape(page_size) if orientation_choice=="Landscape" else portrait(page_size)
        long_lines = [i+1 for i, line in enumerate(lines) if check_line_width(line, page_w)]
        if long_lines:
            st.warning(f"Lines too long: {long_lines}")

        # Generate PDF
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()

        generate_pdf(lines, tmp_path)
        st.success(f"PDF generated at {tmp_path}!")

        # Open PDF in default viewer
        open_pdf(tmp_path)

        # Download button
        with open(tmp_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="output.pdf")
