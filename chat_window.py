# chat_window.py
from PyQt5.QtCore import Qt, QTimer, QThreadPool, pyqtSignal   # ←加这一行
from PyQt5.QtGui import QPixmap, QFont, QTextDocument
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QHBoxLayout, QShortcut, QFileDialog,QApplication
)
from bubble_item import BubbleItem   # 沿用前面的气泡
from llm_stream import StreamLLM     # 上一篇的流式 LLM 封装
import os

class ChatWindow(QWidget):
    closed = pyqtSignal()   # 通知主窗口已关闭

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 聊天")
        self.resize(720, 1080)
        self.setStyleSheet(self.qss())
        self.init_ui()
        self.llm = StreamLLM(
            provider="qwen",
            api_key="sk-0b60c076e5b047e0aa5a403e386b9037",
            model="qwen3-max"
        )
        self.messages = []

    def init_ui(self):
        central = QVBoxLayout(self)

        self.list_w = QListWidget()
        self.input = QTextEdit()
        self.input.setMaximumHeight(90)

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.send_message)
        pic_btn = QPushButton("图片")
        pic_btn.clicked.connect(self.pick_pic)

        hbox = QHBoxLayout()
        hbox.addWidget(pic_btn)
        hbox.addStretch()
        hbox.addWidget(send_btn)

        central.addWidget(self.list_w)
        central.addWidget(self.input)
        central.addLayout(hbox)

        self.setAcceptDrops(True)
        self.input.installEventFilter(self)

    # -------------- 发送 & 流式 --------------
    def send_message(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.add_bubble(text, is_me=True)
        self.input.clear()
        self.messages.append({"role": "user", "content": text})

        item = QListWidgetItem()
        bubble = BubbleItem("", is_me=False)
        item.setSizeHint(bubble.sizeHint())
        self.list_w.addItem(item)
        self.list_w.setItemWidget(item, bubble)

        def stream():
            full = ""
            for tok in self.llm.stream(self.messages):
                full += tok
                bubble.append_text(tok)
            self.messages.append({"role": "assistant", "content": full})

        QThreadPool.globalInstance().start(stream)

    # -------------- 图片拖拽 --------------
    def add_bubble(self, text="", pic_path=None, is_me=True):
        item = QListWidgetItem()
        bubble = BubbleItem(text, pic_path, is_me)
        item.setSizeHint(bubble.sizeHint())
        self.list_w.addItem(item)
        self.list_w.setItemWidget(item, bubble)
        bubble._list_item = item          # 给气泡 item 引用
        bubble._list_widget = self.list_w  # ← 给气泡列表引用
        self.list_w.scrollToBottom()

    def pick_pic(self):
        path, _ = QFileDialog.getOpenFileName(self, "选图", "", "Images (*.png *.jpg *.bmp)")
        if path:
            self.add_bubble(pic_path=path, is_me=True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasImage() or e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0].toLocalFile()
            self.add_bubble(pic_path=url, is_me=True)

    def eventFilter(self, obj, ev):
        if obj == self.input and ev.type() == ev.KeyPress and ev.key() in (Qt.Key_Return, Qt.Key_Enter) and ev.modifiers() == Qt.NoModifier:
            self.send_message()
            return True
        return super().eventFilter(obj, ev)

    # -------------- 关闭即隐藏 --------------
    def closeEvent(self, ev):
        self.hide()
        self.closed.emit()
        ev.ignore()

    # -------------- 皮肤 --------------
    def qss(self):
        return """
        /* ========== 全局 ========== */
        QWidget{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #1e1e2e, stop:1 #252536);
            color: #E0E0E0;
            font-size: 21px;
            font-family: "Microsoft YaHei", "PingFang SC";
        }

        /* ========== 聊天列表 ========== */
        QListWidget{
            background: transparent;
            border: none;
            outline: 0;
        }
        QListWidget::item{
            border-radius: 12px;
            padding: 4px;
        }
        QListWidget::item:selected{
            background: rgba(255, 255, 255, 30);
        }

        /* ========== 输入框 ========== */
        QTextEdit{
            background: #2C2C3E;
            color: #E0E0E0;
            border: 1px solid #3A3A4D;
            border-radius: 12px;
            padding: 10px;
            selection-background-color: #2196F3;
        }

        /* ========== 按钮 ========== */
        QPushButton{
            background: #2196F3;
            color: white;
            border-radius: 10px;
            padding: 10px 22px;
            font-size: 21px;
            font-weight: 500;
        }
        QPushButton:hover{
            background: #42A5F5;
        }
        QPushButton:pressed{
            background: #1E88E5;
        }

        /* ========== 滚动条 ========== */
        QScrollBar:vertical{
            background: transparent;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical{
            background: #5A5A72;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical{
            border: none;
            background: none;
        }
        """