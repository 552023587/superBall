import speech_recognition as sr
from PyQt5.QtCore import QThread, pyqtSignal

class VoiceThread(QThread):
    wake = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        """软探测 -> 有麦才工作，无麦静默跳过"""
        try:
            # 1. 仅探测硬件
            sr.Microphone()
        except Exception as e:          # OSError / AttributeError 都抓
            print("麦克风不可用，语音线程跳过：", e)
            return

        # 2. 正式工作循环（带兜底）
        try:
            with sr.Microphone() as source:
                rec = sr.Recognizer()
                rec.energy_threshold = 1500
                rec.adjust_for_ambient_noise(source, duration=0.5)
                while self._running:
                    try:
                        audio = rec.listen(source, timeout=1, phrase_time_limit=5)
                        text = rec.recognize_google(audio, language="zh-CN")
                        self.wake.emit(text)
                    except (sr.WaitTimeoutError, sr.UnknownValueError):
                        continue
        except Exception as e:
            print("语音识别运行异常：", e)

    def stop(self):
        self._running = False
        self.wait()