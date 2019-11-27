from multiprocessing import Process, Manager, Event, Queue
import queue
import cv2
import time
import logging
import pathlib


class LabelRecorderProcess(Process):
    def __init__(self, filename):
        super().__init__()
        self.label_queue = Queue()
        self.stop_event = Event()
        path = pathlib.Path(filename)
        path.parent.joinpath("label").mkdir(exist_ok=True)
        self.basepath = path.parent.joinpath("label") / path.stem

    def run(self):
        while not self.stop_event.is_set() or not self.label_queue.empty():
            try:
                frame_number, label, frame = self.label_queue.get_nowait()
                self._record_label(frame_number, label, frame)
            except queue.Empty:
                time.sleep(0.1)

    def record(self, frame_number, label, frame):
        self.label_queue.put((frame_number, label, frame))

    def _record_label(self, frame_number, label, frame):
        logging.debug('Writing frame {} to file'.format(frame_number))
        path = (str(self.basepath)
            + "_frame_"
            + str(frame_number)
            + "_label_"
            + label
            + ".jpeg"
        )
        cv2.imwrite(path, frame)