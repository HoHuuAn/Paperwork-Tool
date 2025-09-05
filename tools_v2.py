from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6 import uic, QtGui
import sys
import os

import modules.process_cccd as cccd
import modules.create_pdf_cccd as create_pdf_cccd
import modules.create_pdf_multi_cccd as create_pdf_multi_cccd
from modules.CCCD import CCCD
from modules.crop_paper import scan

CONFIG_FILE = 'path.txt'


class Tools(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('tools_v2.ui', self)
        self.show()

        # ======================================== Xử lý 1 CCCD ========================================
        self.process_and_create_file_button_1_page.clicked.connect(
            lambda: self.process(process=True, create_file_1_page=True))
        self.process_and_create_file_button_2_page.clicked.connect(
            lambda: self.process(process=True, create_file_2_page=True))

        self.single_cccd_decrease_button.clicked.connect(
            lambda: self.update_quantity('single_cccd', -1))
        self.single_cccd_increase_button.clicked.connect(
            lambda: self.update_quantity('single_cccd', 1))
        self.single_cccd_quantity.setText(str(1))

        # ======================================== Xử lý nhiều CCCD ========================================
        self.mulit_cccd_load_images.clicked.connect(lambda: self.load_images())

        self.mulit_cccd_create_file_button_1_page.clicked.connect(
            lambda: self.process_multi_cccd(create_file_1_page=True))
        self.mulit_cccd_create_file_button_2_page.clicked.connect(
            lambda: self.process_multi_cccd(create_file_2_page=True))

        self.mulit_cccd_decrease_button.clicked.connect(
            lambda: self.update_quantity('mulit_cccd', -1))
        self.mulit_cccd_increase_button.clicked.connect(
            lambda: self.update_quantity('mulit_cccd', 1))
        self.mulit_cccd_quantity.setText(str(1))
        self.list_of_images = []

        # ======================================== Cắt giấy A4 ========================================
        self.crop_paper_button.clicked.connect(lambda: self.crop_a4())

        self.last_path = self.load_last_path()

    def update_quantity(self, type: str, delta: int):
        if type == 'single_cccd':
            self.single_cccd_quantity.setText(
                str(max(1, int(self.single_cccd_quantity.text()) + delta)))
        else:
            self.mulit_cccd_quantity.setText(
                str(max(1, int(self.mulit_cccd_quantity.text()) + delta)))

    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return f.read().strip()

    def save_last_path(self, path):
        with open(CONFIG_FILE, 'w') as f:
            f.write(path)

     # ======================================== Xử lý 1 CCCD ========================================

    def process(self, process: bool = False, create_file_1_page: bool = False, create_file_2_page: bool = False):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            'Open files',
            self.last_path,
            "Images (*.jpg *.png *.jpeg *.gif)"
        )
        processed_images = []
        if file_paths:
            self.save_last_path(os.path.dirname(file_paths[-1]))

            # Xử lý ảnh
            if process:
                for path in file_paths:
                    processed_images.append(cccd.process(path))
            else:
                for path in file_paths:
                    processed_images.append(
                        CCCD(side=cccd.detect_id_card_side(image_path=path), path=path))

            # Sắp xếp ảnh
            if processed_images[0].get_side() == 'back':
                processed_images = processed_images[::-1]

            # Tạo file
            if create_file_2_page:
                create_pdf_cccd.create_pdf_2_page(images=processed_images,
                                                  pdf_output=os.path.dirname(
                                                      file_paths[-1]) + "/output.pdf",
                                                  count=int(self.single_cccd_quantity.text()))
            if create_file_1_page:
                create_pdf_cccd.create_pdf_1_page(images=processed_images,
                                                  pdf_output=os.path.dirname(
                                                      file_paths[-1]) + "/output.pdf",
                                                  count=int(self.single_cccd_quantity.text()))
            # Xóa ảnh đã xử lý
            for image in processed_images:
                os.remove(image.get_path())
            processed_images.clear()

    # ======================================== Xử lý nhiều CCCD ========================================

    def load_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            'Open files',
            self.last_path,
            "Images (*.jpg *.png *.jpeg *.gif)"
        )
        processed_images = []
        if file_paths:
            self.save_last_path(os.path.dirname(file_paths[-1]))

            for path in file_paths:
                processed_images.append(cccd.process(path))

            # Sắp xếp ảnh
            if processed_images[0].get_side() == 'back':
                processed_images = processed_images[::-1]

            self.list_of_images.append(processed_images)
            for image in self.list_of_images:
                print(image[0])
                print(image[1])

    def process_multi_cccd(self, create_file_1_page: bool = False, create_file_2_page: bool = False):
        try:
            if not self.list_of_images:
                QMessageBox.critical(
                    self, "Error", f"Làm ơn chọn ảnh CCCD trước")

            if create_file_1_page:
                create_pdf_multi_cccd.create_pdf_1_page(images=self.list_of_images,
                                                        pdf_output=os.path.dirname(
                                                            self.list_of_images[0][0].get_path()) + "/output.pdf",
                                                        count=int(self.mulit_cccd_quantity.text()))

            if create_file_2_page:
                create_pdf_multi_cccd.create_pdf_2_page(images=self.list_of_images,
                                                        pdf_output=os.path.dirname(
                                                            self.list_of_images[0][0].get_path()) + "/output.pdf",
                                                        count=int(self.mulit_cccd_quantity.text()))

            QMessageBox.information(
                self, "Success", "Tạo file thành công")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Đã có lỗi xảy ra: {e}")

        # Xóa ảnh đã xử lý
        for image in self.list_of_images:
            for i in image:
                os.remove(i.get_path())

        self.list_of_images.clear()

    # ======================================== Cắt giấy A4 ========================================

    def crop_a4(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            'Open files',
            self.last_path,
            "Images (*.jpg *.png *.jpeg *.gif)"
        )
        if file_paths:
            self.save_last_path(os.path.dirname(file_paths[-1]))

            for path in file_paths:
                scan(path)
            QMessageBox.information(
                self, "Success", "Cắt giấy A4 thành công")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    tools = Tools()
    app.exec()
