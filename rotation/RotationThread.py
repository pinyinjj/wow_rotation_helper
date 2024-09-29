from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
from rotation import RotationHelper


class RotationThread(QThread):
    finished = Signal()  # 线程完成时的信号

    def __init__(self, config_file, keybind_file, class_name, talent_name):
        super().__init__()
        self.rotation_helper = RotationHelper(class_name, talent_name, config_file, keybind_file)
        self.is_running = True  # 控制运行状态
        self.is_paused = False  # 控制暂停状态
        self.mutex = QMutex()  # 线程锁
        self.pause_cond = QWaitCondition()  # 暂停条件

    def run(self):
        print("RotationThread started.")
        while self.is_running:
            self.mutex.lock()  # 加锁

            if self.is_paused:
                print("RotationThread paused. Waiting to resume...")
                self.pause_cond.wait(self.mutex)  # 等待恢复
                print("RotationThread resumed.")

            self.mutex.unlock()  # 解锁

            if not self.is_running:  # 在运行标志检查之后立即跳出循环
                break

            print("RotationThread running rotation_helper.run()")
            self.rotation_helper.run()  # 运行 RotationHelper 的逻辑
            self.msleep(100)  # 避免 CPU 占用过高

        print("RotationThread finished.")
        self.finished.emit()  # 线程结束时发出信号


    def pause(self):
        """暂停线程"""
        print("Pausing RotationThread.")
        self.mutex.lock()
        self.is_paused = True
        self.rotation_helper.pause()
        self.mutex.unlock()

    def resume(self):
        """恢复线程"""
        print("Resuming RotationThread.")
        self.mutex.lock()
        self.is_paused = False
        self.rotation_helper.resume()
        self.pause_cond.wakeAll()  # 唤醒所有等待的线程
        self.mutex.unlock()
