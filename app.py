import os
import math
import tempfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
import streamlit as st

# ================= CONFIG =================
PAPER_SIZES = {"A2": A2, "A3": A3, "A4": A4}
LETTER_HEIGHT_OPTIONS = [50, 75, 100, 150]

# Folder containing PNG letter images
LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
os.makedirs(LETTERS_FOLDER, exist_ok=True)

# ================= PDF FUNCTION =================
def generate_pdf_from_images(lines, pdf_path, paper_choice, orientation_choice, letter_height_mm, footer_text):
    page_size = PAPER_SIZES[paper_choice]
    page_w, page_h = landscape(page_size) if orientation_choice == "Landscape" else portrait(page_size)
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))

    margin_left = 20 * mm
    margin_top = 20 * mm
    line_spacing = letter_height_mm * mm + 20 * mm  # Height of character + 20mm gap
    line_mid_gap = 10 * mm  # Line in the middle of each line
    y = page_h - margin_top
    page_number = 1
    total_pages = math.ceil(len(lines) / 20)

    for i, line in enumerate(lines, start=1):
        x = margin_left

        # Draw each character
        for ch in line:
            if ch == " ":
                x += 10 * mm
                continue
            img_path = None
            for candidate in [f"{ch.upper()}.png", f"{ch.lower()}.png"]:
                p = os.path.join(LETTERS_FOLDER, candidate)
                if os.path.exists(p):
                    img_path = p
                    break
            if img_path:
                with Image.open(img_path) as img:
                    w, h = img.size
                    aspect = w / h
                    draw_h = letter_height_mm * mm
                    draw_w = draw_h * aspect
                    c.drawImage(img_path, x, y - draw_h, width=draw_w, height=draw_h, mask='auto')
                    x += draw_w

        # Draw horizontal line in the middle of the line
        c.setStrokeColor("#999999")
        c.setLineWidth(0.5)
        c.line(margin_left, y - line_mid_gap, page_w - margin_left, y - line_mid_gap)

        # Move y down for next line
        y -= line_spacing

        # Check if need new page
        if y < margin_top:
            c.setFont("Helvetica", 10)
            footer_text_centered = f"Page {page_number}/{total_pages} - {paper_choice} - {footer_text}"
            text_width = c.stringWidth(footer_text_centered, "Helvetica", 10)
            c.drawString((page_w - text_width) / 2, 15 * mm, footer_text_centered)
            c.showPage()
            page_number += 1
            y = page_h - margin_top

    # Footer on last page
    c.setFont("Helvetica", 10)
    footer_text_centered = f"Page {page_number}/{total_pages} - {paper_choice} - {footer_text}"
    text_width = c.stringWidth(footer_text_centered, "Helvetica", 10)
    c.drawString((page_w - text_width) / 2, 15 * mm, footer_text_centered)
    c.save()

# ================= STREAMLIT UI =================
st.set_page_config(page_title="Smart Text-to-PDF", layout="centered")

st.title("🧠 Smart Text-to-PDF Converter")
st.write("Generate PDFs from PNG letters with correct line spacing, middle horizontal lines, and centered footer.")

st.markdown("---")

text_input = st.text_area("✏️ Enter text (each line will have proper spacing):", height=200)
paper_choice = st.selectbox("📄 Paper size", list(PAPER_SIZES.keys()), index=1)
orientation_choice = st.radio("↔️ Page orientation", ["Portrait", "Landscape"], horizontal=True)
letter_height_mm = st.selectbox("🔠 Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=0)
footer_text = st.text_input("🏷️ Footer content", "Author")

# ------------------- PROCESS -------------------
lines = [l.strip() for l in text_input.split("\n") if l.strip()]
too_long_lines = []
max_chars_per_line = 50  # Approximate, can adjust according to letter width
for idx, line in enumerate(lines):
    if len(line) > max_chars_per_line:
        too_long_lines.append(idx + 1)

missing_chars = []
for line in lines:
    for ch in line:
        if ch != " ":
            found = False
            for candidate in [f"{ch.upper()}.png", f"{ch.lower()}.png"]:
                if os.path.exists(os.path.join(LETTERS_FOLDER, candidate)):
                    found = True
                    break
            if not found:
                missing_chars.append(ch)

# ------------------- BUTTON -------------------
if st.button("📄 Generate PDF"):
    if not text_input.strip():
        st.warning("Please enter some text before generating PDF.")
    elif too_long_lines:
        st.error(f"Lines too long (> {max_chars_per_line} characters): {', '.join(map(str, too_long_lines))}")
    elif missing_chars:
        st.error(f"The following characters do not have PNG images: {', '.join(sorted(set(missing_chars)))}")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            generate_pdf_from_images(
                lines, tmpfile.name, paper_choice, orientation_choice, letter_height_mm, footer_text
            )
            tmpfile.flush()
            st.success("✅ PDF successfully generated!")
            with open(tmpfile.name, "rb") as f:
                st.download_button("⬇️ Download PDF", f, file_name="output.pdf", mime="application/pdf")

st.markdown("---")
st.caption("🧩 Designed by ChatGPT – Streamlit PDF Generator Pro v4")
