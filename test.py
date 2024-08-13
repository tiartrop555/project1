import cv2
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog
from PIL import Image, ImageTk
from datetime import timedelta

class VideoPlayer:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        # 綁定關閉事件以關閉所有視窗
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

        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop_video)
        self.stop_button.pack(side=tk.LEFT)

        # 進度條
        self.progress = tk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, showvalue=0)
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)
        self.progress.bind("<Motion>", self.on_progress_move)

        # 顯示時間的標籤
        self.time_label = tk.Label(self.window, text="00:00 / 00:00")
        self.time_label.pack(side=tk.BOTTOM, fill=tk.X)

        # 創建放大視窗
        self.zoom_window = tk.Toplevel(self.window)
        self.zoom_window.title("Zoomed View")
        self.zoom_window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.zoom_canvas = tk.Canvas(self.zoom_window, width=640, height=480)
        self.zoom_canvas.pack(expand=True, fill=tk.BOTH)

        # 綁定鼠標事件
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.vid = None
        self.video_source = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.delay = 0
        self.total_duration = timedelta(0)
        self.tracker = None
        self.roi = None

        self.window.mainloop()
    
    def on_file_drop(self, event):
        """Handle file drop event."""
        file_path = self.get_file_path_from_event(event)
        if file_path:
            self.load_video(file_path)
    
    def get_file_path_from_event(self, event):
        """Extract file path from event data."""
        # Remove leading and trailing quotes (for Windows paths)
        file_path = event.data.strip('{}').replace('/', '\\')
        return file_path
    
    def on_file_click(self, event):
        """Handle file click event to open file dialog."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"), ("All files", "*.*")]
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, video_source):
        """Load the video file."""
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
        self.drop_frame.pack_forget()
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.control_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.play_video()

    def update(self):
        if self.vid and self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                if self.tracker and self.tracking:
                    # 更新追蹤器
                    success, bbox = self.tracker.update(frame)
                    if success:
                        # 繪製追蹤框
                        p1 = (int(bbox[0]), int(bbox[1]))
                        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                        # 在 Tkinter 畫布上繪製追蹤框
                        self.canvas.delete("tracker")
                        self.canvas.create_rectangle(p1[0], p1[1], p2[0], p2[1], outline="blue", width=2, tags="tracker")

                        # 顯示放大畫面
                        zoomed_frame = frame[p1[1]:p2[1], p1[0]:p2[0]]
                        zoomed_frame = cv2.resize(zoomed_frame, (640, 480), interpolation=cv2.INTER_LINEAR)
                        zoomed_frame = cv2.cvtColor(zoomed_frame, cv2.COLOR_BGR2RGB)
                        self.zoom_photo = ImageTk.PhotoImage(image=Image.fromarray(zoomed_frame))
                        self.zoom_canvas.create_image(0, 0, image=self.zoom_photo, anchor=tk.NW)

                # 自动调整帧的大小以适应画布
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                # 获取视频的宽高
                frame_height, frame_width = frame.shape[:2]

                # 计算缩放比例以保持纵横比
                scale = min(canvas_width / frame_width, canvas_height / frame_height)

                # 根据比例调整帧的大小
                new_width = int(frame_width * scale)
                new_height = int(frame_height * scale)
                resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

                # 计算图像置中时的左上角坐标
                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2

                # 将 BGR 影像轉換為 RGB
                resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                # 轉換為 PIL 影像
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(resized_frame))
                self.canvas.create_image(x_offset, y_offset, image=self.photo, anchor=tk.NW)

                self.current_frame = int(self.vid.get(cv2.CAP_PROP_POS_FRAMES))
                progress_value = (self.current_frame / self.total_frames) * 100
                self.progress.set(progress_value)

                current_time = timedelta(seconds=int(self.current_frame / self.fps))
                time_str = f"{str(current_time)[:7]} / {str(self.total_duration)[:7]}"
                self.time_label.config(text=time_str)

            self.window.after(self.delay, self.update)
    
    def play_video(self):
        if self.vid and not self.vid.isOpened():
            self.vid = cv2.VideoCapture(self.video_source)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        if self.roi and self.roi[2] and self.roi[3]:
            # 初始化追蹤器
            self.tracker = cv2.TrackerCSRT_create()
            ret, frame = self.vid.read()
            if ret:
                self.tracker.init(frame, self.roi)
        self.tracking = True  # 開始追蹤
        self.update()

    def pause_video(self):
        if self.vid:
            self.vid.release()
        self.tracking = False  # 停止追蹤
        # 進入圈選模式
        self.start_x = None
        self.start_y = None
        self.rect_id = None

    def stop_video(self):
        if self.vid:
            self.vid.release()
        self.canvas.delete("all")
        self.current_frame = 0
        self.progress.set(0)
        self.time_label.config(text="00:00 / 00:00")
        self.tracker = None
        self.roi = None
        self.tracking = False

    def on_progress_move(self, event):
        if self.vid:
            progress_value = self.progress.get()
            self.current_frame = int((progress_value / 100) * self.total_frames)
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

    def set_frame_position(self, frame_pos):
        if self.vid:
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

    def on_mouse_click(self, event):
        if not self.tracking:
            self.start_x, self.start_y = event.x, event.y

    def on_mouse_drag(self, event):
        if not self.tracking and self.start_x and self.start_y:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red")

    def on_mouse_release(self, event):
        if not self.tracking and self.start_x and self.start_y:
            end_x, end_y = event.x, event.y
            self.roi = (min(self.start_x, end_x), min(self.start_y, end_y), abs(self.start_x - end_x), abs(self.start_y - end_y))
            print(f"Selected ROI: {self.roi}")

    def on_close(self):
        if self.vid:
            self.vid.release()
        self.window.destroy()
        self.zoom_window.destroy()

# 創建主視窗
root = TkinterDnD.Tk()
VideoPlayer(root, "Tkinter OpenCV Video Player")