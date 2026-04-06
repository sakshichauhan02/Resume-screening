import pdfplumber

def extract_text_from_pdf(file):
    """
    Extracts text from a given PDF file object using pdfplumber.
    """
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted_page_text = page.extract_text()
                if extracted_page_text:
                    text += extracted_page_text + "\n"
    except Exception as e:
        return f"Error extracting text: {str(e)}"
    
    return text.strip() or "No text found in PDF."
