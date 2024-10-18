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
        font_size=30,
        bg_color_readonly="#1e1e1e",
        hover_color="#6c99f4",
        parent=None,
    ):

        super().__init__(parent)

        # 设置为只读
        self.setReadOnly(True)

        # 设置样式，包括自定义滚动条样式
        self.setStyleSheet(f"""
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
            /* 自定义滚动条样式 */
            QScrollBar:vertical {{
                border: none;
                background: {bg_color}; /* 滚动条背景色 */
                width: 10px; /* 滚动条宽度 */
                margin: 0px 0px 0px 0px; /* 外边距 */
            }}
            QScrollBar::handle:vertical {{
                background:{color}; /* 滚动条滑块颜色 */
                min-height: 30px; /* 滑块最小高度 */
                border-radius: 5px; /* 滑块圆角 */
            }}
            QScrollBar::handle:vertical:hover {{
                background: {hover_color}; /* 滑块悬停颜色 */
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none; /* 上下箭头按钮的背景色 */
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none; /* 上下滚动区域的背景色 */
            }}
        """)

        # 连接信号以追加日志消息
        self.textWritten.connect(self.append_log)

    def write(self, message):
        """将捕获的输出发送到信号"""
        if message.strip():  # 过滤空白字符
            self.textWritten.emit(message)

    def flush(self):
        """用于兼容性"""
        pass

    def append_log(self, message):
        """追加日志消息并滚动到末尾"""
        self.append(message)
        self.ensureCursorVisible()


