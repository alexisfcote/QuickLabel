from multiprocessing import Process, Manager, Event, cpu_count
import os
import logging

FASTAI = False
BATCH_SIZE = 24
SKIP = 1
try:
    from fastai.vision import load_learner, PIL, Path, pil2tensor, np, Image
    import torch
    FASTAI = True
except NameError:
    logging.warning('Fastai not installed')


class PredictProcess(Process):
    def __init__(self, model_path, video_path, image_reader_process):
        super().__init__()
        self.model_path = model_path
        self.video_path = video_path
        self.learn = None
        self.running = False
        self.managed_dict = Manager().dict()
        self.image_reader_process = image_reader_process
        self.stop_event = Event()
    
    def prepare_model(self):
        try:
            self.learn = load_learner(*os.path.split(self.model_path))
            torch.set_num_threads(int(max(1, np.floor(0.8*cpu_count()))))
        except FileNotFoundError:
            logging.warning('DL model not found')
            return False
        logging.debug('DL model loaded')  
        return True

    def run(self):
        self.prepare_model()
        frame_number = 0
        finished = False
        while not self.stop_event.is_set() and not finished:
            im_batch = []
            im_batch_frame_number = []
            for _ in range(0, BATCH_SIZE):
                frame = self.image_reader_process[frame_number]
                if frame is not None:
                    im_batch_frame_number.append(frame_number)
                    im_batch.append(frame)
                else:
                    finished = True
                    logging.debug("finished DL process")
                frame_number += SKIP

            if len(im_batch):
                labels, probs = self.predict_batch(im_batch)

            for frame_n, label, prob in zip(im_batch_frame_number, labels, probs):
                self.managed_dict[frame_n] = (label, prob)
            logging.debug("processed image {}".format(frame_number))
        logging.debug("Quitting DL process")
            

    def predict(self, frame):
        """
        Use loaded learner to predict the frame class
        returns (pred_label, prob_dict)
        """
        im = self.prepare_image(frame)
        pred = self.learn.predict(im)
        pred_label = pred[0].obj
        pred_proba = dict(zip(self.learn.data.classes, pred[2].numpy()))
        return pred_label, pred_proba

    def prepare_image(self, frame):
        """
        Transform a cv2 frame to fastai image
        """
        x = PIL.Image.fromarray(frame[:,:,::-1])
        x = pil2tensor(x,np.float32).div_(255)
        return Image(x)


    def predict_batch(self, framelist):
        """
        Use loaded learner to predict the frame class of a batch of images
        returns (pred_label, prob_dict)
        """
        imlist = [self.prepare_image(frame) for frame in framelist]
        with torch.no_grad():
            imlist = [self.learn.data.one_item(im)[0].cpu() for im in imlist]
            probs = torch.softmax(self.learn.model.cpu().eval()(torch.cat(imlist)),1).numpy()
            labels = [self.learn.data.classes[x] for x in np.argmax(probs, axis=1)]
            probs = [dict(zip(self.learn.data.classes, prob)) for prob in probs]
        return labels, probs


    