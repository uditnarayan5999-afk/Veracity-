import io
import pytesseract
from PIL import Image
from pypdf import PdfReader
from docx import Document

# Explicitly set tesseract path for Apple Silicon Macs
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    filename = filename.lower()
    text = ""
    try:
        if filename.endswith('.pdf'):
            text_parts = []
            pdf = PdfReader(io.BytesIO(file_content))
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            text = "\n".join(text_parts)
        elif filename.endswith('.docx'):
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
            img = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(img)
        elif filename.endswith('.txt') or filename.endswith('.md') or filename.endswith('.c') or filename.endswith('.cpp') or filename.endswith('.js') or filename.endswith('.py'):
            text = file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        
    return text.strip()
