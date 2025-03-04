from fpdf import FPDF
import os
import PyPDF2

def chunker(seq: list, size: int):
    """Yield successive chunks of the given size from seq."""
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def reorder_pdf(input_pdf_path: str, output_pdf_path: str):
    """
    Reorders a PDF with an even number of pages by splitting it into
    two halves and interleaving them. For example, with 6 pages, produces:
    page 1, page 4, page 2, page 5, page 3, page 6.
    """
    reader = PyPDF2.PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    if total_pages % 2 != 0:
        raise ValueError("PDF does not have an even number of pages.")
    half = total_pages // 2
    writer = PyPDF2.PdfWriter()
    for i in range(half):
        writer.add_page(reader.pages[i])
        writer.add_page(reader.pages[i + half])
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

def create_pdf_2_page(images: list, pdf_output: str, count: int = 1):
    """
    Expects images as a list of pairs: [ [front, back], [front, back], ... ].
    For each pair, the function inserts it count times.
    It first creates front pages (with front images placed on the right)
    and back pages (with back images placed on the left). After generating
    the temporary PDF, it is reordered so that the first half and second half
    are interleaved (e.g., P1, P4, P2, P5, P3, P6 for a 6-page PDF).
    """
    # Create a temporary PDF file
    temp_pdf = "temp_output.pdf"
    pdf = FPDF('P', 'mm', 'A4')
    
    cell_width = pdf.w / 2 - 10
    cell_height = 60
    margin = 8
    margin_left = 10
    pairs_per_page = 4

    # Build lists for repeated front and back images
    front_rows = []
    back_rows = []
    for pair in images:
        for _ in range(count):
            front_rows.append(pair[0])
            back_rows.append(pair[1])
    
    # Create pages for front images (positioned on the right)
    for chunk in chunker(front_rows, pairs_per_page):
        pdf.add_page()
        for idx, image in enumerate(chunk):
            pdf.set_xy(margin_left + cell_width, margin + idx * (cell_height + margin))
            pdf.image(image.get_path(), w=cell_width, h=cell_height)
    
    # Create pages for back images (positioned on the left)
    for chunk in chunker(back_rows, pairs_per_page):
        pdf.add_page()
        for idx, image in enumerate(chunk):
            pdf.set_xy(margin, margin + idx * (cell_height + margin))
            pdf.image(image.get_path(), w=cell_width, h=cell_height)
    
    pdf.output(temp_pdf)
    
    # Reorder pages so that pages are interleaved from the two halves.
    reorder_pdf(temp_pdf, pdf_output)
    os.remove(temp_pdf)



def create_pdf_1_page(images: list, pdf_output: str, count: int = 1):
    """
    Expects images as a list of pairs: [ [front, back], [front, back], ... ].
    For each pair, the function inserts it count times.
    On each page, up to 4 rows are printed, with the front image on the left and the back image on the right.
    """
    pdf = FPDF('P', 'mm', 'A4')
    
    cell_width = pdf.w / 2 - 10
    cell_height = 60
    margin = 8
    margin_left = 10
    pairs_per_page = 4

    # Build a list of pair rows repeated count times
    pair_rows = []
    for pair in images:
        for _ in range(count):
            pair_rows.append(pair)
    
    # Create pages with up to 4 pair rows per page
    for chunk in chunker(pair_rows, pairs_per_page):
        pdf.add_page()
        for idx, pair in enumerate(chunk):
            front, back = pair[0], pair[1]
            # Front image on the left
            pdf.set_xy(margin, margin + idx * (cell_height + margin))
            pdf.image(front.get_path(), w=cell_width, h=cell_height)
            # Back image on the right
            pdf.set_xy(margin_left + cell_width, margin + idx * (cell_height + margin))
            pdf.image(back.get_path(), w=cell_width, h=cell_height)
    
    pdf.output(pdf_output)