import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
import base64

# -------------------
# Config
# -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]  # mm
LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
os.makedirs(LETTERS_FOLDER, exist_ok=True)

# -------------------
# Sidebar / Controls
# -------------------
st.sidebar.title("Settings")

# Admin upload PNG
st.sidebar.subheader("Admin: Upload Letters")
uploaded_files = st.sidebar.file_uploader(
    "Upload PNG letters", type=["png"], accept_multiple_files=True
)
for file in uploaded_files:
    save_path = os.path.join(LETTERS_FOLDER, file.name.upper())
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
if uploaded_files:
    st.sidebar.success(f"Uploaded {len(uploaded_files)} file(s)")

paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox(
    "Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=2
)
letter_height = letter_height_mm * mm

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
def check_missing_chars(lines):
    missing_chars = set()
    for line in lines:
        for ch in line.upper():
            if ch != " ":
                img_path = os.path.join(LETTERS_FOLDER, f"{ch}.png")
                if not os.path.exists(img_path):
                    missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm):
    x = margin_x
    for ch in line.upper():
        if ch == " ":
            x += space_width
            continue
        img_path = os.path.join(LETTERS_FOLDER, f"{ch}.png")
        if os.path.exists(img_path):
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

    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    margin_x = 20*mm
    margin_y = 10*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height

    # Preload char dimensions
    char_dimensions = {}
    unique_chars = set("".join(lines).upper().replace(" ", ""))
    for ch in unique_chars:
        img_path = os.path.join(LETTERS_FOLDER, f"{ch}.png")
        if os.path.exists(img_path):
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
            img_path = os.path.join(LETTERS_FOLDER, f"{ch}.png")
            if os.path.exists(img_path):
                w, h = char_dimensions[ch]
                letter_width = letter_height * w / h
                c.drawImage(img_path, x, current_y, width=letter_width, height=letter_height, mask='auto')
                x += letter_width + 5*mm
            else:
                x += 50*mm

        # Footer
        c.setFont("Helvetica", 10)
        footer_text = f"Page {page_num}/{total_pages} - {paper_choice} - NCC"
        c.drawCentredString(page_w/2, 5*mm, footer_text)

        current_y -= (letter_height + line_spacing)

    c.save()

def preview_pdf(pdf_path):
    """Hiển thị PDF trong Streamlit bằng iframe"""
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    b64 = base64.b64encode(pdf_data).decode("utf-8")
    pdf_display = f"""
        <iframe src="data:application/pdf;base64,{b64}" width="100%" height="700px" style="border: none;"></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)

# -------------------
# Generate & Preview
# -------------------
if st.button("Generate PDF"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.warning("Please enter at least one line.")
    else:
        long_lines = [i+1 for i, line in enumerate(lines) if check_line_width(line, PAPER_SIZES[paper_choice][0])]
        missing_chars = check_missing_chars(lines)

        if long_lines:
            st.warning(f"Lines too long: {long_lines}")
        if missing_chars:
            st.warning(f"Missing PNG letters: {', '.join(sorted(missing_chars))}")

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()

        generate_pdf(lines, tmp_path)
        st.success("PDF generated!")

        # Preview
        preview_pdf(tmp_path)

        # Download
        with open(tmp_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="output.pdf")
