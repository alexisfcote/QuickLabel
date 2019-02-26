import sys
import time
import os
import pathlib
import re
import numpy as np

import pkg_resources
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QDialog,
                             QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                             QToolBar, QVBoxLayout, QWidget)

import cv2

class FuniiLabel(QMainWindow):
    """Create the main window that stores all of the widgets necessary for the application."""

    def __init__(self, parent=None):
        """Initialize the components of the main window."""
        super(FuniiLabel, self).__init__(parent)
        self.setWindowTitle("FuniiLabel")
        window_icon = pkg_resources.resource_filename(
            "funiilabel.images", "ic_insert_drive_file_black_48dp_1x.png"
        )
        self.setWindowIcon(QIcon(window_icon))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.label = QLabel(self)

        layout.addWidget(self.label)

        self.menu_bar = self.menuBar()
        self.about_dialog = AboutDialog()

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready", 5000)

        self.file_menu()
        self.help_menu()

        self.filename = None
        self.last_label = None
        self.batch = None

    def file_menu(self):
        """Create a file submenu with an Open File item that opens a file dialog."""
        self.file_sub_menu = self.menu_bar.addMenu("File")

        self.open_action = QAction("Open File", self)
        self.open_action.setStatusTip("Open a file to label.")
        self.open_action.setShortcut("CTRL+O")
        self.open_action.triggered.connect(self.open_file)

        self.open_batch_action = QAction("Open Batch", self)
        self.open_batch_action.setStatusTip("Open a folder with all video to label.")
        self.open_batch_action.setShortcut("CTRL+B")
        self.open_batch_action.triggered.connect(self.open_batch)

        self.exit_action = QAction("Exit Application", self)
        self.exit_action.setStatusTip("Exit the application.")
        self.exit_action.setShortcut("CTRL+Q")
        self.exit_action.triggered.connect(lambda: QApplication.quit())

        self.record_label_to_file_action = QAction("Record label", self)
        self.record_label_to_file_action.setStatusTip("Record labelled video to file.")
        self.record_label_to_file_action.setShortcut("CTRL+R")
        self.record_label_to_file_action.triggered.connect(self.record_label_to_file)


        self.file_sub_menu.addAction(self.open_action)
        self.file_sub_menu.addAction(self.open_batch_action)
        self.file_sub_menu.addAction(self.exit_action)
        self.file_sub_menu.addAction(self.record_label_to_file_action)

    def help_menu(self):
        """Create a help submenu with an About item tha opens an about dialog."""
        self.help_sub_menu = self.menu_bar.addMenu("Help")

        self.about_action = QAction("About", self)
        self.about_action.setStatusTip("About the application.")
        self.about_action.setShortcut("CTRL+H")
        self.about_action.triggered.connect(lambda: self.about_dialog.exec_())

        self.help_sub_menu.addAction(self.about_action)

    def open_file(self):
        """Open a QFileDialog to allow the user to open a file into the application."""
        filename, accepted = QFileDialog.getOpenFileName(self, "Open File")

        if accepted:
            self.load_file(filename)

    def open_batch(self):
        foldername = QFileDialog.getExistingDirectory(self, "Open Folder")
        if foldername:
            print(foldername)


    def load_file(self, filename):
        self.filename = filename
        self.last_label = None
        self.cap = cv2.VideoCapture(self.filename)
        _, frame = self.cap.read()
        self.frame = frame
        self.height, self.width, self.channel = frame.shape
        self.bytesPerLine = 3 * self.width
        self.resize(self.width, self.height)
        self.display_next_image()


    def display_next_image(self):
        # Capture frame-by-frame
        ret, frame = self.cap.read()
        self.frame = np.copy(frame)
        if not ret:
            return False
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame,self.last_label,(10,self.height-10), font, 4,(255,255,255),3,cv2.LINE_AA)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        qImg = QImage(frame.data, self.width, self.height, self.bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)
        return True

    def record_label(self):
        path = pathlib.Path(self.filename)
        path.parent.joinpath('label').mkdir(exist_ok=True)
        path = (path.parent.joinpath('label') / 
               (path.stem 
               + '_frame_' + str(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)-1)) 
               + '_label_' + self.last_label 
               + '.jpeg'))
        cv2.imwrite(str(path), self.frame)

    def record_label_to_file(self):
        """Open a QFileDialog to allow the user to open a file into the application."""
        filename, accepted = QFileDialog.getOpenFileName(self, "Open File")
        if accepted:
            self.write_label_to_file(filename)

    def write_label_to_file(self, filename):
        path = pathlib.Path(filename)
        path.parent.joinpath('label').mkdir(exist_ok=True)
        path = (path.parent.joinpath('label') / 
            (path.stem 
            + '.txt'))

        with open(path, 'w') as f:
            f.write('Frame, Label\n')
            labels = []
            for file in path.parent.glob(path.stem + '*.jpeg'):
                labels.append(re.search('_frame_(\d*)_label_(.*)\.jpeg', str(file)).groups())
                labels[-1] = (int(labels[-1][0]), labels[-1][1])
            labels = sorted(labels, key=lambda tup: tup[0])
            f.writelines([str(x) + ',' + y + '\n' for x, y in labels])

            

    def keyPressEvent(self, e):
        if self.filename is not None:
            label = None
            if e.key() == Qt.Key_Backspace:
                current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame - 2)
                self.display_next_image()
                return

            if e.key() == Qt.Key_F:
                label = 'Fight'
            if e.key() == Qt.Key_S:
                label = 'Stealth'
            if e.key() == Qt.Key_E:
                label = 'Explore'
            if e.key() == Qt.Key_O:
                label = 'Other'
            if label is None:
                return

            self.last_label = label
            self.record_label()
            if not self.display_next_image():
                # Video ended
                self.write_label_to_file(self.filename)
                self.status_bar.showMessage('VideoEnded')
                self.filename = None
                self.cap.release()

class AboutDialog(QDialog):
    """Create the necessary elements to show helpful text in a dialog."""

    def __init__(self, parent=None):
        """Display a dialog that shows application information."""
        super(AboutDialog, self).__init__(parent)

        self.setWindowTitle("About")
        help_icon = pkg_resources.resource_filename(
            "funiilabel.images", "ic_help_black_48dp_1x.png"
        )
        self.setWindowIcon(QIcon(help_icon))
        self.resize(300, 200)

        author = QLabel("Alexis Fortin-Cote")
        author.setAlignment(Qt.AlignCenter)

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignVCenter)

        self.layout.addWidget(author)

        self.setLayout(self.layout)


def main():
    application = QApplication(sys.argv)
    window = FuniiLabel()
    desktop = QDesktopWidget().availableGeometry()
    width = (desktop.width() - window.width()) / 2
    height = (desktop.height() - window.height()) / 2
    window.show()
    window.move(width, height)
    sys.exit(application.exec_())


if __name__ == "__main__":
    main()
