# 調整放大比例 輸入自動調整為720p
import cv2
import numpy as np
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
from PIL import Image, ImageTk
from datetime import timedelta

# 創建VideoPlayer類別
class VideoPlayer:
    # Videoplayer類別的初始化方式_init_，開啟視窗，初始畫面
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.window.state('zoomed')
        self.window.resizable(False, False)

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # 創建拖放區域
        self.drop_frame = tk.Label(window, text="拖放影片檔案到這裡，或點擊以選擇檔案", bg="lightgray", width=60, height=10)
        self.drop_frame.pack(pady=20, expand=True, fill=tk.BOTH)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_file_drop)
        self.drop_frame.bind("<Button-1>", self.on_file_click)

        # 創建主畫布來顯示影片
        self.canvas = tk.Canvas(window, width=640, height=480)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        
        # 圈選的起始點和結束點
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.tracking = False

        # 創建控制面板
        self.control_frame = tk.Frame(window)
        self.control_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 按鈕
        self.play_button = tk.Button(self.control_frame, text="Play", command=self.play_video)
        self.play_button.pack(side=tk.LEFT)

        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause_video)
        self.pause_button.pack(side=tk.LEFT)

        self.reset_button = tk.Button(self.control_frame, text="Reset", command=self.reset)
        self.reset_button.pack(side=tk.LEFT)

        self.clear_button = tk.Button(self.control_frame, text="Clear", command=self.clear_trace)
        self.clear_button.pack(side=tk.LEFT)

        # 進度條
        self.progress = tk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, showvalue=0)
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)
        #self.progress.bind("<Motion>", self.on_progress_move)
        self.progress.bind("<B1-Motion>", self.on_progress_move)

        # 顯示時間的標籤
        self.time_label = tk.Label(self.window, text="00:00 / 00:00")
        self.time_label.pack(side=tk.BOTTOM, fill=tk.X)

        # 創建放大視窗
        self.zoom_window = tk.Toplevel(self.window)
        self.zoom_window.title("Zoomed View")
        self.zoom_window.protocol("WM_DELETE_WINDOW", self.reset)
        # 創建畫布到 "Zoom View" 視窗
        self.zoom_canvas = tk.Canvas(self.zoom_window, width=640, height=480)
        self.zoom_canvas.pack(expand=True, fill=tk.BOTH)
        self.zoom_window.withdraw()

        # 綁定鼠標事件
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.vid = None  # cv2.VideoCapture對象
        self.video_source = None  # 影片資料路徑
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.delay = 0
        self.total_duration = timedelta(0)
        self.tracker = None
        self.roi = None

        self.window.mainloop()  # 啟動 Tkinter 的主循環，讓窗口保持顯示並等待事件觸發
            
    
    # 處理當文件被拖放到特定區域時的事件
    def on_file_drop(self, event):
        file_path = self.get_file_path_from_event(event)
        if file_path:
            self.load_video(file_path)
    
    # 移除路徑字符串開頭和結尾的 {}，所有的斜杠 / 替換為反斜杠 \
    def get_file_path_from_event(self, event):
        file_path = event.data.strip('{}').replace('/', '\\')
        return file_path
    
    # 顯示一個文件選擇對話框，讓用戶選擇視頻文件，選擇後加載並播放該視頻
    def on_file_click(self, event):
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv")]
        )
        if file_path:
            self.load_video(file_path)

    # 一開始播放影片
    def load_video(self, video_source):
        if self.vid:
            self.vid.release()
        self.video_source = video_source
        self.vid = cv2.VideoCapture(self.video_source) 
        self.current_frame = 0
        self.total_frames = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        self.delay = int(500 / self.fps)   # self.delay = int(1000 / self.fps)
        #print(self.fps)
        #print(self.delay)
        self.total_duration = timedelta(seconds=int(self.total_frames / self.fps))
        self.tracker = None
        self.roi = None
        self.drop_frame.pack_forget()
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.update()
    '''
        # 調整影片解析度到720p
    def resize_frame_to_720p(self, frame):
        # 目標解析度 720p (1280x720)
        target_width = 1280
        target_height = 720
        return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
    '''

    
    # 對影片的每一幀做處理，物件追蹤，放大後畫面處理，影片適應視窗大小
    def update(self):
        if self.vid and self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # 將每一幀調整為720p
                #frame = self.resize_frame_to_720p(frame)
                if self.tracker and self.tracking:
                    success, bbox = self.tracker.update(frame)
                    if success:
                        # 繪製追蹤框
                        p1 = (int(bbox[0]), int(bbox[1]))
                        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                        # cv2.rectangle 在圖像上繪製矩形框
                        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                        # 顯示放大畫面
                        zoomed_frame = frame[p1[1]:p2[1], p1[0]:p2[0]]
                        
                        # 計算放大畫布的大小
                        zoom_canvas_width = self.zoom_canvas.winfo_width()
                        zoom_canvas_height = self.zoom_canvas.winfo_height()

                        # 計算影像的大小，以保持等比例
                        zoomed_height, zoomed_width = zoomed_frame.shape[:2]
                        zoom_scale = min(zoom_canvas_width / zoomed_width, zoom_canvas_height / zoomed_height)
                        new_zoomed_width = int(zoomed_width * zoom_scale)
                        new_zoomed_height = int(zoomed_height * zoom_scale)

                        # 調整影像大小
                        zoomed_frame = cv2.resize(zoomed_frame, (new_zoomed_width, new_zoomed_height), interpolation=cv2.INTER_LINEAR)

                        # 創建空白畫布以適應放大影像
                        zoom_canvas_frame = 255 * np.ones(shape=[zoom_canvas_height, zoom_canvas_width, 3], dtype=np.uint8)
                        
                        # 計算顯示影像的起始點
                        x_offset = (zoom_canvas_width - new_zoomed_width) // 2
                        y_offset = (zoom_canvas_height - new_zoomed_height) // 2
                        
                        # 將影像放入空白畫布
                        zoom_canvas_frame[y_offset:y_offset+new_zoomed_height, x_offset:x_offset+new_zoomed_width] = zoomed_frame
                        
                        # 轉換為RGB格式以顯示
                        zoom_canvas_frame = cv2.cvtColor(zoom_canvas_frame, cv2.COLOR_BGR2RGB)
                        self.zoom_photo = ImageTk.PhotoImage(image=Image.fromarray(zoom_canvas_frame))
                        self.zoom_canvas.create_image(0, 0, image=self.zoom_photo, anchor=tk.NW)


                # 獲取畫布的寬度和高度
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                frame_height, frame_width = frame.shape[:2]
                scale = min(canvas_width / frame_width, canvas_height / frame_height)

                # 調整影像的大小
                new_width = int(frame_width * scale)
                new_height = int(frame_height * scale)
                resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2

                resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
                self.canvas.create_image(x_offset, y_offset, image=self.photo, anchor=tk.NW)

                self.current_frame = int(self.vid.get(cv2.CAP_PROP_POS_FRAMES))
                progress_value = (self.current_frame / self.total_frames) * 100
                self.progress.set(progress_value)
                current_time = timedelta(seconds=int(self.current_frame / self.fps))
                time_str = f"{str(current_time)[:7]} / {str(self.total_duration)[:7]}"
                self.time_label.config(text=time_str)

            # after 方法是 Tkinter 窗口對象的一部分，用於安排定時任務， 將 self.update 方法安排為在 self.delay 毫秒後被調用
            self.window.after(self.delay, self.update)
    
    # 開始播放視頻並啟動物體追蹤
    def play_video(self):
        if self.vid and not self.vid.isOpened():
            self.vid = cv2.VideoCapture(self.video_source)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        if self.roi and self.roi[2] and self.roi[3]:
            #self.tracker = cv2.TrackerKCF_create()  # 替換為 KCF 追蹤器
            self.tracker = cv2.TrackerCSRT_create()
            ret, frame = self.vid.read()
            if ret:
                self.tracker.init(frame, self.roi)
                self.zoom_window.deiconify()
        #self.tracking = True
        self.update()  # 調用 update 方法，開始進行定時更新。update 方法會定期刷新視頻畫面，並在必要時進行追蹤處理

    # 暫停視頻播放並停止追蹤
    def pause_video(self):
        if self.vid:
            self.vid.release()
        self.tracking = False
        self.start_x = None
        self.start_y = None
        self.rect_id = None

    def reset(self):
        # 停止播放影片並釋放資源
        if self.vid:
            self.vid.release()
        self.canvas.delete("all")  # 清空畫布上的所有圖像
        self.zoom_canvas.delete("all")  # 清空放大視窗畫布上的所有圖像
        # 重置進度條和時間標籤
        self.progress.set(0)
        self.time_label.config(text="00:00 / 00:00")
        self.drop_frame.pack(pady=20, expand=True, fill=tk.BOTH)  # 顯示拖放區域
        self.canvas.pack_forget()  # 隱藏影片畫布
        self.canvas.pack(expand=True, fill=tk.BOTH)  # 將顯示視頻的畫布（canvas）重新顯示，並設置其在窗口中擴展填充
        # 隱藏放大視窗
        self.zoom_window.withdraw()
        # 重置變量
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

    def clear_trace(self):
        # 隱藏放大視窗
        self.zoom_window.withdraw()
        self.tracker = None
        self.roi = None
        self.tracking = False
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        if self.vid and not self.vid.isOpened():
            self.vid = cv2.VideoCapture(self.video_source)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            self.update()
            self.pause_video()

    def on_progress_move(self, event):
        #if self.vid and not self.tracking:  # 確保只有在非追蹤狀態下進行幀的更新:
        self.vid.release()
        progress_value = self.progress.get()
        self.current_frame = int((progress_value / 100) * self.total_frames)
        self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

    def on_mouse_click(self, event):
        if not self.tracking:
            self.start_x, self.start_y = event.x, event.y

    def on_mouse_drag(self, event):
        if not self.tracking and self.start_x and self.start_y:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", tags="choose")

    def on_mouse_release(self, event):
        if not self.tracking and self.start_x and self.start_y:
            end_x, end_y = event.x, event.y
            self.roi = (min(self.start_x, end_x), min(self.start_y, end_y), abs(self.start_x - end_x), abs(self.start_y - end_y))
            print(f"Selected ROI: {self.roi}")
            self.canvas.delete("choose")
            self.tracking = True

    
    # 處理應用程式關閉時的清理工作，確保資源得到妥善釋放
    def on_close(self):
        if self.vid:
            self.vid.release()
        self.window.destroy()
        self.zoom_window.destroy()

root = TkinterDnD.Tk()
VideoPlayer(root, "Tkinter OpenCV Video Player")