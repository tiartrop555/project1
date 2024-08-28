import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QSlider, QWidget, QFileDialog, QFrame, QDialog
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter
from datetime import timedelta

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt OpenCV Video Player")
        self.setGeometry(100, 100, 800, 600)

        # 創建主窗口小部件
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # 創建佈局
        self.layout = QVBoxLayout(self.central_widget)

        # 創建拖放區域
        self.drop_label = QLabel("拖放影片檔案到這裡，或點擊以選擇檔案", self)
        self.drop_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("background-color: lightgray;")
        self.drop_label.setAcceptDrops(True)
        self.drop_label.mousePressEvent = self.on_file_click
        self.layout.addWidget(self.drop_label)

        # 創建主畫布來顯示影片
        self.video_label = QLabel(self)
        self.layout.addWidget(self.video_label)

        # 創建控制面板
        self.control_layout = QVBoxLayout()
        self.layout.addLayout(self.control_layout)

        # 按鈕
        self.play_button = QPushButton("Play", self)
        self.play_button.clicked.connect(self.play_video)
        self.control_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("Pause", self)
        self.pause_button.clicked.connect(self.pause_video)
        self.control_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.reset)
        self.control_layout.addWidget(self.reset_button)

        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_trace)
        self.control_layout.addWidget(self.clear_button)

        # 進度條
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.sliderMoved.connect(self.on_progress_move)
        self.control_layout.addWidget(self.progress_slider)

        # 顯示時間的標籤
        self.time_label = QLabel("00:00 / 00:00", self)
        self.layout.addWidget(self.time_label)

        # 創建放大視窗
        self.zoom_window = QDialog(self)
        self.zoom_window.setWindowTitle("Zoomed View")
        self.zoom_label = QLabel(self.zoom_window)
        self.zoom_window.setGeometry(QRect(100, 100, 640, 480))
        self.zoom_layout = QVBoxLayout(self.zoom_window)
        self.zoom_layout.addWidget(self.zoom_label)
        self.zoom_window.hide()

        # 圈選的起始點和結束點
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.tracking = False

        # 影片屬性
        self.vid = None
        self.video_source = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.delay = 0
        self.total_duration = timedelta(0)
        self.tracker = None
        self.roi = None

        # 計時器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    # 檔案拖放功能
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.load_video(file_path)

    # 檔案選擇功能
    def on_file_click(self, event):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇影片檔案", "", "Video files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        if file_path:
            self.load_video(file_path)

    # 影片載入
    def load_video(self, video_source):
        if self.vid:
            self.vid.release()
        self.video_source = video_source
        self.vid = cv2.VideoCapture(self.video_source)
        self.current_frame = 0
        self.total_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        self.delay = int(1000 / self.fps)
        self.total_duration = timedelta(seconds=int(self.total_frames / self.fps))
        self.tracker = None
        self.roi = None
        self.timer.start(self.delay)

    # 每一幀更新
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
                        zoomed_frame = self.resize_frame_to_label(zoomed_frame, self.zoom_label.width(), self.zoom_label.height())
                        self.display_image(zoomed_frame, self.zoom_label)

                frame = self.resize_frame_to_label(frame, self.video_label.width(), self.video_label.height())
                self.display_image(frame, self.video_label)

                self.current_frame = int(self.vid.get(cv2.CAP_PROP_POS_FRAMES))
                progress_value = (int)(self.current_frame / self.total_frames) * 100
                self.progress_slider.setValue(progress_value)
                current_time = timedelta(seconds=int(self.current_frame / self.fps))
                time_str = f"{str(current_time)[:7]} / {str(self.total_duration)[:7]}"
                self.time_label.setText(time_str)

    # 影片播放功能
    def play_video(self):
        if self.vid and not self.vid.isOpened():
            self.vid = cv2.VideoCapture(self.video_source)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        if self.roi and self.roi[2] and self.roi[3]:
            self.tracker = cv2.TrackerCSRT_create()
            ret, frame = self.vid.read()
            if ret:
                self.tracker.init(frame, self.roi)
                self.zoom_window.show()
        self.tracking = True
        self.timer.start(self.delay)

    # 暫停影片
    def pause_video(self):
        self.timer.stop()
        self.tracking = False
        self.start_x = None
        self.start_y = None
        self.rect = None

    # 重置功能
    def reset(self):
        self.timer.stop()
        if self.vid:
            self.vid.release()
        self.video_label.clear()
        self.zoom_label.clear()
        self.progress_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")
        self.drop_label.show()
        self.video_label.hide()
        self.zoom_window.hide()
        self.vid = None
        self.video_source = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.delay = 0
        self.total_duration = timedelta(0)
        self.tracker = None
        self.roi = None
        self.tracking = False

    # 清除追蹤功能
    def clear_trace(self):
        self.zoom_window.hide()
        self.tracker = None
        self.roi = None
        self.tracking = False
        self.start_x = None
        self.start_y = None
        self.rect = None

    # 進度條移動
    def on_progress_move(self, position):
        if self.vid:
            self.timer.stop()
            self.current_frame = int((position / 100) * self.total_frames)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.update_frame()

    # 框選區域
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_x is not None and self.start_y is not None:
            end_x = event.x()
            end_y = event.y()
            if self.start_x != end_x and self.start_y != end_y:
                self.rect = QRect(self.start_x, self.start_y, end_x - self.start_x, end_y - self.start_y)
                self.roi = (self.start_x, self.start_y, end_x - self.start_x, end_y - self.start_y)

    def mouseMoveEvent(self, event):
        if self.start_x is not None and self.start_y is not None:
            self.rect = QRect(self.start_x, self.start_y, event.x() - self.start_x, event.y() - self.start_y)
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rect:
            painter = QPainter(self)
            painter.setPen(Qt.red)
            painter.drawRect(self.rect)

    # 顯示圖像
    def display_image(self, frame, label):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(q_image))

    # 調整圖像大小以適應標籤
    def resize_frame_to_label(self, frame, label_width, label_height):
        height, width = frame.shape[:2]
        ratio = min(label_width / width, label_height / height)
        return cv2.resize(frame, (int(width * ratio), int(height * ratio)))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
