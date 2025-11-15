from PySide6.QtCore import QThread, Signal, QMutex
from rotation import RotationHelper

class RotationThread(QThread):
    finished = Signal()  # Signal emitted when the thread finishes
    icon_matched = Signal(str)  # Signal emitted when an icon is matched (icon_name)

    def __init__(self, config_file, keybind_file, class_name, talent_name, game_version):
        super().__init__()
        self.rotation_helper = RotationHelper(class_name, talent_name, config_file, keybind_file, game_version)
        # Set callback to emit signal when icon is matched
        self.rotation_helper.set_match_callback(self.on_icon_matched)
        self.is_running = True  # Control the running state
        self.mutex = QMutex()  # Thread lock
    
    def on_icon_matched(self, icon_name):
        """Callback function to emit signal when icon is matched"""
        self.icon_matched.emit(icon_name)

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
        if self.rotation_helper:
            self.rotation_helper.stop()  # Signal the RotationHelper to stop its loop
            self.rotation_helper = None  # Clear the reference to allow memory release
        self.mutex.unlock()

    def clean_up(self):
        """Force cleanup by ensuring the instance is fully cleared."""
        print("Cleaning up RotationHelper...")
        self.mutex.lock()
        self.rotation_helper = None  # Clear any remaining reference
        self.mutex.unlock()
        print("RotationHelper Clean Done")
