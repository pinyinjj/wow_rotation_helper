
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTextEdit

class PyLoggerWindow(QTextEdit):
    textWritten = Signal(str)

    def __init__(
        self,
        bg_color="#2c2c2c",
        color="#ffffff",
        radius="8px",
        padding="10px",
        font_size=12,
        bg_color_readonly="#1e1e1e",
        parent=None,
    ):
        super().__init__(parent)

        # 设置为只读
        self.setReadOnly(True)

        # 自定义样式
        self.setStyleSheet(f'''
            QTextEdit {{
                background-color: {bg_color};
                color: {color};
                border-radius: {radius};
                padding: {padding};
                font-size: {font_size}px;
            }}
            QTextEdit[readOnly="true"] {{
                background-color: {bg_color_readonly};
            }}
        ''')

        # 连接信号槽，用于将捕获的文本显示到日志窗口
        self.textWritten.connect(self.append_log)

    def write(self, message):
        """将捕获的输出发送到信号"""
        if message.strip():  # 过滤空白字符
            self.textWritten.emit(message)

    def flush(self):
        """用于兼容性"""
        pass

    def append_log(self, message):
        """追加日志消息，并滚动到末尾"""
        self.append(message)
        self.ensureCursorVisible()

