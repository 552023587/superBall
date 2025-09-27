# bubble_item.py
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy
from markdown import markdown

def md_to_html(txt: str) -> str:
    return markdown(txt, extensions=['extra', 'codehilite'])

class BubbleItem(QWidget):
    appendRequested = pyqtSignal(str)
    adjustRequested = pyqtSignal()
    def __init__(self, text="", pic_path=None, is_me=True):
        super().__init__()
        self.is_me = is_me
        self.text = ""
        self._build_ui()
        self.appendRequested.connect(self._do_append)
        if text:
            self.append_text(text)
        if pic_path:
            self.set_pic(pic_path)

    def _build_ui(self):
        # 用 QLabel 显示富文本，无滚动条
        self.label = QLabel()
        self.label.setWordWrap(True)                       # 自动换行
        self.label.setMaximumWidth(500)
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.label.setStyleSheet(self._css())
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        if self.is_me:
            lay.addStretch(); lay.addWidget(self.label)
        else:
            lay.addWidget(self.label); lay.addStretch()

    def _css(self):
        bg = "#95EC69" if self.is_me else "#FFFFFF"
        return f"QLabel{{background:{bg};color:#000;font-size:20px;font-family:Microsoft YaHei;border-radius:12px;padding:10px 14px;}}"

    def set_text(self, txt: str):
        self.text = txt
        self.label.setText(md_to_html(txt))
        self._update_height()

    def set_pic(self, pic_path: str):
        self.label.setText(self.label.text() + f'<br><img src="{pic_path}" style="max-width:100%;height:auto;">')
        self._update_height()

    def append_text(self, token: str):
        self.text += token
        self.appendRequested.emit(self.text)
        self.adjustRequested.emit()   # 通知父列表更新高度
    @pyqtSlot(str)
    def _do_append(self, txt: str):
        self.set_text(txt)
        if hasattr(self, '_list_item'):
            self._list_item.setSizeHint(self.sizeHint())
        # 用列表引用滚动到底
        if hasattr(self, '_list_widget'):
            self._list_widget.scrollToBottom()

    def _update_height(self):
        # QLabel 自动算高，仅需留边距
        self.label.adjustSize()
        self.adjustSize()