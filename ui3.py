# ui.py
from PyQt5.QtWidgets import QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QWidget  ###
from PyQt5.QtCore import Qt


class VideoPlayerUI(QWidget):  # 定義了一個名為 VideoPlayerUI 的類，繼承自 QWidget，這意味著它是一個窗口部件。
    def __init__(self):  # 這是類的構造函數，當創建 VideoPlayerUI 的實例時會自動調用。
        super().__init__()  # 調用父類 QWidget 的構造函數來初始化基類，這是必要的步驟，以確保 QWidget 的內部機制正確運行。
        
        # Layouts 創建佈局
        self.main_layout = QVBoxLayout(self)  # 創建一個垂直佈局（QVBoxLayout），這個佈局用來管理窗口內部控件的排列。self 是當前視窗的實例，這個佈局會應用到這個視窗。
        self.controls_layout = QHBoxLayout()  # 創建一個水平佈局（QHBoxLayout），用來管理播放控制按鈕和其他控件的排列。

        # Create widgets 創建並添加控件
        self.video_label = QLabel()  # 創建一個 QLabel 控件，用來顯示視頻畫面。初始狀態下它是空白的，會在後續顯示視頻內容。
        self.video_label.setAlignment(Qt.AlignCenter)  # 設置 QLabel 的對齊方式為居中（Qt.AlignCenter），確保視頻畫面在視窗中居中顯示。
        self.main_layout.addWidget(self.video_label)  # 將 video_label 添加到主佈局 main_layout 中。這表示視頻顯示區域將在視窗的頂部顯示。

        # 創建底部控件排列方法
        self.controls_frame = QWidget()  # 創建一個 QWidget 作為容器，來包含控制按鈕和進度條。
        self.controls_frame.setLayout(self.controls_layout)  # 將之前創建的 controls_layout（水平佈局）設置為這個容器的佈局。
        self.main_layout.addWidget(self.controls_frame)  # 將 controls_frame 添加到主佈局 main_layout，放置在視頻顯示區域的下方。

        # 創建按鈕
        self.play_button = QPushButton("Play")  # 創建一個名為 "Play" 的按鈕，用於播放視頻。
        self.pause_button = QPushButton("Pause")  # 創建一個名為 "Pause" 的按鈕，用於暫停視頻。
        self.reset_button = QPushButton("Reset")  # 創建一個名為 "Reset" 的按鈕，用於重置視頻。
        self.clear_button = QPushButton("Clear")  # 創建一個名為 "Clear" 的按鈕，用於清除視頻內容。

        # 將這些按鈕按順序添加到 controls_layout 中，按鈕會水平排列在控制區域
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.reset_button)
        self.controls_layout.addWidget(self.clear_button)

        # 創建進度條和時間標籤
        self.progress_slider = QSlider(Qt.Horizontal)  # 創建一個水平的滑塊（進度條），用來顯示和調整視頻的播放進度。
        self.controls_layout.addWidget(self.progress_slider)  # 將滑塊添加到 controls_layout，它將位於按鈕的右側。

        self.time_label = QLabel("00:00 / 00:00")  # 創建一個 QLabel 用於顯示當前播放時間和總時間。初始狀態下，顯示 "00:00 / 00:00"。
        self.controls_layout.addWidget(self.time_label)  # 將時間標籤添加到 controls_layout，它將位於滑塊的右側。

        # 創建放大視窗：用widget先創建一個視窗，設定為垂直佈局。再在視窗裏面創建一個widget對象叫self.widget。最後在self.widget裏面加入一個label對象，用於顯示放大圖像
        self.zoom_window = QWidget(self)
        self.zoom_window.setWindowTitle("Zoomed View")
        self.widget = QWidget(self.zoom_window)
        self.zoom_label = QLabel(self.widget)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_window_layout = QVBoxLayout(self.zoom_window)
        self.zoom_window_layout.addWidget(self.widget)