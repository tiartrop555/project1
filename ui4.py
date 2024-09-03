from PyQt5.QtWidgets import QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt

class VideoPlayerUI(QWidget):
    def __init__(self):
        super().__init__()

        # 主垂直佈局
        self.main_layout = QVBoxLayout(self)
        # 創建一個水平佈局來管理控制按鈕和滑動條
        self.controls_layout = QHBoxLayout()

        # 創建用於顯示視頻的 QLabel
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        # 設置 video_label 的背景色為黑色
        self.video_label.setStyleSheet("background-color: black;")
        # 設置 sizePolicy 使 QLabel 能夠擴展填充剩餘空間
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.video_label)
        
        # 創建控制按鈕和滑動條
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.clear_button = QPushButton("Clear")
        self.open_file_button = QPushButton("Open File")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00 / 00:00")

        # 將控件添加到控制佈局中
        self.controls_layout.addWidget(self.open_file_button)
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.reset_button)
        self.controls_layout.addWidget(self.clear_button)
        self.controls_layout.addWidget(self.progress_slider)
        self.controls_layout.addWidget(self.time_label)

        # 創建控制佈局的容器
        self.controls_frame = QWidget()
        # 將所有在 controls_layout 中排好的控件（比如播放按鈕、進度條等），統一放到 controls_frame 這個容器
        # controls_frame 就會根據 controls_layout 的規則來安排這些控件的位置和大小
        self.controls_frame.setLayout(self.controls_layout)

        # 將控制佈局 controls_frame 添加到主佈局中
        self.main_layout.addWidget(self.controls_frame)
        
        # 將控制佈局對齊底部
        self.controls_layout.setAlignment(Qt.AlignBottom)

        # 調整邊距
        # 設置 main_layout 內部內容與視窗邊緣之間的邊距 (margins)，setContentsMargins 設定佈局內容與左、上、右、下邊界之間的距離
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        # 設置 main_layout 內部元素（video_label 和 controls_frame）之間的間距 (spacing)
        self.main_layout.setSpacing(0)

        # 創建放大視窗
        self.zoom_window = QWidget(self)
        self.zoom_window.setWindowTitle("Zoomed View")
        self.widget = QWidget(self.zoom_window)
        self.zoom_label = QLabel(self.widget)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_window_layout = QVBoxLayout(self.zoom_window)
        self.zoom_window_layout.addWidget(self.widget)