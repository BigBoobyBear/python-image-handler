import os
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QHBoxLayout,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import image_utils


class ImageCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, path, delete_callback, score=None):
        super().__init__()
        self.path = path
        self.delete_callback = delete_callback
        self.score = score
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.img_label.setScaledContents(False)

        self.pixmap = QPixmap(str(self.path))
        self._rescale()

        pill = QLabel(
            f"{self.path.name[:15]} • ★ {self.score:.1f} • {image_utils.format_size(os.path.getsize(self.path))}"
        )
        pill.setStyleSheet(
            "background: #333; color: #ddd; border-radius: 12px; padding: 5px; font-size: 10px;"
        )
        pill.setAlignment(Qt.AlignCenter)

        self.btn_del = QPushButton("DELETE")
        self.btn_del.setFixedSize(140, 40)
        self.btn_del.setStyleSheet(
            "background: #c0392b; color: white; border-radius: 20px; font-weight: bold;"
        )
        self.btn_del.clicked.connect(lambda: self.delete_callback(self.path, self))

        layout.addWidget(self.img_label, stretch=1)
        layout.addWidget(pill, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_del, alignment=Qt.AlignCenter)
        self.setStyleSheet(
            "background: #181818; border-radius: 15px; border: 1px solid #252525;"
        )

    def _rescale(self):
        if not self.pixmap.isNull() and self.img_label.size().isValid():
            self.img_label.setPixmap(
                self.pixmap.scaled(
                    self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

    def resizeEvent(self, event):
        self._rescale()
        super().resizeEvent(event)
