from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt6 import uic, QtGui
import sys
import os

import modules.process_cccd as cccd
import modules.create_pdf_cccd as create_pdf_cccd
from modules.CCCD import CCCD

CONFIG_FILE = 'path.txt'

class Tools(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('tools.ui', self)
        self.show()
        self.process_cccd_button.clicked.connect(lambda: self.process(process = True, create_file= False))

        self.process_and_create_file_button.clicked.connect(lambda: self.process(process = True, create_file= True))

        self.decrease_button.clicked.connect(lambda: self.update_quantity('crop', -1))
        self.increase_button.clicked.connect(lambda: self.update_quantity('crop', 1))
        self.quantity.setText(str(1))

        self.create_file_button.clicked.connect(lambda: self.process(process = False, create_file= True))

        self.decrease_none_crop_button.clicked.connect(lambda: self.update_quantity('none_crop', -1))
        self.increase_none_crop_button.clicked.connect(lambda: self.update_quantity('none_crop', 1))
        self.quantity_none_crop.setText(str(1))

        self.last_path = self.load_last_path()


    def update_quantity(self, type: str, delta: int):
        if type == 'crop':
            self.quantity.setText(str(max(1, int(self.quantity.text()) + delta)))
        else: 
            self.quantity_none_crop.setText(str(max(1, int(self.quantity_none_crop.text()) + delta)))

    def load_last_path(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return f.read().strip()

    def save_last_path(self, path):
        with open(CONFIG_FILE, 'w') as f:
            f.write(path)

    def process(self, process:bool, create_file:bool):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            'Open files',
            self.last_path,
            "Images (*.jpg *.png *.jpeg *.gif)"
        )
        processed_images = []
        if file_paths:
            self.save_last_path(os.path.dirname(file_paths[-1]))
            
            if process:
                for path in file_paths:
                    processed_images.append(cccd.process(path))
            else:
                for path in file_paths:
                    processed_images.append(CCCD(side = cccd.detect_id_card_side(image_path=path), path = path))
            
            if processed_images[0].get_side() == 'back':
                processed_images = processed_images[::-1]

            if create_file:
                create_pdf_cccd.create_pdf(images=processed_images,  
                                           pdf_output=os.path.dirname(file_paths[-1]) + "/output.pdf", 
                                           count = int(self.quantity.text() if process else self.quantity_none_crop.text()))


    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    tools = Tools()
    app.exec()