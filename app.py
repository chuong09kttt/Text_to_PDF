import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, A2, A1, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile
import base64

# Optional: preview PDF as images
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# -------------------
# Config
# -------------------
st.set_page_config(page_title="Text to PDF Viewer", layout="wide")

PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]

# -------------------
# Sidebar / Controls
# -------------------
with st.sidebar:
    st.header("Settings")
    paper_choice = st.selectbox("Paper size", list(PAPER_SIZES.keys()), index=3)
    orientation_choice = st.selectbox("Orientation", ["Portrait", "Landscape"], index=0)
    letter_height_mm = st.selectbox("Letter Height (mm)", LETTER_HEIGHT_OPTIONS, index=2)

# -------------------
# Main UI
# -------------------
st.title("📝 Text to PDF Viewer")
st.markdown("Enter your text, choose settings, generate PDF, and preview it like a real PDF viewer.")

text_input = st.text_area("Enter text (one line per row):", height=200, placeholder="Line 1\nLine 2\nLine 3...")

# -------------------
# PDF generation
# -------------------
def generate_pdf(lines, pdf_path):
    page_size = PAPER_SIZES[paper_choice]
    if orientation_choice == "Landscape":
        page_w, page_h = landscape(page_size)
    else:
        page_w, page_h = portrait(page_size)

    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    margin_x, margin_y = 20*mm, 20*mm
    line_spacing = 15*mm
    letter_height = letter_height_mm * mm
    current_y = page_h - margin_y - letter_height

    for line in lines:
        x = margin_x
        for ch in line:
            if ch != " ":
                c.setFont("Helvetica", 20)
                c.drawString(x, current_y, ch)
                x += 15
            else:
                x += 10
        current_y -= (letter_height + line_spacing)
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
    c.save()

def pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def pdf_to_images(pdf_path):
    if not PDF2IMAGE_AVAILABLE:
        st.warning("pdf2image not installed. Image preview unavailable.")
        return []
    return convert_from_path(pdf_path)

# -------------------
# Generate & Preview
# -------------------
if st.button("Generate PDF", type="primary"):
    lines = [line.strip() for line in text_input.splitlines() if line.strip()]
    if not lines:
        st.warning("Please enter at least one line of text.")
    else:
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp_pdf.name
        tmp_pdf.close()

        generate_pdf(lines, tmp_path)
        st.success("✅ PDF generated!")

        # --- PDF iframe preview ---
        st.subheader("📄 PDF Preview (Scrollable & Zoomable)")
        pdf_b64 = pdf_to_base64(tmp_path)
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{pdf_b64}" width="100%" height="700px" style="border:1px solid #888;"></iframe>',
            unsafe_allow_html=True
        )

        # --- Image page preview ---
        if PDF2IMAGE_AVAILABLE:
            st.subheader("🖼 Image Preview Pages")
            images = pdf_to_images(tmp_path)
            for idx, img in enumerate(images):
                st.image(img, caption=f"Page {idx+1}", use_column_width=True)

        # --- Download button ---
        with open(tmp_path, "rb") as f:
            st.download_button("⬇ Download PDF", f, file_name="output.pdf", mime="application/pdf")
