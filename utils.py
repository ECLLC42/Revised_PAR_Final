# utils.py

import logging
import PyPDF2
from reportlab.pdfgen import canvas
import os
import markdown2
from io import BytesIO
from PyPDF2 import PdfReader
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
from html import escape
from xml.etree.ElementTree import fromstring, ParseError
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER

sys.setrecursionlimit(5000)  # Increase as needed, but be cautious

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}

def extract_text_with_pypdf2(pdf_path):
    logging.info(f"Extracting text from {pdf_path} using PyPDF2")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def create_blank_pdf(filename, output_folder):
    """Create a blank PDF file with the given filename in the output folder."""
    filepath = os.path.join(output_folder, filename)
    c = canvas.Canvas(filepath)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"This is a blank file for {filename}")
    c.save()
    logging.info(f"Created blank PDF: {filepath}")
    return filepath

def extract_text_from_pdf_bytes(pdf_bytes):
    pdf = PdfReader(BytesIO(pdf_bytes))
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text

def simple_markdown_to_pdf(cover_content, toc_content, markdown_content):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

    # Add cover page
    elements.append(Paragraph(cover_content, styles['Normal']))
    elements.append(PageBreak())

    # Add table of contents
    elements.append(Paragraph(toc_content, styles['Normal']))
    elements.append(PageBreak())

    # Process markdown content
    lines = markdown_content.split('\n')
    for line in lines:
        if line.strip():
            if line.startswith('# '):
                elements.append(Paragraph(line[2:], styles['Heading1']))
            elif line.startswith('## '):
                elements.append(Paragraph(line[3:], styles['Heading2']))
            else:
                elements.append(Paragraph(line, styles['Normal']))
        else:
            elements.append(Spacer(1, 0.2*inch))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

UTILS_VERSION = "1.0"
print(f"Utils module version: {UTILS_VERSION}")