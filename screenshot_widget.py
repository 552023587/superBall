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

# -------------- 截图 --------------
class ScreenshotWidget(QWidget):
    """选框截图（Esc 取消，双击/回车完成）"""
    done = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.begin = QPoint()
        self.end = QPoint()
        self.qshot = None

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))  # 遮罩
        if not self.begin.isNull() and not self.end.isNull():
            r = QRect(self.begin, self.end).normalized()
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(r, Qt.transparent)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            p.drawRect(r)

    def mousePressEvent(self, ev):
        self.begin = ev.pos()
        self.end = self.begin

    def mouseMoveEvent(self, ev):
        self.end = ev.pos()
        self.update()

    def mouseDoubleClickEvent(self, ev):
        print("[DEBUG] 双击")
        self._shoot()

    def keyPressEvent(self, ev):
        if ev.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._shoot()
        elif ev.key() == Qt.Key_Escape:
            self.close()
    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.end != self.begin:
            self._shoot()          # 松手就截
    def _shoot(self):
        r = QRect(self.begin, self.end).normalized()
        # 转成全局
        r.moveTopLeft(self.mapToGlobal(r.topLeft()))
        print(r.width())
        print(r.height())
        if r.width() <= 10 or r.height() <= 10:
            self.close()
            return

        # 1. 截屏
        screen = QApplication.primaryScreen()
        pix = screen.grabWindow(0, r.x(), r.y(), r.width(), r.height())

        # 2. 弹出「另存为」
        file_path, filt = QFileDialog.getSaveFileName(
            self,
            "保存截图",
            str(Path.home() / "screenshot.png"),  # 默认文件名
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        if not file_path:  # 用户点了取消
            self.close()
            return

        # 3. 按扩展名决定保存质量
        fmt = Path(file_path).suffix[1:].encode().lower()
        ok = pix.save(file_path, fmt, 95 if fmt != b"png" else -1)
        if not ok:
            QMessageBox.critical(self, "错误", "保存失败！")
            self.close()
            return

        # 4. 成功 → 打开文件
        if sys.platform == "win32":
            os.startfile(file_path)
        else:
            subprocess.run(["xdg-open", file_path])

        self.done.emit(pix)
        self.close()
