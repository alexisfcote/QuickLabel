import os
import pathlib
import re
import sys
import logging
import time

import numpy as np
import pkg_resources
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QDialog,
                             QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                             QVBoxLayout, QWidget)

import cv2
from funiilabel.config import *
from funiilabel.predictprocess import PredictProcess, Manager, Event, FASTAI
from funiilabel.imagereaderprocess import ImageReaderProcess

FONT = cv2.FONT_HERSHEY_SIMPLEX



class FuniiLabelGUI(QMainWindow):
    """Create the main window that stores all of the widgets necessary for the application."""

    def __init__(self, parent=None):
        """Initialize the components of the main window."""
        super(FuniiLabelGUI, self).__init__(parent)
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
            self.batch = []

    def load_file(self, file):
        raise NotImplementedError

    def open_batch(self):
        folderpath = pathlib.Path(QFileDialog.getExistingDirectory(self, "Open Folder"))
        if not folderpath:
            return

        self.batch = []
        files = folderpath.glob("*.mp4")
        already_labelled_files = set([x.stem.split('_frame_')[0] for x in (folderpath / 'label').glob('*.jpeg')])

        for file in files:
            if os.path.getsize(folderpath / file) > MIN_FILE_SIZE:
                if not (folderpath / file).stem in already_labelled_files:
                    self.batch.append(str(folderpath / file))

        if len(self.batch) > 0:
            self.load_file(self.batch.pop())


    def record_label_to_file(self):
        """Open a QFileDialog to allow the user to open a file into the application."""
        filename, accepted = QFileDialog.getOpenFileName(self, "Open File")
        if accepted:
            self.write_label_to_file(filename)


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
