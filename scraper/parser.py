
from pypdf import PdfReader
from utils.logger import logger

def parse_pdf(file_path, case_number):
    try:
        reader = PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        lines = text.split('\n')
        serial = None
        court_name = None
        for line in lines:
            if case_number in line:
                words = line.strip().split()
                if words and words[0].isdigit():
                    serial = words[0]
                break
        return serial, court_name, None
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return None, None, f"Error parsing PDF: {e}"
