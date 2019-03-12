from multiprocessing import Process, Manager, Event, Queue
import cv2
import time
import logging
import numpy as np
import queue
import gc

TIMEOUT = 15 #sec
MAXFRAMEBUFFER = 1000

class ImageReaderProcess(Process):
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.image_managed_dict = Manager().dict()
        self.stop_event = Event()
        self.to_grab_queue = Queue(maxsize=1_000_000)
        self.last_frame = Manager().Value('i', 999999)

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        self.last_frame.value = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))-1
        while not self.stop_event.is_set():
            try:
                frame_to_grab = self.to_grab_queue.get(timeout=1)
            except queue.Empty:
                continue
            if frame_to_grab in self.image_managed_dict.keys():
                continue
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_to_grab)
            for i in range(30): # Read ahead of the ask
                ret, frame = cap.read()
                if ret:
                    self.image_managed_dict[frame_to_grab+i] = frame

            if len(self.image_managed_dict.keys()) > MAXFRAMEBUFFER: # Clear memory of earlier frames
                keys = sorted(self.image_managed_dict.keys())
                for key in keys[:MAXFRAMEBUFFER//2]:
                    del self.image_managed_dict[key]
                gc.collect()

        cap.release()


    def __getitem__(self, key):
        if key > self.last_frame.value:
            return None
        try:
            frame = self.image_managed_dict[key]
            return frame
        except KeyError:
            self.to_grab_queue.put(key)
            time.sleep(0.01)
            return self.__getitem__(key)
            

    def __len__(self):
        return self.last_frame.value