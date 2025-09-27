# -*- coding: utf-8 -*-
import sys, os, tempfile, subprocess, threading, queue, enum,random
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
    QListWidgetItem, QLabel, QScrollArea, QFrame, QFileDialog,QToolTip
)
from tool_enum import Tool

class FloatingBanner(QWidget):
    def __init__(self, parent=None):
        """
        浮动横幅类的初始化方法
        :param parent: 父窗口对象
        """
        super().__init__(parent)
        self._parent = parent  # 保存父窗口引用
        self._drag_pos = QPoint()  # 拖动位置初始化
        self.db_tool = Tool.MAINWND  # 默认双击打开主窗口

        # 外观设置
        self.bg_color = QColor("#ffffff")  # 背景色
        self.border_color = QColor("#2196F3")  # 边框颜色
        self.text_color = self.border_color  # 文字颜色
        self.font_size = 14  # 字体大小
        self.texts = ["..."]  # 显示文本列表
        self.tooltips = ["默认提示"]  # 提示文本列表
        self.thresholds = None  # 阈值列表
        self.values = None  # 数值列表
        
        # 设置窗口标志：无边框、置顶、工具窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 设置窗口属性：透明背景、非系统背景、不绘制在屏幕上、不透明鼠标事件
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setAttribute(Qt.WA_PaintOnScreen, False)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.resize(90, 90)  # 设置初始窗口大小

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
    def onData(self, texts, tooltips=None, values=None, thresholds=None):
        """
        更新显示文本和提示文本
        :param texts: 显示文本列表
        :param tooltips: 提示文本列表，可选
        :param values: 数值列表，可选
        :param thresholds: 阈值列表，可选
        """
        # 确保texts是字符串列表
        self.texts = [str(text) if not isinstance(text, str) else text for text in texts]
        
        # 如果提供了tooltips，确保它们也是字符串列表
        if tooltips:
            self.tooltips = [str(tip) if not isinstance(tip, str) else tip for tip in tooltips]
            
        # 如果提供了values和thresholds，保存它们
        if values is not None:
            self.values = values
        if thresholds is not None:
            self.thresholds = thresholds
            
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
        # 随机选择一个文本和对应的值（如果有）
        index = random.randint(0, len(self.texts) - 1)
        text = self.texts[index]
        
        # 确定文字颜色
        text_color = QColor("#2196F3")  # 默认蓝色
        if self.values is not None and self.thresholds is not None and index < len(self.values):
            try:
                value = float(self.values[index])
                threshold = float(self.thresholds[index])
                # 根据值与阈值的关系设置颜色
                if value > threshold:
                    text_color = QColor("#7b00ff")  # 红色
                else:
                    text_color = QColor("#009a7e")  # 绿色
            except (ValueError, TypeError):
                # 如果转换失败，使用默认颜色
                pass
        
        p.setPen(text_color)
        p.setFont(QFont("Microsoft YaHei", self.font_size, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, text)

    # ------ 鼠标事件 ------
    def enterEvent(self, event):
        """鼠标进入窗口时显示提示"""
        if self.tooltips:
            # 确保选择的提示是字符串
            tooltip = random.choice(self.tooltips)
            if not isinstance(tooltip, str):
                tooltip = str(tooltip)
            QToolTip.showText(event.globalPos(), tooltip)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口时隐藏提示"""
        QToolTip.hideText()
        super().leaveEvent(event)

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


