# player.py
import cv2  # 視頻處理和數據處理
import numpy as np  # 視頻處理和數據處理
from PyQt5.QtCore import Qt, QEvent, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter  # 圖像處理和顯示
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

        self.zoom_window.setGeometry(QRect(100, 100, 640, 480))
        self.zoom_window.setWindowFlags(Qt.Window)  # Ensure the window has minimize, maximize, and close buttons
        self.zoom_window.closeEvent = self.closeEvent  # 改寫放大視窗的關閉事件，讓它可以做到clear_trace（）
        self.zoom_window.hide()

        # 圈選的起始點和結束點
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.scaled_pixmap = None

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
        self.tracker = None
        self.roi = None
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
                # 先將 QImage 轉換為 QPixmap
                pixmap = QPixmap.fromImage(image)

                # 等比例縮放 QPixmap，以適應 video_label 的大小
                self.scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # 將縮放後的圖像設置為 video_label 的顯示內容，使圖像顯示在界面上
                self.video_label.setPixmap(self.scaled_pixmap)
  
                # 更新進度條和時間標籤
                self.update_ui()

    def process_tracking(self, frame):
        success, bbox = self.tracker.update(frame)
        if success:
            p1 = (int(bbox[0]), int(bbox[1]))
            p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
            zoomed_frame = frame[p1[1]:p2[1], p1[0]:p2[0]]
            zoomed_frame = cv2.cvtColor(zoomed_frame, cv2.COLOR_BGR2RGB)
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
        width = image.width()
        height = image.height()
        self.zoom_label.resize(self.widget.size())
        ratio = min(self.zoom_label.width() / width, self.zoom_label.height() / height)
        new_image = image.scaled(int(width * ratio), int(height * ratio), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.zoom_label.setPixmap(QPixmap.fromImage(new_image))  # 将传入的 image 图像设置为 zoom_label 中显示的内容。 

    # 控制影片的播放
    def play_video(self):
        if self.vid and not self.vid.isOpened():  # 检查 self.vid 是否存在并有效。 如果视频文件未成功打开，后续操作（如启动定时器播放视频）将没有意义。
            self.vid = cv2.VideoCapture(self.video_source)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        if self.roi and self.roi[2] and self.roi[3]:
            self.tracker = cv2.TrackerCSRT_create()
            ret, frame = self.vid.read()
            if ret:
                print(f"ROI: x={self.roi[0]}, y={self.roi[1]}, width={self.roi[2]}, height={self.roi[3]}")
                print(f"Image size: width={frame.shape[1]}, height={frame.shape[0]}")
                if len(frame.shape) == 2 or frame.shape[2] == 1:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                window_size = self.size()
                width = window_size.width()
                height = window_size.height()
                scale_width = frame.shape[1] / width
                scale_height = frame.shape[0] / height
                x = int(self.roi[0] * (scale_width))
                y = int(self.roi[1] * (scale_height))
                w = int(self.roi[2] * (scale_width))
                h = int(self.roi[3] * (scale_height))
                new_roi = (x,y,w,h)

                self.tracker.init(frame, new_roi)
                self.zoom_window.show()
        self.rect = None
        
        if self.vid and self.vid.isOpened() and not self.timer:  # 当前是否没有正在运行的定时器，防止重复启动定时器
            self.timer = self.startTimer(int(1000 / self.fps))  #  启动一个定时器来控制视频帧的播放，并将定时器的 ID 保存到 self.timer

    # 暫停影片的播放
    def pause_video(self):
        if self.timer:
            # 銷毀已啟動的計時器。killTimer 方法會根據計時器的 ID（即 self.timer）來停止該計時器
            # (停止影片幀的更新，從而暫停影片的播放)
            self.killTimer(self.timer)
            # 將 self.timer 設置為 None，表示計時器已經停止且無效
            self.timer = None
        self.tracking = False
        self.start_x = None
        self.start_y = None
        self.rect = None

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
        self.zoom_label.clear()
        self.zoom_window.hide()
        self.vid = None
        self.video_source = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.delay = 0
        self.total_duration = timedelta(0)
        self.tracker = None
        self.rect = None
        self.roi = None
        self.tracking = False

    # 重置與目標追蹤（tracking）相關的狀態和數據
    def clear_trace(self):
        # 暫停影片播放
        # 將 self.tracker 設置為 None，表示取消當前的目標追蹤器
        # (清除先前設置的追蹤器，防止它繼續嘗試在影片中追蹤目標)
        self.tracker = None
        # 將 self.roi 設置為 None，表示清除當前的感興趣區域（Region of Interest）
        self.roi = None
        # 將 self.tracking 設置為 False，表示關閉目標追蹤功能
        self.tracking = False
        self.zoom_window.hide()
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.update_frame()

    # 覆寫 closeEvent 方法
    def closeEvent(self, event):
        self.clear_trace()  # 在窗口關閉時調用 reset() 方法
        event.accept()  # 接受關閉事件

    # 在用戶拖動進度條時被調用，用來更新影片的播放位置
    def on_progress_move(self):
        if self.vid:
            # OpenCV 提供的 cv2.VideoCapture.set 方法來設置影片當前幀的位置。cv2.CAP_PROP_POS_FRAMES 是一個標誌，表示要設置的屬性是影片的幀位置
            # 取得進度條當前的位置（值），表示用戶在進度條上選擇的新幀位置，通常是幀數，因此會直接傳給 cv2.set 方法來更新影片的播放位置
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.progress_slider.value())

    # 框選區域
    def mousePressEvent(self, event):
        self.pause_video()
        if event.button() == Qt.LeftButton:
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseMoveEvent(self, event):
        if self.start_x is not None and self.start_y is not None:
            end_x = event.x()
            end_y = event.y()
            self.rect = QRect(min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_x is not None and self.start_y is not None:
            end_x = event.x()
            end_y = event.y()
            if self.start_x != end_x and self.start_y != end_y:
                self.rect = QRect(min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))
                self.roi = (min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))
                self.tracking = True

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rect:
            paint_frame = self.scaled_pixmap.copy()
            painter = QPainter(paint_frame)
            painter.setPen(Qt.red)
            painter.drawRect(self.rect)
            painter.end()
            self.video_label.setPixmap(paint_frame)
