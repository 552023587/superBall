# main.py
import sys, os, tempfile, subprocess, threading, queue, enum
import psutil
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction
from robot_tray import RobotStaticTray
from floating_ball import FloatingBanner
from screenshot_widget import ScreenshotWidget
from voice_thread import VoiceThread
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from chat_window import ChatWindow   # 独立聊天窗口
from PyQt5.QtWidgets import qApp



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

         # 数据接口（示例 CPU）
        self.cpu_timer = QTimer(self)
        self.cpu_timer.timeout.connect(self._cpu_fetch)
        self.cpu_timer.start(2000)
        self._cpu_fetch()

        self.ball.show()

        # -------------- 截图快捷键 --------------
        self.shortcut = QShortcut(QKeySequence("Alt+Shift+S"), self)
        self.shortcut.activated.connect(self.do_screenshot)

        # -------------- 语音识别 --------------
        self.voice = VoiceThread()
        self.voice.wake.connect(self.on_voice)
        self.voice.start()

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

    def _cpu_fetch(self):
        val = psutil.cpu_percent()
        self.ball.onData([f"{int(val)}%"])

# -------------- 启动 --------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    hidden = HiddenMain()
    # hidden.show()   # 完全隐藏
    sys.exit(app.exec_())