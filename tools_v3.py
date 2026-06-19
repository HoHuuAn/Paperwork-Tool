from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6 import uic, QtGui
import sys
import os
import logging

from common.ulti import build_image_pairs
import modules.process as cccd
import modules.create_pdf_multi_cccd as create_pdf_multi_cccd

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
                    if result is not None:
                        processed_images.append(result)
                except Exception as e:
                    logger.error(f"Error processing {path}: {str(e)}", exc_info=True)
                self.progressBar.setValue(idx + 1)
                QApplication.processEvents()

            # Pair all detected fronts/backs, including repeated or unreadable IDs.
            self.list_of_images, error_pairs, unpaired_ids = build_image_pairs(processed_images)

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
