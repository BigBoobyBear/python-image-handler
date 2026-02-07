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


class ImageCard(QWidget):
    clicked = pyqtSignal()

    def __init__(self, path, delete_callback, score=None):
        super().__init__()
        self.path = path
        self.delete_callback = delete_callback
        self.score = score
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def get_size_format(self, b):
        for unit in ["", "K", "M", "G"]:
            if b < 1024:
                return f"{b:.1f}{unit}B"
            b /= 1024
        return f"{b:.1f}TB"

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Image Container (CSS 'contain' equivalent)
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)

        # 'Ignored' allows the label to be smaller than the pixmap,
        # which is necessary for the layout to dictate the size.
        self.img_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        # MUST BE FALSE to prevent the 'zoom/stretch' effect
        self.img_label.setScaledContents(False)

        self.pixmap = QPixmap(str(self.path))
        if not self.pixmap.isNull():
            # Initial scale - logic in resizeEvent would be ideal,
            # but this bounding box scale works for static grids.
            self.update_pixmap()

        # 2. Pill Metadata
        pill_row = QHBoxLayout()
        pill_row.addStretch()

        name_txt = (
            self.path.name[:12] + ".." if len(self.path.name) > 12 else self.path.name
        )
        score_val = f"{self.score:.1f}" if self.score else "N/A"

        meta_pill = QLabel(
            f"{name_txt}  •  ★ {score_val}  •  {self.get_size_format(os.path.getsize(self.path))}"
        )
        meta_pill.setStyleSheet(
            """
            background: #333; 
            color: #ddd; 
            border-radius: 12px; 
            padding: 5px 15px; 
            font-size: 10px;
        """
        )
        pill_row.addWidget(meta_pill)
        pill_row.addStretch()

        # 3. Delete Button
        btn_row = QHBoxLayout()
        self.btn_del = QPushButton("DELETE")
        self.btn_del.setFixedWidth(120)
        self.btn_del.setFixedHeight(36)
        self.btn_del.setStyleSheet(
            """
            QPushButton { 
                background: #c0392b; color: white; border-radius: 18px; 
                font-weight: bold; font-size: 11px; border: none;
            }
            QPushButton:hover { background: #e74c3c; }
        """
        )
        self.btn_del.clicked.connect(lambda: self.delete_callback(self.path, self))
        btn_row.addStretch()
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()

        layout.addWidget(self.img_label, stretch=1)
        layout.addLayout(pill_row)
        layout.addLayout(btn_row)

        self.setStyleSheet(
            "background-color: #181818; border-radius: 15px; border: 1px solid #252525;"
        )

    def update_pixmap(self):
        """Ensures the image is contained within the label dimensions."""
        if not self.pixmap.isNull():
            # We scale to a very large size but KeepAspectRatio
            # The label's 'Ignored' policy handles the actual clipping/containment
            self.img_label.setPixmap(
                self.pixmap.scaled(
                    1200, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

    def resizeEvent(self, event):
        """Dynamic resizing to keep images 'contained' when window scales."""
        super().resizeEvent(event)
        if hasattr(self, "pixmap") and not self.pixmap.isNull():
            # Shrink the image to fit the new label size minus some padding
            w = self.img_label.width()
            h = self.img_label.height()
            if w > 0 and h > 0:
                self.img_label.setPixmap(
                    self.pixmap.scaled(
                        w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
