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

        self.pixmap = QPixmap(str(self.path))
        self._update_image()

        meta_txt = f"{self.path.name[:10]}.. • ★ {self.score:.1f} • {image_utils.format_size(os.path.getsize(self.path))}"
        self.pill = QLabel(meta_txt)
        self.pill.setStyleSheet(
            "background: #333; color: #ddd; border-radius: 12px; padding: 5px; font-size: 10px;"
        )
        self.pill.setAlignment(Qt.AlignCenter)

        self.btn_del = QPushButton("DELETE")
        self.btn_del.setFixedSize(120, 35)
        self.btn_del.setStyleSheet(
            "background: #c0392b; color: white; border-radius: 17px; font-weight: bold;"
        )
        self.btn_del.clicked.connect(lambda: self.delete_callback(self.path, self))

        layout.addWidget(self.img_label, stretch=1)
        layout.addWidget(self.pill)
        layout.addWidget(self.btn_del, alignment=Qt.AlignCenter)
        self.setStyleSheet(
            "background: #181818; border-radius: 15px; border: 1px solid #252525;"
        )

    def _update_image(self):
        if not self.pixmap.isNull():
            self.img_label.setPixmap(
                self.pixmap.scaled(
                    self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

    def resizeEvent(self, event):
        self._update_image()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
