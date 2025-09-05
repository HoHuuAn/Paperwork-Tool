from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6 import uic, QtGui
import sys
import os

import modules.process as cccd
import modules.create_pdf_multi_cccd as create_pdf_multi_cccd
from modules.CCCD import CCCD

CONFIG_FILE = 'path.txt'


class Tools(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('tools_v3.ui', self)
        self.show()

        # ======================================== KHAI BÁO ========================================
        self.process_and_create_file_button_1_page.clicked.connect(
            lambda: self.process(create_file_1_page=True))
        self.process_and_create_file_button_2_page.clicked.connect(
            lambda: self.process(create_file_2_page=True))

        self.decrease_button.clicked.connect(
            lambda: self.update_quantity(-1))
        self.increase_button.clicked.connect(
            lambda: self.update_quantity(1))
        self.quantity.setText(str(1))

        self.last_path = self.load_last_path()
        self.list_of_images = []

    def update_quantity(self, delta: int):
        self.quantity.setText(
            str(max(1, int(self.quantity.text()) + delta)))

    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return f.read().strip()

    def save_last_path(self, path):
        with open(CONFIG_FILE, 'w') as f:
            f.write(path)

     # ======================================== XỬ LÝ ========================================

    def process(self, create_file_1_page: bool = False, create_file_2_page: bool = False):

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            'Open files',
            self.last_path,
            "Images (*.jpg *.png *.jpeg *.gif)"
        )
        processed_images = []
        if file_paths:
            self.save_last_path(os.path.dirname(file_paths[-1]))

            # Cập nhật progressBar
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(len(file_paths))
            self.progressBar.setValue(0)
            QApplication.processEvents()

            # Xử lý ảnh
            for idx, path in enumerate(file_paths):
                processed_images.append(cccd.process(path))
                self.progressBar.setValue(idx + 1)
                QApplication.processEvents()

            # Sắp xếp ảnh: luôn để ảnh 'front' trước 'back' nếu cùng id
            processed_images.sort(key=lambda img: (
                img.get_id(), 0 if img.get_side() == 'front' else 1))

            # Nhóm ảnh thành các cặp dựa trên ID
            pairs = {}
            for img in processed_images:
                img_id = img.get_id()
                if img_id not in pairs:
                    pairs[img_id] = []
                pairs[img_id].append(img)

            # Loại bỏ các cặp mà bất kỳ ảnh nào có processed == False
            error_pairs = []
            filtered_pairs = {}
            for img_id, pair in pairs.items():
                if len(pair) == 2:
                    if all(getattr(img, 'processed', True) for img in pair):
                        filtered_pairs[img_id] = pair
                    else:
                        error_pairs.append(img_id)
            pairs = filtered_pairs

            # Thêm từng cặp vào list_of_images
            for img_id in sorted(pairs.keys()):
                pair = pairs[img_id]
                if len(pair) == 2:  # Đảm bảo có đủ front và back
                    self.list_of_images.append(pair)
                else:
                    print(
                        f"Cảnh báo: ID {img_id} không có đủ 2 ảnh (front và back)")

            # Tạo file
            if create_file_1_page and self.list_of_images and len(self.list_of_images) > 0 and len(self.list_of_images[0]) > 0:
                create_pdf_multi_cccd.create_pdf_1_page(images=self.list_of_images,
                                                        pdf_output=os.path.dirname(
                                                            self.list_of_images[0][0].get_path()) + "/output.pdf",
                                                        count=int(self.quantity.text()))
                QMessageBox.information(self, "THÀNH CÔNG", "Hoàn Thành!")

            if create_file_2_page and self.list_of_images and len(self.list_of_images) > 0 and len(self.list_of_images[0]) > 0:
                create_pdf_multi_cccd.create_pdf_2_page(images=self.list_of_images,
                                                        pdf_output=os.path.dirname(
                                                            self.list_of_images[0][0].get_path()) + "/output.pdf",
                                                        count=int(self.quantity.text()))
                QMessageBox.information(self, "THÀNH CÔNG", "Hoàn Thành!")

            # Xóa ảnh đã xử lý
            for image in processed_images:
                os.remove(image.get_path())
            processed_images.clear()

            # Đặt progressBar về 0 khi xong
            self.progressBar.setValue(0)
            QApplication.processEvents()

            if error_pairs:
                QMessageBox.critical(
                    self, "THẤT BẠI", f"Các ID lỗi: {', '.join(str(i) for i in error_pairs)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    tools = Tools()
    app.exec()
