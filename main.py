import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from image_processor import ImageProcessor
from review_modal import ReviewModal


def main():
    app = QApplication(sys.argv)

    # Hardcoded path logic
    base_path = Path(__file__).parent / "my_photos"

    if not base_path.exists():
        QMessageBox.critical(
            None, "Folder Missing", f"Could not find folder: {base_path}"
        )
        return

    processor = ImageProcessor(base_path)
    window = ReviewModal(processor)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
