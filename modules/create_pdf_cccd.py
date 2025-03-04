from fpdf import FPDF


def create_pdf_2_page(images: list, pdf_output: str, count: int = 1):
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


def create_pdf_1_page(images: list, pdf_output: str, count: int = 1):
    pdf = FPDF('P', 'mm', 'A4')

    cell_width = pdf.w / 2 - 10
    cell_height = 60
    margin = 8
    margin_left = 10

    front_image = None
    back_image = None
    for image in images:
        if image.get_side() == 'front':
            front_image = image
        elif image.get_side() == 'back':
            back_image = image

    while count > 0:
        quantity_per_page = 4 if count >= 4 else count
        pdf.add_page()
        for index in range(quantity_per_page):
            # Place front image on the left
            pdf.set_xy(margin, margin + index * (cell_height + margin))
            pdf.image(front_image.get_path(), w=cell_width, h=cell_height)

            # Place back image on the right
            pdf.set_xy(margin_left + cell_width, margin +
                       index * (cell_height + margin))
            pdf.image(back_image.get_path(), w=cell_width, h=cell_height)

        count -= quantity_per_page

    pdf.output(pdf_output)
