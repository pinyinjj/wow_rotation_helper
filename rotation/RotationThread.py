from PySide6.QtCore import QThread, Signal, QMutex
from rotation import RotationHelper


class RotationThread(QThread):
    finished = Signal()  # Signal emitted when the thread finishes

    def __init__(self, config_file, keybind_file, class_name, talent_name):
        super().__init__()
        self.rotation_helper = RotationHelper(class_name, talent_name, config_file, keybind_file)
        self.is_running = True  # Control the running state
        self.mutex = QMutex()  # Thread lock

    def run(self):
        print("RotationThread started.")
        try:
            self.rotation_helper.run()  # This will loop until `running` is False
        except Exception as e:
            print(f"Error in RotationHelper: {e}")
        finally:
            self.is_running = False
            print("RotationThread finished.")
            self.finished.emit()  # Emit the finished signal when the thread completes

    def stop(self):
        """Stop the thread by signaling the rotation_helper to stop."""
        print("Stopping RotationThread.")
        self.mutex.lock()
        self.rotation_helper.stop()  # Signal the RotationHelper to stop its loop
        self.mutex.unlock()

