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
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QDesktopWidget,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

import cv2
from funiilabel.config import *
from funiilabel.gui import FuniiLabelGUI
from funiilabel.predictprocess import PredictProcess, Manager, Event, FASTAI
from funiilabel.imagereaderprocess import ImageReaderProcess
from funiilabel.labelrecorderprocess import LabelRecorderProcess

FONT = cv2.FONT_HERSHEY_SIMPLEX


class FuniiLabel(FuniiLabelGUI):
    """Create the main window that stores all of the widgets necessary for the application."""

    def __init__(self, parent=None):
        """Initialize the components of the main window."""
        super(FuniiLabel, self).__init__(parent)

        self.filename = None
        self.last_label = None
        self.batch = []
        self.image_managed_dict = None
        self.managed_dict = None
        self.image_reader_process = None
        self.prediction_process = None
        self.label_recorder_process = None
        self.current_frame_number = 0

    def load_file(self, filename):
        self.filename = filename
        self.status_bar.showMessage("Video Loaded", 5000)
        self.last_label = None
        cap = cv2.VideoCapture(self.filename)
        _, frame = cap.read()
        cap.release()
        self.frame = frame
        self.height, self.width, self.channel = frame.shape
        self.bytesPerLine = 3 * self.width
        self.resize(self.width, self.height)

        self.image_reader_process = ImageReaderProcess(self.filename)
        self.image_reader_process.start()
        self.current_frame_number = 0

        self.label_recorder_process = LabelRecorderProcess(self.filename)
        self.label_recorder_process.start()

        if FASTAI:
            model_path = pkg_resources.resource_filename(
            "models", "cnn1.pkl"
        )
            self.prediction_process = PredictProcess(
                model_path, filename, self.image_reader_process)
            self.prediction_process.start()

        self.display_next_image()
        if len(self.batch) > 0:
            self.status_bar.showMessage(
                f"{self.filename}. {len(self.batch)} files to go"
            )
        else:
            self.status_bar.showMessage(f"{self.filename}.")

    def add_fast_ai_text(self, frame, label, proba):
        n = 0
        for key, val in proba.items():
            color = (100, 255, 100) if key == label else (255, 255, 255)
            cv2.putText(
                frame,
                "{:10s}".format(key),
                (10, self.height - 200 + n * 30),
                FONT,
                1,
                color,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                ": {:.2f}".format(val),
                (150, self.height - 200 + n * 30),
                FONT,
                1,
                color,
                2,
                cv2.LINE_AA,
            )
            n += 1

        return frame

    def display_next_image(self):
        # Capture frame-by-frame
        frame = self.image_reader_process[self.current_frame_number]
        self.frame = np.copy(frame)
        if frame is None:
            return False

        if (
            FASTAI
            and self.current_frame_number in self.prediction_process.managed_dict.keys()
        ):
            label, proba = self.prediction_process.managed_dict[
                self.current_frame_number
            ]
            self.add_fast_ai_text(frame, label, proba)

        cv2.putText(
            frame,
            self.last_label,
            (10, self.height - 10),
            FONT,
            4,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            str(self.current_frame_number) + "/" + str(len(self.image_reader_process)),
            (self.width - 250, self.height - 10),
            FONT,
            1,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        qImg = QImage(
            frame.data, self.width, self.height, self.bytesPerLine, QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)
        self.current_frame_number += 1

        return True

    def record_label_to_file(self):
        """Open a QFileDialog to allow the user to open a file into the application."""
        filename, accepted = QFileDialog.getOpenFileName(self, "Open File")
        if accepted:
            self.write_labels_to_file(filename)

    def write_labels_to_file(self, filename):
        path = pathlib.Path(filename)
        path.parent.joinpath("label").mkdir(exist_ok=True)
        path = path.parent.joinpath("label") / (path.stem + ".txt")

        with open(path, "w") as f:
            f.write("Frame, Label\n")
            labels = []
            for file in path.parent.glob(path.stem + "*.jpeg"):
                labels.append(
                    re.search(r"_frame_(\d*)_label_(.*)\.jpeg", str(file)).groups()
                )
                labels[-1] = (int(labels[-1][0]), labels[-1][1])
            labels = sorted(labels, key=lambda tup: tup[0])
            f.writelines([str(x) + "," + y + "\n" for x, y in labels])

    def keyPressEvent(self, e):
        if self.filename is not None:
            label = None
            if e.key() == Qt.Key_Backspace:
                self.current_frame_number -= 2
                self.current_frame_number = max(0, self.current_frame_number)
                self.last_label = None
                self.display_next_image()
                return

            if e.key() == Qt.Key_F:
                label = "Fight"
            if e.key() == Qt.Key_S:
                label = "Stealth"
            if e.key() == Qt.Key_E:
                label = "Explore"
            if e.key() == Qt.Key_O:
                label = "Other"

            if label is not None:
                self.last_label = label
                self.label_recorder_process.record(
                    frame_number=self.current_frame_number,
                    label=label,
                    frame=self.frame,
                )

            if not self.display_next_image():
                # Video ended
                self.write_labels_to_file(self.filename)
                self.status_bar.showMessage("VideoEnded")
                self.filename = None
                if len(self.batch) > 0:
                    self.load_file(self.batch.pop())

    def closeEvent(self, event):
        for proc in [self.image_reader_process, self.prediction_process, self.label_recorder_process]:
            if proc is not None:
                proc.stop_event.set()
                proc.join()


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
    logging.basicConfig(level=logging.DEBUG)
    main()
