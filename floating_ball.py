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
from tool_enum import Tool
# -------------- 悬浮球 --------------
class FloatingBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._drag_pos = QPoint()
        self.db_tool = Tool.MAINWND  # 默认双击打开主窗口

        # 外观
        self.bg_color = QColor("#ffffff")
        self.border_color = QColor("#2196F3")
        self.text_color = self.border_color
        self.font_size = 14
        self.texts = ["..."]
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setAttribute(Qt.WA_PaintOnScreen, False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.resize(60, 60)
    def _round_mask(self):
        """返回一个圆形 QRegion，用来裁掉四角"""
        diameter = min(self.width(), self.height())
        region = QRegion(0, 0, diameter, diameter, QRegion.Ellipse)
        return region
    
    def resizeEvent(self, ev):
        """窗口大小一变，掩码跟着变"""
        super().resizeEvent(ev)
        self.setMask(self._round_mask())
    # ------ 接收数据 ------
    def onData(self, texts):
        self.texts = texts
        self.update()

    # ------ 绘制 ------
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)        # 抗锯齿
        p.setRenderHint(QPainter.HighQualityAntialiasing, True)

        dia = min(self.width(), self.height())
        rect = QRectF(0, 0, dia, dia)
        rect.moveCenter(self.rect().center())

        # 1. 画阴影（可选，视觉更柔和）
        shadow = QRadialGradient(rect.center(), dia/2)
        shadow.setColorAt(0, QColor(33, 150, 243, 0))     # 中心透明
        shadow.setColorAt(0.9, QColor(33, 150, 243, 30))  # 边缘淡蓝
        shadow.setColorAt(1, QColor(33, 150, 243, 80))
        p.setBrush(shadow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(rect.adjusted(-2, -2, 2, 2))        # 比本体大一点

        # 2. 画实心圆（白底 + 蓝边）
        path = QPainterPath()
        path.addEllipse(rect)
        p.fillPath(path, QBrush(QColor("#ffffff")))
        p.setPen(QPen(QColor("#2196F3"), 3))
        p.drawPath(path)

        # 3. 文字
        p.setPen(QColor("#2196F3"))
        p.setFont(QFont("Microsoft YaHei", self.font_size, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, self.texts[0])

    # ------ 鼠标 ------
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_pos = ev.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.LeftButton and not self._drag_pos.isNull():
            self.move(ev.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, ev):
        self._drag_pos = QPoint()
        self._magnetic_to_edge()

    def mouseDoubleClickEvent(self, ev):
        if self.db_tool == Tool.SCREENSHOT:
            self._parent.do_screenshot()
        elif self.db_tool == Tool.VOICE:
            self._parent.do_voice()
        else:
            self._parent.show_main()

    def contextMenuEvent(self, ev):
        pass

    # ------ 贴边吸附 ------
    def _magnetic_to_edge(self):
        desk = QApplication.primaryScreen().availableGeometry()
        margin = 20
        g = self.frameGeometry()
        tgt = QRect(g)
        if g.left() <= margin:
            tgt.moveLeft(0)
        elif desk.right() - g.right() <= margin:
            tgt.moveRight(desk.right())
        if g.top() <= margin:
            tgt.moveTop(0)
        if tgt == g:
            return
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(200)
        self._anim.setStartValue(g)
        self._anim.setEndValue(tgt)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

