# start.py
import sys  # 提供了與 Python 解譯器和操作系統之間交互的功能。這裡主要用於獲取命令行參數並在程式結束時退出
from PyQt5.QtWidgets import QApplication  # QApplication 是每個 PyQt 應用程式都必須實例化的一個類，負責管理應用程式的控制流和主要設置。它處理 GUI 事件並監控應用程式的整體運行。
from player import VideoPlayer  # 從名為 player 的模組（通常是另一個 Python 檔案）中匯入 VideoPlayer 類。這個類定義了應用程式的主要視窗，具體內容在 player.py 文件中。

#QApplication 提供了運行環境，而 VideoPlayer 提供了用戶界面
def main():
    app = QApplication(sys.argv)  # 創建一個 QApplication 實例 app。sys.argv 是從命令行傳遞給應用程式的參數列表，允許我們從命令行控制應用程式的行為。
    player = VideoPlayer()  # 創建 VideoPlayer 類的一個實例 player，這個實例是主視窗或主介面。
    player.show()  # 顯示 VideoPlayer 視窗。這會使視窗在螢幕上可見
    sys.exit(app.exec_())  # 進入應用程式的主事件循環。
                           # app.exec_() 會運行應用程式的事件循環，並在關閉應用程式時返回一個狀態碼。
                           # sys.exit() 確保應用程式乾淨地退出並返回正確的狀態碼給操作系統。

if __name__ == "__main__":  # 用於確保只有當這個腳本作為主程式執行時，main() 函數才會被調用。可以防止在此腳本被其他腳本作為模組導入時不必要地運行 main() 函數。
    main()