import cv2
import numpy as np
from attr import evolve

from pipe.pipe import Pipe

class DevicePipe(Pipe):
    """
    Detect the embedded game screen inside the frame.
    """
    decay = 0.001

    def __init__(self):
        pass

    def start(self):
        self._movement_map = None
        self._last_frame = None

    def process(self, frame, state):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self._last_frame is None:
            self._movement_map = np.zeros(gray_frame.shape,
                                          np.float)
            self._last_frame = gray_frame
            return {}

        diff = cv2.absdiff(gray_frame, self._last_frame)
        if diff.sum() == 0:
            return {}

        # 0 for same pixels, 255 for changed pixels
        mask = cv2.threshold(diff, 1, 255, cv2.THRESH_BINARY)[1]

        # slow decay
        cv2.accumulateWeighted(mask, self._movement_map, self.decay)

        # convert frame of floats to 1 channel gray
        movement_frame = cv2.convertScaleAbs(
            self._movement_map,
            alpha=255.0/self._movement_map.max())

        # smoothen for better contour performance
        movement_frame = cv2.blur(
            movement_frame, (int(gray_frame.shape[0]/10),
                             int(gray_frame.shape[1]/10)))

        movement_frame = cv2.threshold(
            movement_frame,
            0, 255,
            cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # TODO try edge detection
        contours = cv2.findContours(
            movement_frame,
            cv2.RETR_EXTERNAL, # only match parent contours
            cv2.CHAIN_APPROX_SIMPLE)[1]

        rects = [cv2.boundingRect(contour) for contour in contours]
        # find largest area
        x1, y1, w, h = sorted(rects,
                      key=lambda rect: rect[2]*rect[3],
                      reverse=True)[0]

        self._last_frame = gray_frame
        stream_config = evolve(state.stream_config,
                               screen_box=((x1, y1),
                                           (x1+w, y1+h)))

        return {
            "stream_config": stream_config
        }