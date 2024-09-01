# player.py
import cv2  # cv2：OpenCV 庫，用於處理視頻和圖像操作。
import numpy as np  # np：NumPy 庫，用於數值計算和矩陣操作。
from PyQt5.QtGui import QImage, QPixmap, QPainter  # QImage 和 QPixmap：PyQt 的圖像類，用於將 OpenCV 的圖像轉換為 Qt 支持的格式，以便顯示在界面上。
from PyQt5.QtWidgets import QFileDialog  # QFileDialog 和 QLabel：PyQt 的組件，用於文件對話框和顯示文本或圖像。
from datetime import timedelta  # timedelta：從 datetime 模組中導入，用於計算和表示時間間隔。
from ui import VideoPlayerUI  # VideoPlayerUI：自定義的 UI 類，定義了播放器的界面。
from PyQt5.QtCore import Qt, QRect
# 定義 VideoPlayer 類，繼承自 VideoPlayerUI，這意味著它不僅擁有 UI 的所有屬性和方法，還可以添加新的屬性和功能。
class VideoPlayer(VideoPlayerUI): 
    def __init__(self):
        super().__init__()  # 調用 VideoPlayerUI 類的 __init__ 方法，確保父類的初始化邏輯被執行。
        self.vid = None  # self.vid：保存當前視頻文件的 OpenCV VideoCapture 對象。
        self.timer = None  # self.timer：保存 PyQt 的計時器 ID，用於控制視頻播放。
        self.current_frame = 0  # self.current_frame：當前播放到的幀數。
        self.total_frames = 0  # self.total_frames：視頻的總幀數。
        self.fps = 0  # self.fps：視頻的每秒幀數（frames per second）。
        self.tracker = None  # self.tracker：OpenCV 的目標追蹤器對象，用於跟踪選定的目標。
        self.roi = None  # self.roi：感興趣區域（region of interest）的邊界框。
        self.tracking = False  # self.tracking：布爾值，表示是否正在進行追蹤。

        self.zoom_window.setGeometry(QRect(100, 100, 640, 480))
        self.zoom_window.setWindowFlags(Qt.Window)  # Ensure the window has minimize, maximize, and close buttons
        self.zoom_window.closeEvent = self.closeEvent  # 改寫放大視窗的關閉事件，讓它可以做到reset（）
        self.zoom_window.hide()

        # 圈選的起始點和結束點
        self.start_x = None  #滑鼠按下的起始點
        self.start_y = None
        self.rect = None  # 滑鼠拉出的方框
        self.pixmap = None   # 當前要輸出的那一幀圖像
        self.pause_flag = False  # 用於控制在按下pause或clear之後，才能在圖像上進行框選

        # Connect buttons
        self.play_button.clicked.connect(self.play_video)  # 當點擊播放按鈕時，調用 play_video() 方法。
        self.pause_button.clicked.connect(self.pause_video)
        self.reset_button.clicked.connect(self.reset)
        self.clear_button.clicked.connect(self.clear_trace)
        self.progress_slider.sliderMoved.connect(self.on_progress_move)  # 當拖動進度條時，調用 on_progress_move() 方法來調整視頻播放位置。

        # 覆蓋 showEvent 事件處理函數，當窗口顯示時自動打開文件對話框，讓用戶選擇要播放的視頻文件。
        self.showEvent = self.open_file_dialog

    # 打開文件對話框
    def open_file_dialog(self, event):
        # 打開一個文件選擇對話框，讓用戶選擇視頻文件。支持多種視頻格式。
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv)")
        if file_path:  
            self.open_file(file_path) 
        super().showEvent(event)  

    # 打開並初始化視頻文件
    def open_file(self, file_path):
        if self.vid:
            self.vid.release()  # 如果 self.vid 已經被初始化並且指向一個有效的 VideoCapture 對象，這行代碼將釋放該對象，從而釋放系統資源。
        self.vid = cv2.VideoCapture(file_path)  # 使用 OpenCV 打開指定路徑的視頻文件。
        self.current_frame = 0  # 將當前幀數重置為 0，這表示從視頻的起始位置開始播放。
        self.total_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))  # 獲取視頻的總幀數。
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)  # 獲取視頻的幀率（fps）
        self.total_duration = timedelta(seconds=int(self.total_frames / self.fps))  # self.total_duration：計算並保存視頻的總時長。
        self.progress_slider.setMaximum(self.total_frames)  # 設置進度條的最大值為視頻總幀數，允許用戶在整個視頻範圍內拖動滑塊。
        self.tracker = None
        self.roi = None
        if self.timer:  # 如果計時器已存在並運行，則停止它。這樣可以避免在打開新視頻時，舊的計時器繼續影響新視頻的播放。
            self.timer.stop()
        self.timer = self.startTimer(int(1000 / self.fps))  # 啟動一個計時器，以 fps 為頻率定期觸發 timerEvent()，更新視頻畫面。
                                                            

    # 計時器事件
    def timerEvent(self, event):  
        self.update_frame()  # 當計時器觸發時，調用 update_frame() 方法來讀取並顯示視頻的下一幀。

    # 更新畫面並處理追蹤
    def update_frame(self):
        if self.vid and self.vid.isOpened():  # 是否已經打開了一個有效的視頻文件
            ret, frame = self.vid.read()  # 從視頻中讀取一幀。ret 是一個布爾值，表示讀取是否成功；frame 是讀取到的圖像幀。
            if ret:
                if self.tracker and self.tracking: # 如果追蹤器 (tracker) 已啟動並處於追蹤模式，則更新追蹤框 (bbox) 的位置，並在幀上繪製一個矩形框。
                    success, bbox = self.tracker.update(frame)  # 使用 OpenCV 的追蹤器更新當前幀中的目標位置。
                    if success:  # 如果追蹤成功，將追蹤框內的畫面裁剪出來作為放大視圖顯示在另一個窗口中。
                        p1 = (int(bbox[0]), int(bbox[1])) 
                        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)  # 使用 OpenCV 在當前幀上繪製一個藍色矩形框，標記出追蹤到的目標位置。
                        zoomed_frame = frame[p1[1]:p2[1], p1[0]:p2[0]]  # 將幀中的追蹤框內的區域裁剪出來，這部分畫面將作為放大視圖顯示在另一個窗口中。
                        zoomed_frame = cv2.cvtColor(zoomed_frame, cv2.COLOR_BGR2RGB)
                        zoomed_image = self.convert_to_qimage(zoomed_frame)  # 將裁剪出的追蹤框畫面（zoomed_frame）轉換為 PyQt 可顯示的 QImage 格式。
                        self.show_zoomed_image(zoomed_image)  # 在另一個窗口中顯示放大後的目標畫面。
                        
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 將 OpenCV 默認的 BGR 格式圖像轉換為 RGB 格式，以便在 PyQt 中顯示。
                image = self.convert_to_qimage(frame)  # 將 NumPy 陣列格式的圖像轉換為 PyQt 的 QImage
                self.pixmap = QPixmap.fromImage(image)
                self.video_label.setPixmap(self.pixmap)  # 在 video_label 上顯示轉換後的圖像。

                # 更新進度條和時間標籤
                self.current_frame = int(self.vid.get(cv2.CAP_PROP_POS_FRAMES))  # 獲取當前播放的幀號，更新 self.current_frame 變量。
                self.progress_slider.setValue(self.current_frame)  # 更新進度條的位置，使其與當前播放的幀號保持一致。
                current_time = timedelta(seconds=int(self.current_frame / self.fps))  # 計算當前幀對應的播放時間，並轉換為 timedelta 格式。
                time_str = f"{str(current_time)[:7]} / {str(self.total_duration)[:7]}"  # 格式化當前播放時間和總播放時間，顯示在播放器的時間標籤中。
                self.time_label.setText(time_str)  # 更新顯示時間的 QLabel，讓用戶看到當前播放時間和視頻的總時長。
    
    # 圖像格式轉換
    def convert_to_qimage(self, frame):
        height, width, channel = frame.shape  # 獲取圖像的高 (height)、寬 (width) 和通道數 (channel)
        bytes_per_line = 3 * width  # 這行代碼計算每一行圖像數據所佔的字節數 (bytes_per_line)。
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)  # frame.data: 圖像數據的指針或內存位置，這是 OpenCV 圖像陣列的原始數據。 
        return q_image

    # 顯示放大視圖
    def show_zoomed_image(self, image):
        # 取得圖像的寬高
        width = image.width()  
        height = image.height()
        self.zoom_label.resize(self.widget.size())  # 將label大小調整爲視窗内的widget大小
        ratio = min(self.zoom_label.width() / width, self.zoom_label.height() / height)
        new_image = image.scaled(int(width * ratio), int(height * ratio), Qt.KeepAspectRatio, Qt.SmoothTransformation)  # 將圖像大小調整為label的大小
        self.zoom_label.setPixmap(QPixmap.fromImage(new_image))  # 将传入的 image 图像设置为 zoom_label 中显示的内容。  
      
    # 檢查視頻是否已加載，並啟動計時器以繼續播放。
    def play_video(self):
        if self.vid and not self.vid.isOpened():  # 检查 self.vid 是否存在并有效。 
            self.vid = cv2.VideoCapture(self.video_source)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        if self.roi and self.roi[2] and self.roi[3]:
            self.tracker = cv2.TrackerCSRT_create()
            ret, frame = self.vid.read()
            if ret:
                self.tracker.init(frame, self.roi)
                self.zoom_window.show()
        self.tracking = True
        self.rect = None
        self.pause_flag = False
        
        if self.vid and self.vid.isOpened() and not self.timer:  # 当前是否没有正在运行的定时器，防止重复启动定时器
            self.timer = self.startTimer(int(1000 / self.fps))  #  启动一个定时器来控制视频帧的播放，并将定时器的 ID 保存到 self.timer   

    # 暫停視頻播放，通過停止計時器來實現。
    def pause_video(self):
        if self.timer:
            self.killTimer(self.timer)  # 停止当前的定时器。
            self.timer = None   # 将 self.timer 设置为 None，以表示定时器已被停止。
        self.tracking = False
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.pause_flag = True

    # 重置播放器狀態，釋放視頻資源，清除顯示的圖像，並重置進度條和時間標籤。
    def reset(self):
        self.pause_video()  # 确保在重置播放器时，视频的播放被暂停，从而避免播放状态干扰重置操作。
        if self.vid:
            self.vid.release()
        self.video_label.clear()  # 清除显示的视频帧
        self.progress_slider.setValue(0)  # 将进度条的值设置为 0。表示将视频的播放进度重置到开始位置。
        self.time_label.setText("00:00 / 00:00")  # 设置时间标签的文本为 "00:00 / 00:00"。视频时间被重置为起始状态。
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
        self.pause_flag = False

    # 暫停視頻並清除追蹤器和相關狀態。
    def clear_trace(self):
        self.tracker = None  # 清除当前的追踪器对象，即停止任何目标追踪
        self.roi = None  # 清除当前选定的感兴趣区域
        self.tracking = False  # 表示停止追踪，并标记追踪状态为未开始
        self.zoom_window.hide()
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.update_frame()
        self.pause_video()

    # 覆寫 closeEvent 方法
    def closeEvent(self, event):
        self.reset()  # 在窗口關閉時調用 reset() 方法
        event.accept()  # 接受關閉事件


    # 處理進度條拖動事件
    def on_progress_move(self):
        if self.vid:
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.progress_slider.value())  # 更新视频播放的位置，以匹配进度条的值。
    
    # 框選區域
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_x is not None and self.start_y is not None:
            end_x = event.x()
            end_y = event.y()
            if self.start_x != end_x and self.start_y != end_y and self.pause_flag:
                self.rect = QRect(min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))
                self.roi = (min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))

    def mouseMoveEvent(self, event):
        if self.start_x is not None and self.start_y is not None and self.pause_flag:
            end_x = event.x()
            end_y = event.y()
            self.rect = QRect(min(self.start_x, end_x), min(self.start_y, end_y), abs(end_x - self.start_x), abs(end_y - self.start_y))
            self.update()

    # 繪製滑鼠拖動顯示的紅框
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rect:
            paint_frame = self.pixmap.copy()  # 將當前圖像複製一份，防止改動到原本的圖像
            painter = QPainter(paint_frame)
            painter.setPen(Qt.red)
            painter.drawRect(self.rect)
            painter.end()
            self.video_label.setPixmap(paint_frame)  # 將繪製好的圖像顯示到label上面
    