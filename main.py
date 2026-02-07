import sys
import tensorflow as tf
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from logic import ImageProcessor
from review_modal import ReviewModal


def check_gpu():
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        print(f"✅ Metal GPU Detected: {gpus}")
    else:
        print(
            "⚠️ Running on CPU. For faster NIMA analysis, ensure tensorflow-metal is installed."
        )


def main():
    app = QApplication(sys.argv)
    check_gpu()

    # Configuration
    SOURCE_FOLDER = "my_photos"  # Ensure this folder exists

    if not Path(SOURCE_FOLDER).exists():
        QMessageBox.critical(
            None, "Fatal Error", f"Folder '{SOURCE_FOLDER}' not found."
        )
        return

    processor = ImageProcessor(SOURCE_FOLDER)
    window = ReviewModal(processor)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
