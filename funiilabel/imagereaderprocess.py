from multiprocessing import Process, Manager, Event
import cv2
import time
import logging

TIMEOUT = 15 #sec

class ImageReaderProcess(Process):
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.image_managed_dict = Manager().dict()
        self.stop_event = Event()
        self.finished_event = Event()

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        while not self.stop_event.is_set():
            frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            _, frame = cap.read()
            if frame is None:
                self.finished_event.set()
                return
            self.image_managed_dict[frame_number] = frame
        
    def __getitem__(self, key):
        if self.finished_event.is_set():
            if key not in self.image_managed_dict.keys():
                logging.error("Image {} not in video".format(key))
                return None

        start_time = time.time()
        while (time.time() - start_time) < TIMEOUT:
            if key in self.image_managed_dict.keys():
                return self.image_managed_dict[key]
            time.sleep(0.1)
        raise Exception('Image not loaded in time or not found')

    def __len__(self):
        return max(self.image_managed_dict.keys())