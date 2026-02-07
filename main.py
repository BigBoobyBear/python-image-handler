import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from logic import ImageProcessor
from review_modal import ReviewModal


def main():
    app = QApplication(sys.argv)

    # Configuration
    SOURCE_FOLDER = "my_photos"
    BLUR_THRESHOLD = 100.0

    if not Path(SOURCE_FOLDER).exists():
        QMessageBox.critical(
            None, "Fatal Error", f"Folder '{SOURCE_FOLDER}' not found."
        )
        return

    processor = ImageProcessor(SOURCE_FOLDER, BLUR_THRESHOLD)
    window = ReviewModal(processor)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
