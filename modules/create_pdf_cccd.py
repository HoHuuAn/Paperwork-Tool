from fpdf import FPDF
import modules.CCCD as CCCD

def create_pdf(images:list, pdf_output:str, count:int):
    pdf = FPDF('P', 'mm', 'A4')

    cell_width = pdf.w/2 - 10
    cell_height = 60
    margin = 8

    margin_left = 10

    while (count > 0):
        quantity_per_page = 4 if count >= 4 else count
        for image in images:
            pdf.add_page()
            if image.get_side() == 'front':
                for index in range(0, quantity_per_page):
                    pdf.set_xy(margin_left + cell_width, margin +
                               index * (cell_height + margin))
                    pdf.image(image.get_path(), w=cell_width, h=cell_height)

            elif image.get_side() == 'back':
                for index in range(0, quantity_per_page):
                    pdf.set_xy(margin, margin + index * (cell_height + margin))
                    pdf.image(image.get_path(), w=cell_width, h=cell_height)

        count -= quantity_per_page

    pdf.output(pdf_output)
