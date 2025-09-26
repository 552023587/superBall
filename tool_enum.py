# -*- coding: utf-8 -*-
"""
悬浮球工具箱：双击可配 + 选框截图 + 语音助手
python3.8+  |  pip install pyaudio speechrecognition pillow pyqt5
"""
import enum

# -------------- 工具 --------------
class Tool(enum.Enum):
    NONE = 0
    SCREENSHOT = 1
    VOICE = 2
    MAINWND = 3