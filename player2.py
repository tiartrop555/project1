# player.py
import cv2  # 視頻處理和數據處理
import numpy as np  # 視頻處理和數據處理
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QImage, QPixmap  # 圖像處理和顯示
from PyQt5.QtWidgets import QFileDialog  # 顯示文件對話框
from datetime import timedelta  # 時間計算
from ui import VideoPlayerUI  # 自定義的 GUI 類，視頻播放器的界面

# 定義了 VideoPlayer 類，它繼承自 VideoPlayerUI
class VideoPlayer(VideoPlayerUI):
    def __init__(self):
        super().__init__()  # 調用父類的初始化方法
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.showMaximized()  # 確保在窗口顯示時它是最大化的
        self.setFixedSize(self.size())
        self.vid = None  # 存儲視頻捕獲對象
        self.timer = None  # 定時更新視頻幀
        self.current_frame = 0  # 記錄當前視頻幀
        self.total_frames = 0  # 記錄視頻的總幀數
        self.fps = 0  # 記錄視頻的幀率（每秒幀數）
        self.tracker = None  # 跟踪對象
        self.roi = None  # 記錄感興趣區域（Region of Interest, ROI）
        self.tracking = False  # 標識是否正在跟踪對象

        # 連接控件事件
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.reset_button.clicked.connect(self.reset)
        self.clear_button.clicked.connect(self.clear_trace)
        self.progress_slider.sliderMoved.connect(self.on_progress_move)
        self.open_file_button.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        if file_path:
            self.open_file(file_path)

    # 打開一個新視頻文件並進行初始化，根據視頻文件設置幀數、FPS、總時長等參數，並設置進度條的範圍，最後啟動一個計時器來控制視頻的播放
    def open_file(self, file_path):
        self.pause_video()
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
        # 根據 FPS 計算計時器的間隔時間，並啟動一個新的計時器 (每一幀需要多少毫秒來顯示)
        self.timer = self.startTimer(int(1000 / self.fps))

    # 當計時器事件觸發時，方法會被調用會呼叫 update_frame 方法來更新視頻幀的顯示
    def timerEvent(self, event):
        self.update_frame()

    # 更新視頻播放中的每一幀並進行相關處理 (從視頻流中讀取幀數，進行跟蹤、顯示處理，並更新進度條和時間顯示)
    def update_frame(self):
        # 檢查視頻文件是否已經打開並且可以進行讀取
        if self.vid and self.vid.isOpened():
            # 使用 read() 方法從視頻中讀取下一幀。ret 是一個布林值，表示讀取是否成功。frame 是讀取到的幀數據（圖像）
            ret, frame = self.vid.read()
            # 檢查幀讀取是否成功
            if ret:
                # 檢查是否有啟動目標跟蹤（tracker）並且跟蹤狀態（tracking）為真
                if self.tracker and self.tracking:
                    self.process_tracking(frame)
                
                # 將幀從 BGR 色彩空間轉換為 RGB 色彩空間
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 將 RGB 幀轉換為 PyQt5 的 QImage 對象
                image = self.convert_to_qimage(frame)
                # 等比例縮放 QPixmap，以適應 video_label 的大小
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.video_label.setPixmap(scaled_pixmap)
                self.update_ui()

    def process_tracking(self, frame):
        success, bbox = self.tracker.update(frame)
        if success:
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
            zoomed_frame = frame[p1[1]:p2[1], p1[0]:p2[0]]
            zoomed_image = self.convert_to_qimage(zoomed_frame)
            self.show_zoomed_image(zoomed_image)

    def update_ui(self):
        self.current_frame = int(self.vid.get(cv2.CAP_PROP_POS_FRAMES))
        self.progress_slider.setValue(self.current_frame)
        current_time = timedelta(seconds=int(self.current_frame / self.fps))
        time_str = f"{str(current_time)[:7]} / {str(self.total_duration)[:7]}"
        self.time_label.setText(time_str)

    
    #　將 OpenCV 的影像幀轉換為 PyQt5 的 QImage，以便在 PyQt5 的 GUI 中顯示
    def convert_to_qimage(self, frame):
        # 從影像幀中獲取其高度（height）、寬度（width）以及色彩通道數量（channel）
        height, width, channel = frame.shape
        # 計算每行像素佔用的位元組數（這裡每個像素佔用 3 個位元組，對應於 RGB 三個色彩通道）
        bytes_per_line = 3 * width
        # 將 OpenCV 的影像幀轉換為 PyQt5 的 QImage 對象
        # 影像幀的原始資料，影像的寬度，影像的高度，每行的位元組數，指定 QImage 的格式
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        #返回轉換後的 QImage 對象，這個對象可以直接用於在 PyQt5 的介面中顯示
        return q_image

    # 用來在一個單獨的視窗中顯示放大的影像
    def show_zoomed_image(self, image):
        # 檢查 self 是否已有屬性 zoom_window
        if not hasattr(self, 'zoom_window'):
            # 引入 QDialog 和 QVBoxLayout，這些是 PyQt5 中用來創建對話框和設置垂直布局的組件
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
            # 創建一個新的 QDialog 對象 zoom_window，這將是用來顯示放大影像的視窗
            self.zoom_window = QDialog()
            # 設置 zoom_window 的標題為 "Zoomed View"
            self.zoom_window.setWindowTitle("Zoomed View")
            # 創建一個垂直布局 zoom_layout 並將其應用到 zoom_window 中
            self.zoom_layout = QVBoxLayout(self.zoom_window)
            # 創建一個新的 QLabel 對象 zoom_label，用來顯示放大的影像
            self.zoom_label = QLabel()
            # 將 zoom_label 添加到 zoom_layout 中，這樣它就會在 zoom_window 視窗內部顯示
            self.zoom_layout.addWidget(self.zoom_label)
            # 顯示 zoom_window 視窗
            self.zoom_window.show()
        # 使用 setPixmap 方法將轉換成 QPixmap 的 image 設置為 zoom_label 的內容，在放大視窗中顯示該影像
        self.zoom_label.setPixmap(QPixmap.fromImage(image))

    # 控制影片的播放
    def play_video(self):
        if self.vid:
            # 檢查是否計時器（self.timer）尚未啟動
            if not self.timer:
                # 計算每幀之間的時間間隔並啟動計時器
                self.timer = self.startTimer(int(1000 / self.fps))

    # 暫停影片的播放
    def pause_video(self):
        if self.timer:
            # 銷毀已啟動的計時器。killTimer 方法會根據計時器的 ID（即 self.timer）來停止該計時器
            # (停止影片幀的更新，從而暫停影片的播放)
            self.killTimer(self.timer)
            # 將 self.timer 設置為 None，表示計時器已經停止且無效
            self.timer = None

    # 重置影片播放器的狀態，使其恢復到初始狀態
    def reset(self):
        # 暫停影片播放
        self.pause_video()
        if self.vid:
            # 釋放影片資源，關閉與影片相關的文件或設備，並釋放內存
            self.vid.release()
        # 清除影片顯示區域（video_label）的內容，使其變為空白
        self.video_label.clear()
        # 將進度條（progress_slider）的值設置為 0
        self.progress_slider.setValue(0)
        # 將時間標籤（time_label）的文本設置為 "00:00 / 00:00"
        self.time_label.setText("00:00 / 00:00")

    # 重置與目標追蹤（tracking）相關的狀態和數據
    def clear_trace(self):
        # 暫停影片播放
        self.pause_video()
        # 將 self.tracker 設置為 None，表示取消當前的目標追蹤器
        # (清除先前設置的追蹤器，防止它繼續嘗試在影片中追蹤目標)
        self.tracker = None
        # 將 self.roi 設置為 None，表示清除當前的感興趣區域（Region of Interest）
        self.roi = None
        # 將 self.tracking 設置為 False，表示關閉目標追蹤功能
        self.tracking = False

    # 在用戶拖動進度條時被調用，用來更新影片的播放位置
    def on_progress_move(self):
        if self.vid:
            # OpenCV 提供的 cv2.VideoCapture.set 方法來設置影片當前幀的位置。cv2.CAP_PROP_POS_FRAMES 是一個標誌，表示要設置的屬性是影片的幀位置
            # 取得進度條當前的位置（值），表示用戶在進度條上選擇的新幀位置，通常是幀數，因此會直接傳給 cv2.set 方法來更新影片的播放位置
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.progress_slider.value())
