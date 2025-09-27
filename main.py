# main.py
import sys, os, tempfile, subprocess, threading, queue, enum, math, psutil,json
import psutil
from typing import List, Callable, Awaitable
from PyQt5.QtCore import Qt, QTimer, QThreadPool, pyqtSignal, QPropertyAnimation, QEasingCurve, QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction
from robot_tray import RobotStaticTray
from floating_ball import FloatingBanner
from screenshot_widget import ScreenshotWidget
from voice_thread import VoiceThread
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from chat_window import ChatWindow   # 独立聊天窗口
from PyQt5.QtWidgets import qApp
from stock import Stock
import logging

BASE_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

CONFIG_PATH = BASE_DIR+'\\config.json'
CONFIG = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = json.load(f)
print(CONFIG)                   
# ========== 1. 异步数据 Worker ==========
class DataWorker(QObject):
    """在子线程里轮询接口，拿到数据后发射 signal"""
    dataReady = pyqtSignal(list)   # 发射 List[str]

    def __init__(self, fetcher: Callable[[], List[str]], interval: int = 3000):
        super().__init__()
        self.fetcher = fetcher       # 接口函数
        self.interval = interval     # 毫秒

    def start(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._run)
        self.timer.start(self.interval)
        self._run()                  # 立刻执行一次

    def _run(self):
        try:
            new_data = self.fetcher()
            if new_data and isinstance(new_data, list):
                self.dataReady.emit(new_data)
        except Exception as e:
            print("接口异常:", e)
            self.dataReady.emit(["--"])


class HiddenMain(QMainWindow):
    def __init__(self):
        super().__init__()
        # 完全隐藏主窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(0, 0)

        # -------------- 托盘 --------------
        self.menu = self._build_menu()
        self.tray = RobotStaticTray(self.menu, self)
        self.tray.show()

        # -------------- 悬浮球 --------------
        self.ball = FloatingBanner(self)


        self._cpu_fetch()

        # 子线程跑数据
        self.thread = QThread()
        self.worker = DataWorker(self._stock_fetch, interval=10000)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start)
        self.worker.dataReady.connect(self.ball.onData)
        self.thread.start()

        self.ball.show()

        # -------------- 截图快捷键 --------------
        self.shortcut = QShortcut(QKeySequence("Alt+Shift+S"), self)
        self.shortcut.activated.connect(self.do_screenshot)

        # -------------- 语音识别 --------------
        # self.voice = VoiceThread()
        # self.voice.wake.connect(self.on_voice)
        # self.voice.start()

        # -------------- 聊天窗口实例 --------------
        self.chat = None   # 懒加载

    # -------------- 托盘菜单 --------------
    def _build_menu(self):
        menu = QMenu()
        act_chat = QAction("打开聊天窗口", self)
        act_chat.triggered.connect(self.toggle_chat)
        act_shot = QAction("选框截图", self)
        act_shot.triggered.connect(self.do_screenshot)
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(qApp.quit)
        menu.addAction(act_chat)
        menu.addAction(act_shot)
        menu.addSeparator()
        menu.addAction(act_quit)
        return menu

    # -------------- 截图 --------------
    def do_screenshot(self):
        self.ss = ScreenshotWidget()
        self.ss.done.connect(lambda: None)
        self.ss.show()

    # -------------- 语音命令 --------------
    def on_voice(self, text):
        if "截图" in text:
            self.do_screenshot()
        elif "聊天" in text or "打开窗口" in text:
            self.toggle_chat()
        elif "退出" in text:
            qApp.quit()

    # -------------- 聊天窗口开关 --------------
    def toggle_chat(self):
        if self.chat is None:
            self.chat = ChatWindow()
            self.chat.closed.connect(self.on_chat_closed)
        if self.chat.isVisible():
            self.chat.raise_()
            self.chat.activateWindow()
        else:
            self.chat.show()

    def on_chat_closed(self):
        # 聊天窗口只是隐藏，实例仍在
        self.chat = None
    def show_main(self):
        self.toggle_chat()

    def _cpu_fetch(self) -> List[str]:
        val = psutil.cpu_percent()
        self.ball.onData([f"{int(val)}%","222"])

    def _stock_fetch(self) -> List[str]:
        prices = []
        tips = []
        values = []
        thresholds = []
        res = Stock().fund_realtime_stock(CONFIG['stock'])
        for i in range(len(res["stock_code"])):
            close_price = float(res["price"][i])
            prices.append(str(close_price))
            values.append(close_price)
            tips.append(res["short_name"][i])
            thresholds.append(CONFIG['stock_thresholds'][i])
        res = Stock().fund_etf(CONFIG['etf'][0])
        print(res)
        for i in range(len(res["fund_code"])):
            close_price = float(res["price"][i])
            prices.append(str(close_price))
            values.append(close_price)
            tips.append(res["fund_code"][i])
            thresholds.append(CONFIG['etf_thresholds'][i])
        self.ball.onData(texts=prices,tooltips=tips,values=values,thresholds=thresholds)
# -------------- 启动 --------------
if __name__ == '__main__':
    try:
         # 配置日志
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=os.path.join(BASE_DIR, 'error.log'),
            filemode='a'
        )
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        hidden = HiddenMain()
        #hidden.show_main()   # 完全隐藏
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application error: {str(e)}", exc_info=True)
        print(e)