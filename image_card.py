from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtCore import Qt, pyqtSignal, QSize


class ImageCard(QWidget):
    # Signal to notify the parent to open the system preview for the group
    clicked = pyqtSignal()

    def __init__(self, path, delete_callback):
        super().__init__()
        self.path = path
        self.delete_callback = delete_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # Image Display
        self.img_label = QLabel()
        self.img_label.setMinimumSize(350, 250)
        self.img_label.setStyleSheet(
            "background-color: #000; border: 1px solid #3d3d3d;"
        )
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setToolTip("Click to preview this group in System App")

        # Load optimized thumbnail
        reader = QImageReader(str(self.path))
        reader.setAutoTransform(True)
        if reader.canRead():
            original_size = reader.size()
            target_size = original_size.scaled(QSize(500, 400), Qt.KeepAspectRatio)
            reader.setScaledSize(target_size)
            image = reader.read()
            if not image.isNull():
                self.img_label.setPixmap(QPixmap.fromImage(image))
        else:
            self.img_label.setText("Unsupported Format")

        # File Info
        size_mb = self.path.stat().st_size / (1024 * 1024)
        info_text = f"<b>{self.path.name}</b><br><span style='color: #bdc3c7;'>{size_mb:.2f} MB</span>"
        self.info_label = QLabel(info_text)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 11px; color: white;")

        # Delete Action
        self.btn_del = QPushButton("Delete This File")
        self.btn_del.setCursor(Qt.PointingHandCursor)
        self.btn_del.setStyleSheet(
            """
            QPushButton { background-color: #e74c3c; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #c0392b; }
        """
        )
        self.btn_del.clicked.connect(lambda: self.delete_callback(self.path, self))

        layout.addWidget(self.img_label, 1)
        layout.addWidget(self.info_label)
        layout.addWidget(self.btn_del)
        self.setStyleSheet("background-color: #2c3e50; border-radius: 8px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
