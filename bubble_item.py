# -*- coding: utf-8 -*-
import sys, os, tempfile, subprocess, threading, queue, enum
from pathlib import Path
import psutil
from PyQt5.QtCore import (
    Qt, QPoint, QRect, QRectF, QTimer, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve, QObject, QSize
)
from PyQt5.QtGui import (
    QPainter, QBrush, QColor, QPen, QPainterPath, QFont,
    QIcon, QPixmap, QCursor, QKeySequence,QRegion,QRadialGradient
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, QSystemTrayIcon, QShortcut, QMessageBox,
    QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QScrollArea, QFrame, QFileDialog
)


class BubbleItem(QWidget):
    
    def __init__(self, text="", pic_path=None, is_me=True):
        super().__init__()
        self.is_me = is_me
        self.text = ""
        # 水平布局：自己靠右，对方靠左
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        lbl = QLabel()
        self.lbl = lbl
        lbl.setWordWrap(True)
        lbl.setMaximumWidth(420)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # 圆角气泡
        lbl.setStyleSheet(self._style())
        if text:
            lbl.setText(text)
        if pic_path:
            pix = QPixmap(pic_path).scaledToWidth(220, Qt.SmoothTransformation)
            lbl.setPixmap(pix)

        if is_me:
            layout.addStretch()
            layout.addWidget(lbl)
        else:
            layout.addWidget(lbl)
            layout.addStretch()

    def _style(self):
        bg = "#95EC69" if self.is_me else "#FFFFFF"
        color = "#000" if self.is_me else "#000"
        return f"""
            QLabel{{
                background:{bg};
                color:{color};
                border-radius:12px;
                padding:10px 14px;
                font:14px "Microsoft YaHei";
            }}
        """
    
    def append_text(self, token: str):
        self.text += token
        self.lbl.setText(self.text)


    def finish(self):
        # 可选：改变背景，表示流式结束
        self.lbl.setStyleSheet(self._style() + "border:2px solid #2196F3;")