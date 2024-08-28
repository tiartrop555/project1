# player.py
import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFileDialog
from datetime import timedelta
from ui import VideoPlayerUI

class VideoPlayer(VideoPlayerUI):
    def __init__(self):
        super().__init__()
        self.vid = None
        self.timer = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.tracker = None
        self.roi = None
        self.tracking = False

        # Connect buttons
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.reset_button.clicked.connect(self.reset)
        self.clear_button.clicked.connect(self.clear_trace)
        self.progress_slider.sliderMoved.connect(self.on_progress_move)

        # Open file dialog when the window is shown
        self.showEvent = self.open_file_dialog

    def open_file_dialog(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        if file_path:
            self.open_file(file_path)
        super().showEvent(event)

    def open_file(self, file_path):
        if self.vid:
            self.vid.release()
        self.vid = cv2.VideoCapture(file_path)
        self.current_frame = 0
        self.total_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        self.total_duration = timedelta(seconds=int(self.total_frames / self.fps))
        self.progress_slider.setMaximum(self.total_frames)
        if self.timer:
            self.timer.stop()
        self.timer = self.startTimer(int(1000 / self.fps))

    def timerEvent(self, event):
        self.update_frame()

    def update_frame(self):
        if self.vid and self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                if self.tracker and self.tracking:
                    success, bbox = self.tracker.update(frame)
                    if success:
                        p1 = (int(bbox[0]), int(bbox[1]))
                        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                        zoomed_frame = frame[p1[1]:p2[1], p1[0]:p2[0]]
                        zoomed_image = self.convert_to_qimage(zoomed_frame)
                        self.show_zoomed_image(zoomed_image)
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = self.convert_to_qimage(frame)
                self.video_label.setPixmap(QPixmap.fromImage(image))

                self.current_frame = int(self.vid.get(cv2.CAP_PROP_POS_FRAMES))
                self.progress_slider.setValue(self.current_frame)
                current_time = timedelta(seconds=int(self.current_frame / self.fps))
                time_str = f"{str(current_time)[:7]} / {str(self.total_duration)[:7]}"
                self.time_label.setText(time_str)

    def convert_to_qimage(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return q_image

    def show_zoomed_image(self, image):
        if not hasattr(self, 'zoom_window'):
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            self.zoom_window = QDialog()
            self.zoom_window.setWindowTitle("Zoomed View")
            self.zoom_layout = QVBoxLayout(self.zoom_window)
            self.zoom_label = QLabel()
            self.zoom_layout.addWidget(self.zoom_label)
            self.zoom_window.show()
        self.zoom_label.setPixmap(QPixmap.fromImage(image))

    def play_video(self):
        if self.vid:
            if not self.timer:
                self.timer = self.startTimer(int(1000 / self.fps))

    def pause_video(self):
        if self.timer:
            self.killTimer(self.timer)
            self.timer = None

    def reset(self):
        self.pause_video()
        if self.vid:
            self.vid.release()
        self.video_label.clear()
        self.progress_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")

    def clear_trace(self):
        self.pause_video()
        self.tracker = None
        self.roi = None
        self.tracking = False

    def on_progress_move(self):
        if self.vid:
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.progress_slider.value())
