import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A1, A2, A3, A4, landscape, portrait
from reportlab.lib.units import mm
from PIL import Image
import tempfile

# -------------------
# Page Config
# -------------------
st.set_page_config(
    page_title="Text to PDF",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern look and alerts
st.markdown("""
    <style>
    .main {background-color: #f5f5f5;}
    .stButton>button {background-color: #4CAF50;color:white;height:45px;width:220px;border-radius:8px;font-size:16px;}
    .stTextArea>textarea {font-size:16px;}
    .stSidebar {background-color: #e6f2ff; padding: 20px; border-radius:10px;}
    .stAlert {border-radius: 10px; padding: 15px;}
    .alert-success {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .alert-warning {background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;}
    .alert-error {background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;}
    </style>
""", unsafe_allow_html=True)

st.title("📝 Text to PDF Generator")
st.markdown("Convert text into PDF using PNG letters with professional settings.")

# -------------------
# Constants
# -------------------
PAPER_SIZES = {"A1": A1, "A2": A2, "A3": A3, "A4": A4}
DEFAULT_LETTER_HEIGHT = 100

# -------------------
# Admin Upload Section
# -------------------
st.sidebar.header("🔒 Admin Panel")
admin_password = st.sidebar.text_input("Admin Password", type="password")

letters_folder = os.path.join(os.path.dirname(__file__), "ABC")
os.makedirs(letters_folder, exist_ok=True)

if admin_password == "12345":  # Change your password
    st.sidebar.subheader("Upload PNG Letters")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PNG letters", type=["png", "PNG"], accept_multiple_files=True
    )
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(letters_folder, file.name.upper()), "wb") as f:
                f.write(file.getbuffer())
        st.sidebar.success(f"{len(uploaded_files)} PNG(s) uploaded!")

# -------------------
# PDF Settings
# -------------------
st.sidebar.header("📄 PDF Settings")
paper_choice = st.sidebar.selectbox("Paper size", list(PAPER_SIZES.keys()), index=2)
orientation_choice = st.sidebar.selectbox("Orientation", ["Portrait", "Landscape"], index=1)
letter_height_mm = st.sidebar.selectbox(
    "Letter height (mm)", options=[50, 75, 100, 150], index=2
)
letter_height = letter_height_mm * mm

# -------------------
# Text Input Section
# -------------------
st.subheader("✏️ Enter Text")
text_input = st.text_area(
    "Type your text here (one line per row):",
    height=300,
    placeholder="Line 1\nLine 2\nLine 3..."
)

# -------------------
# Helper Functions
# -------------------
def get_available_letters(folder):
    return {f.split('.')[0].upper() for f in os.listdir(folder) if f.lower().endswith(".png")}

def check_missing_letters(lines, folder):
    available = get_available_letters(folder)
    missing = set()
    for line in lines:
        for ch in line.upper():
            if ch != " " and ch not in available:
                missing.add(ch)
    return sorted(missing)

def check_line_width(line, page_width, space_width=15*mm, margin_x=20*mm):
    x = margin_x
    for ch in line.upper():
        if ch == " ":
            x += space_width
        else:
            x += letter_height
        if x > page_width - margin_x:
            return True
    return False

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

    # Preload letter sizes
    char_dimensions = {}
    unique_chars = set("".join(lines).upper().replace(" ", ""))
    for ch in unique_chars:
        img_path = os.path.join(letters_folder, f"{ch}.PNG")
        if not os.path.exists(img_path):
            img_path = os.path.join(letters_folder, f"{ch}.png")
        if os.path.exists(img_path):
            with Image.open(img_path) as im:
                char_dimensions[ch] = im.size

    page_num = 1
    for line in lines:
        if current_y < margin_y:
            c.showPage()
            current_y = page_h - margin_y - letter_height
            page_num +=1

        # Red border 5mm
        c.setStrokeColorRGB(1,0,0)
        c.setLineWidth(2)
        c.rect(5*mm, 5*mm, page_w-10*mm, page_h-10*mm)

        # Draw letters
        x = margin_x
        for ch in line.upper():
            if ch == " ":
                x += 15*mm
                continue
            img_path = os.path.join(letters_folder, f"{ch}.PNG")
            if not os.path.exists(img_path):
                img_path = os.path.join(letters_folder, f"{ch}.png")
            if os.path.exists(img_path):
                w, h = char_dimensions.get(ch, (letter_height, letter_height))
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
# Generate PDF Button
# -------------------
if st.button("Generate PDF"):
    lines = [l.strip() for l in text_input.splitlines() if l.strip()]
    if not lines:
        st.markdown('<div class="stAlert alert-warning">⚠️ Please enter at least one line of text.</div>', unsafe_allow_html=True)
    else:
        missing = check_missing_letters(lines, letters_folder)
        long_lines = [i+1 for i, line in enumerate(lines) if check_line_width(line, PAPER_SIZES[paper_choice][0])]

        if missing:
            st.markdown(f'<div class="stAlert alert-error">❌ Missing PNG letters: {", ".join(missing)}</div>', unsafe_allow_html=True)
        if long_lines:
            st.markdown(f'<div class="stAlert alert-warning">⚠️ Lines too long: {long_lines}</div>', unsafe_allow_html=True)

        if not missing:
            tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp_path = tmp_pdf.name
            tmp_pdf.close()

            generate_pdf(lines, tmp_path)
            st.markdown('<div class="stAlert alert-success">✅ PDF generated successfully!</div>', unsafe_allow_html=True)

            with open(tmp_path, "rb") as f:
                st.download_button(
                    label="📥 Download PDF",
                    data=f,
                    file_name="output.pdf",
                    mime="application/pdf"
                )
