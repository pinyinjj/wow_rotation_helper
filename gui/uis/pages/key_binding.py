from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QMainWindow, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

class KeyBindDialog(QDialog):
    """自定义对话框用于捕获按键绑定"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keybinding info")
        self.setModal(True)
        self.setFixedSize(300, 100)

        layout = QVBoxLayout(self)
        self.label = QLabel("Press Any Key To Bind.", self)
        layout.addWidget(self.label)

        self.key_sequence = None

    def keyPressEvent(self, event):
        """捕获按键事件"""
        key_sequence = QKeySequence(event.key())
        self.key_sequence = key_sequence.toString()
        self.accept()  # 关闭对话框


