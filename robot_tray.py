# -*- coding: utf-8 -*-
"""
悬浮球工具箱：双击可配 + 选框截图 + 语音助手
python3.8+  |  pip install pyaudio speechrecognition pillow pyqt5
"""
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

class RobotStaticTray(QSystemTrayIcon):
    def __init__(self, menu, parent=None):
        super().__init__(parent)
        self.setContextMenu(menu)
        self.update_icon()

    def update_icon(self):
        px = QPixmap(16, 16)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor("#2196F3")))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 16, 16)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawEllipse(QPoint(5, 5), 2, 2)
        p.drawEllipse(QPoint(11, 5), 2, 2)
        p.end()
        self.setIcon(QIcon(px))