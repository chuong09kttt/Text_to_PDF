import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
import base64
import shutil
import streamlit.components.v1 as components

# -------------------
# Config
# -------------------
st.set_page_config(page_title="Text to PDF", layout="wide")
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]

ABC_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
os.makedirs(ABC_FOLDER, exist_ok=True)  # Tạo folder nếu chưa có

# -------------------
# Sidebar / Controls
# -------------------
st.sidebar.title("Settings")
paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox("Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=2)
letter_height = letter_height_mm * mm

# -------------------
# Admin upload PNG letters
# -------------------
st.sidebar.subheader("Admin Upload Letters (PNG)")
uploaded_files = st.sidebar.file_uploader(
    "Upload PNG letters",
    type=["png"],
    accept_multiple_files=True
)
if uploaded_files:
    for file in uploaded_files:
        dest_path = os.path.join(ABC_FOLDER, file.name.upper())
        with open(dest_path, "wb") as f:
            f.write(file.getbuffer())
    st.sidebar.success(f"{len(uploaded_files)} files uploaded to ABC folder.")

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
        for ch in line.upper():
            if ch != " ":
                img_path = os.path.join(ABC_FOLDER, f"{ch}.PNG")
                if not os.path.exists(img_path):
                    missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, margin_x=20*mm, space_width=15*mm):
    x = margin_x
    for ch in line.upper():
        if ch == " ":
            x += space_width
            continue
        img_path = os.path.join(ABC_FOLDER, f"{ch}.PNG")
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
        img_path = os.path.join(ABC_FOLDER, f"{ch}.PNG")
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

        # Draw letters
        x = margin_x
        for ch in line.upper():
            if ch == " ":
                x += 15*mm
                continue
            img_path = os.path.join(ABC_FOLDER, f"{ch}.PNG")
            if os.path.exists(img_path):
                w, h = char_dimensions[ch]
                letter_width = letter_height * w / h
                c.drawImage(img_path, x, current_y, width=letter_width, height=letter_height, mask='auto')
                x += letter_width + 5*mm
            else:
                x += 50*mm

        current_y -= (letter_height + line_spacing)

    c.save()

def display_pdf_with_pdfjs(pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    html_code = f"""
    <html>
      <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.547/pdf.min.js"></script>
        <style>
          #pdf-canvas {{ width: 100%; height: 700px; border: 1px solid #000; }}
        </style>
      </head>
      <body>
        <canvas id="pdf-canvas"></canvas>
        <script>
          const pdfData = atob("{pdf_b64}");
          const pdfjsLib = window['pdfjs-dist/build/pdf'];
          pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.547/pdf.worker.min.js';
          const loadingTask = pdfjsLib.getDocument({{data: pdfData}});
          loadingTask.promise.then(pdf => {{
              let pageNum = 1;
              pdf.getPage(pageNum).then(page => {{
                  const scale = 1.5;
                  const viewport = page.getViewport({{scale: scale}});
                  const canvas = document.getElementById('pdf-canvas');
                  const context = canvas.getContext('2d');
                  canvas.height = viewport.height;
                  canvas.width = viewport.width;
                  page.render({{canvasContext: context, viewport: viewport}});
              }});
          }});
        </script>
      </body>
    </html>
    """
    components.html(html_code, height=750)

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

        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()

        generate_pdf(lines, tmp_path)
        st.success("PDF generated!")

        # Preview with PDF.js
        display_pdf_with_pdfjs(tmp_path)

        # Download
        with open(tmp_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="output.pdf")
