import json
import time
import subprocess
import numpy as np
from threading import Timer

class VideoBuffer(object):
    """
    Buffer a stream using ffmpeg, yielding every nth frame.
    """
    def start(self, stream, fps):
        self._fps = fps
        self._frame = None
        self._running = True
        self._create_pipe(stream)

    def _create_pipe(self, stream):
        probe_pipe = subprocess.Popen([
            "ffprobe", stream.url,
                       "-v", "error",
                       "-show_entries", "stream=width,height",
                       "-of", "json"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)
        video_info = probe_pipe.stdout.read().decode("utf8")
        video_info = json.loads(video_info)["streams"]
        video_info = next(
            data for data in video_info
            if len(data.keys()) > 0
        )
        probe_pipe.terminate()

        self._byte_length = video_info["width"]
        self._byte_width  = video_info["height"]

        self._pipe = subprocess.Popen([
            "ffmpeg", "-i", stream.url,
                      "-loglevel", "quiet", # no text output
                      "-an", # disable audio
                      "-f", "image2pipe",
                      "-framerate", str(self._fps),
                      "-pix_fmt", "bgr24",
                      "-vcodec", "rawvideo", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)

        self._frame = self._read_frame()

    def stop(self):
        self._pipe.terminate()
        self._running = False

    def _read_frame(self):
        if not self._running:
            return

        self._timer = Timer(1.0/self._fps, self._read_frame)
        self._timer.daemon = True
        self._timer.start()

        raw_image = self._pipe.stdout.read(
            self._byte_length * self._byte_width * 3)
        self._frame = np.fromstring(raw_image, dtype="uint8")\
            .reshape((self._byte_width, self._byte_length, 3))

    def read(self):
        return self._frame