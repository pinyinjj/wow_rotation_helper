from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
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
        self.label = QLabel("Press Key Combination To Bind.", self)
        layout.addWidget(self.label)

        self.key_sequence = None
        self.shift_pressed = False  # 用于记录 Shift 键是否按下

    def keyPressEvent(self, event):
        """捕获按键事件"""
        key = event.key()  # 获取按键
        modifiers = event.modifiers()  # 获取修饰符（Ctrl, Shift, Alt 等）

        # 如果按下的是 Shift 键，先不记录，等待下一个按键
        if key == Qt.Key_Shift:
            self.shift_pressed = True
            return  # 暂时不记录按下 Shift 的事件

        # 如果按下了其他键，并且 Shift 键按下，记录为 Shift + 按键
        if self.shift_pressed:
            resolved_key = self.map_special_key(key)  # 处理特殊字符
            self.key_sequence = f"Shift + {resolved_key}"
            self.shift_pressed = False  # 重置 Shift 键的状态

        elif modifiers & Qt.ControlModifier:
            # Ctrl 组合按键
            self.key_sequence = f"Ctrl + {self.key_to_string(key)}"

        elif modifiers & Qt.AltModifier:
            # Alt 组合按键
            self.key_sequence = f"Alt + {self.key_to_string(key)}"

        else:
            # 如果没有按下修饰键，直接记录单个按键
            self.key_sequence = self.key_to_string(key)

        # 更新显示标签
        self.label.setText(f"Captured: {self.key_sequence}")

        # 关闭对话框
        self.accept()

    def key_to_string(self, key):
        """将按键转换为字符串表示"""
        return QKeySequence(key).toString()

    def map_special_key(self, key):
        """将特殊字符映射回其原始的按键值"""
        special_key_map = {
            Qt.Key_Backtick: "`",
            Qt.Key_Exclam: "1",   # '!' -> '1'
            Qt.Key_At: "2",       # '@' -> '2'
            Qt.Key_NumberSign: "3",  # '#' -> '3'
            Qt.Key_Dollar: "4",   # '$' -> '4'
            Qt.Key_Percent: "5",  # '%' -> '5'
            Qt.Key_AsciiCircum: "6",  # '^' -> '6'
            Qt.Key_Ampersand: "7",    # '&' -> '7'
            Qt.Key_Asterisk: "8",  # '*' -> '8'
            Qt.Key_ParenLeft: "9",    # '(' -> '9'
            Qt.Key_ParenRight: "0"    # ')' -> '0'
        }

        # 如果是特殊字符，则转换为对应的原始按键
        return special_key_map.get(key, self.key_to_string(key))
