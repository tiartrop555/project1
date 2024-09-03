# start.py
import sys
from PyQt5.QtWidgets import QApplication
from player import VideoPlayer

# 應用程式的主要入口點
def main():
    app = QApplication(sys.argv)  # 創建一個 QApplication 對象，並將命令列參數傳遞給它，初始化應用程式，並會處理應用程式的事件循環。
    player = VideoPlayer()  # VideoPlayer 對象，應用程式的主要視窗
    player.show()  # 顯示 VideoPlayer 窗口
    sys.exit(app.exec_())  # 啟動應用程式的事件循環，並在事件循環結束後退出應用程式

# 檢查是否是直接運行此腳本，如果是直接運行，則執行下面的 main() 函數
if __name__ == "__main__":
    main()  # 調用 main 函數來啟動應用程式