from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6 import uic, QtGui
import sys
import os
import logging
from datetime import datetime

import modules.process as cccd
import modules.create_pdf_multi_cccd as create_pdf_multi_cccd
from modules.CCCD import CCCD

CONFIG_FILE = 'path.txt'
LOG_FILE = 'app.log'

# Setup logging to file - only ERROR and CRITICAL
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


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
        # Clear list_of_images at the start of each process to avoid stale references
        self.list_of_images = []
        if file_paths:
            self.save_last_path(os.path.dirname(file_paths[-1]))

            # Cập nhật progressBar
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(len(file_paths))
            self.progressBar.setValue(0)
            QApplication.processEvents()

            # Xử lý ảnh
            for idx, path in enumerate(file_paths):
                try:
                    result = cccd.process(path)
                    processed_images.append(result)
                except Exception as e:
                    logger.error(f"Error processing {path}: {str(e)}", exc_info=True)
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
            unpaired_ids = []  # IDs with only 1 image (missing front or back)
            filtered_pairs = {}
            for img_id, pair in pairs.items():
                if len(pair) == 2:
                    if all(getattr(img, 'processed', True) for img in pair):
                        filtered_pairs[img_id] = pair
                    else:
                        error_pairs.append(img_id)
                else:
                    # ID with only 1 image (missing front or back)
                    unpaired_ids.append(img_id)
            pairs = filtered_pairs

            # Thêm từng cặp vào list_of_images
            for img_id in sorted(pairs.keys()):
                pair = pairs[img_id]
                self.list_of_images.append(pair)

            # Tạo file
            if self.list_of_images and len(self.list_of_images) > 0 and len(self.list_of_images[0]) > 0:
                try:
                    if create_file_1_page:
                        output_path = os.path.dirname(self.list_of_images[0][0].get_path()) + "/output.pdf"
                        create_pdf_multi_cccd.create_pdf_1_page(images=self.list_of_images,
                                                                pdf_output=output_path,
                                                                count=int(self.quantity.text()))
                        QMessageBox.information(self, "THÀNH CÔNG", "Hoàn Thành!")

                    if create_file_2_page:
                        output_path = os.path.dirname(self.list_of_images[0][0].get_path()) + "/output.pdf"
                        create_pdf_multi_cccd.create_pdf_2_page(images=self.list_of_images,
                                                                pdf_output=output_path,
                                                                count=int(self.quantity.text()))
                        QMessageBox.information(self, "THÀNH CÔNG", "Hoàn Thành!")
                except Exception as e:
                    QMessageBox.critical(self, "LỖI", f"Lỗi tạo PDF: {str(e)}")
            else:
                # No valid pairs found - show error
                QMessageBox.warning(self, "CẢNH BÁO", "Không tìm thấy cặp ảnh hợp lệ nào!")

            # Không xóa ảnh đã xử lý - giữ lại để kiểm tra
            # for image in processed_images:
            #     os.remove(image.get_path())
            processed_images.clear()

            # Đặt progressBar về 0 khi xong
            self.progressBar.setValue(0)
            QApplication.processEvents()

            # Show errors if any
            error_messages = []
            if error_pairs:
                msg = f"Các ID lỗi xử lý: {', '.join(str(i) for i in error_pairs)}"
                error_messages.append(msg)
                logger.error(msg)
            if unpaired_ids:
                msg = f"Các ID thiếu mặt trước/sau: {', '.join(str(i) for i in unpaired_ids)}"
                error_messages.append(msg)
                logger.error(msg)
            
            if error_messages:
                QMessageBox.critical(self, "THẤT BẠI", "\n".join(error_messages))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    tools = Tools()
    app.exec()
