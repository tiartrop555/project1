# ui.py
from PyQt5.QtWidgets import QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt

class VideoPlayerUI(QWidget):
    def __init__(self):
        super().__init__()
        
        # Layouts
        self.main_layout = QVBoxLayout(self)
        self.controls_layout = QHBoxLayout()

        # Create widgets
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.video_label)

        self.controls_frame = QWidget()
        self.controls_frame.setLayout(self.controls_layout)
        self.main_layout.addWidget(self.controls_frame)

        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.clear_button = QPushButton("Clear")

        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.reset_button)
        self.controls_layout.addWidget(self.clear_button)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.controls_layout.addWidget(self.progress_slider)

        self.time_label = QLabel("00:00 / 00:00")
        self.controls_layout.addWidget(self.time_label)
