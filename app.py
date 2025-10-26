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

st.set_page_config(
    page_title="Text to PDF Converter", 
    layout="wide",
    page_icon="📄"
)

# -------------------
# Custom CSS - Fixed
# -------------------
st.markdown("""
<style>
    /* Main background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar background */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
    }
    
    /* Header styling */
    .main-header {
        color: white; 
        text-align: center; 
        font-weight: 700; 
        font-size: 2.5rem; 
        margin-bottom: 2rem; 
        text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Card styling */
    .content-card {
        background: white; 
        border-radius: 16px; 
        padding: 2rem; 
        box-shadow: 0 8px 32px rgba(0,0,0,0.1); 
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53); 
        color: white; 
        border: none; 
        border-radius: 12px; 
        padding: 0.75rem 2rem; 
        font-weight: 600; 
        font-size: 1.1rem;
        transition: all 0.3s ease; 
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px); 
        box-shadow: 0 6px 20px rgba(255,107,107,0.4);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border-radius: 12px; 
        border: 2px solid #e0e0e0; 
        font-family: 'Courier New', monospace; 
        font-size: 16px;
        transition: border 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea; 
        box-shadow: 0 0 0 2px rgba(102,126,234,0.2);
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 12px; 
        padding: 1rem; 
        font-weight: 500; 
        margin: 1rem 0;
        border: none;
    }
    
    /* Success alert */
    div[data-testid="stAlert"] div:has(> div[aria-label="success"]) {
        background: linear-gradient(45deg, #d4edda, #c3e6cb);
        color: #155724;
    }
    
    /* Warning alert */
    div[data-testid="stAlert"] div:has(> div[aria-label="warning"]) {
        background: linear-gradient(45deg, #fff3cd, #ffeeba);
        color: #856404;
    }
    
    /* Error alert */
    div[data-testid="stAlert"] div:has(> div[aria-label="error"]) {
        background: linear-gradient(45deg, #f8d7da, #f5c6cb);
        color: #721c24;
    }
    
    /* Missing character highlighting */
    .missing-char {
        background-color: #ff6b6b; 
        color: white; 
        padding: 2px 4px; 
        border-radius: 4px; 
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -------------------
# Sidebar settings
# -------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: white; margin-bottom: 0.5rem;'>⚙️</h1>
        <h2 style='color: white; font-weight: 600;'>Settings</h2>
    </div>
    """, unsafe_allow_html=True)
    
    paper_choice = st.selectbox("📄 Paper size", list(PAPER_SIZES.keys()), index=2)
    orientation_choice = st.selectbox("🔄 Orientation", ["Portrait", "Landscape"], index=1)
    letter_height_mm = st.selectbox("📏 Letter height (mm)", LETTER_HEIGHT_OPTIONS, index=2)

    # Admin section
    st.markdown("---")
    st.markdown("<h3 style='color: white;'>🔒 Admin Panel</h3>", unsafe_allow_html=True)
    password = st.text_input("Enter admin password", type="password")
    
    if password == ADMIN_PASSWORD:
        uploaded_files = st.file_uploader("📤 Upload PNG letters", type=["png","PNG"], accept_multiple_files=True)
        if uploaded_files:
            LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
            os.makedirs(LETTERS_FOLDER, exist_ok=True)
            for file in uploaded_files:
                with open(os.path.join(LETTERS_FOLDER, file.name), "wb") as f:
                    f.write(file.getbuffer())
            st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
    else:
        LETTERS_FOLDER = os.path.join(os.path.dirname(__file__), "ABC")
        if not os.path.exists(LETTERS_FOLDER):
            st.error("📁 Letter folder not found. Please contact administrator.")

# -------------------
# Main content
# -------------------
st.markdown("<h1 class='main-header'>📄 Text to PDF Converter</h1>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    
    # Text input section
    st.markdown("### ✍️ Enter Your Text")
    text_input = st.text_area(
        "Type your text below (each line will be treated as a separate line in the PDF):", 
        height=300, 
        placeholder="Enter your first line here...\nSecond line goes here...\nThird line...",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------
# Helper functions
# -------------------
def get_missing_chars(lines):
    missing_chars = set()
    for line in lines:
        for ch in line:
            if ch != " ":
                candidates = [f"{ch.upper()}.png", f"{ch.lower()}.png"]
                if not any(os.path.exists(os.path.join(LETTERS_FOLDER, c)) for c in candidates):
                    missing_chars.add(ch)
    return missing_chars

def check_line_width(line, page_w, letter_height_mm, margin_x=20*mm, space_width=15*mm):
    """Check if a line is too wide for the page"""
    x = margin_x
    letter_height = letter_height_mm * mm
    
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

def get_too_long_lines(lines, letter_height_mm):
    """Get list of line numbers that are too long"""
    page_size = PAPER_SIZES[paper_choice]
    if orientation_choice == "Landscape":
        page_w, _ = landscape(page_size)
    else:
        page_w, _ = portrait(page_size)
    
    too_long_lines = []
    for i, line in enumerate(lines):
        if check_line_width(line, page_w, letter_height_mm):
            too_long_lines.append(i + 1)  # +1 để hiển thị số dòng bắt đầu từ 1
    
    return too_long_lines

def generate_pdf(lines, pdf_path, letter_height_mm):
    page_size = PAPER_SIZES[paper_choice]
    if orientation_choice == "Landscape":
        page_w, page_h = landscape(page_size)
    else:
        page_w, page_h = portrait(page_size)
    letter_height = letter_height_mm * mm
    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    
    # Updated border margin to 2mm
    margin_x = 2*mm
    margin_y = 2*mm
    line_spacing = 20*mm
    current_y = page_h - margin_y - letter_height
    
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
            page_num += 1
        
        # Red border with 2mm margin
        c.setStrokeColorRGB(1, 0, 0)
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
# Download PDF Button
# -------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📥 Download PDF", key="download_pdf", use_container_width=True):
        lines = [line.strip() for line in text_input.splitlines() if line.strip()]
        
        if not lines:
            st.error("⚠️ Please enter at least one line of text.")
        else:
            # Check for missing characters
            missing_chars = get_missing_chars(lines)
            
            # Check for lines that are too long
            too_long_lines = get_too_long_lines(lines, letter_height_mm)
            
            errors = []
            
            if missing_chars:
                errors.append(f"❌ Missing PNG letters: {', '.join(sorted(missing_chars))}")
            
            if too_long_lines:
                errors.append(f"❌ Lines too long for selected paper size: {', '.join(map(str, too_long_lines))}")
            
            if errors:
                for error in errors:
                    st.error(error)
                st.stop()  # Stop execution if there are errors
            
            # Generate PDF if no errors
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_path = tmp_pdf.name
            
            try:
                generate_pdf(lines, tmp_path, letter_height_mm)
                
                with open(tmp_path, "rb") as f:
                    pdf_data = f.read()
                
                st.success("✅ PDF generated successfully! Click below to download.")
                
                # Download button
                st.download_button(
                    label="💾 Save PDF File",
                    data=pdf_data,
                    file_name="document.pdf",
                    mime="application/pdf",
                    key="final-download",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
