import os
import subprocess
import platform
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QProgressBar,
    QMessageBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from image_card import ImageCard
from send2trash import send2trash


class AnalysisWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, list, list)

    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def run(self):
        blur, dups, ugly = self.processor.run_analysis(self.progress.emit)
        self.finished.emit(blur, dups, ugly)


class ReviewModal(QMainWindow):
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.tasks = []
        self.current_idx = 0
        self.showMaximized()
        self.setStyleSheet("background-color: #050505; color: white;")
        self.init_ui()
        self.start_analysis()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.carousel_layout = QHBoxLayout(central_widget)
        self.carousel_layout.setContentsMargins(0, 0, 0, 0)
        self.carousel_layout.setSpacing(0)

        # 1. Left Nav
        self.btn_left = QPushButton("❮")
        self.setup_nav_button(self.btn_left, -1)
        self.carousel_layout.addWidget(self.btn_left)

        # 2. Content
        content_container = QWidget()
        self.main_layout = QVBoxLayout(content_container)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.header = QLabel("AI Analysis...")
        self.header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFixedHeight(30)
        self.main_layout.addWidget(self.header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: none; background: #111; } QProgressBar::chunk { background: #27ae60; }"
        )
        self.main_layout.addWidget(self.progress_bar)

        self.btn_merge = QPushButton("⚡ KEEP BEST VERSION (ENTER)")
        self.btn_merge.setVisible(False)
        self.btn_merge.setFixedHeight(40)
        self.btn_merge.setStyleSheet(
            "background: #27ae60; color: white; border-radius: 20px; font-weight: bold; font-size: 12px;"
        )
        self.btn_merge.clicked.connect(self.auto_merge_group)
        self.main_layout.addWidget(self.btn_merge)

        self.image_display_area = QWidget()
        self.image_display_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.grid = QGridLayout(self.image_display_area)
        self.grid.setSpacing(15)
        self.main_layout.addWidget(self.image_display_area, stretch=1)

        self.carousel_layout.addWidget(content_container, stretch=1)

        # 3. Right Nav
        self.btn_right = QPushButton("❯")
        self.setup_nav_button(self.btn_right, 1)
        self.carousel_layout.addWidget(self.btn_right)

    def setup_nav_button(self, btn, direction):
        btn.setFixedWidth(50)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            """
            QPushButton { 
                background: transparent; 
                color: #222; 
                font-size: 40px; 
                border: none; 
                outline: none; 
            } 
            QPushButton:hover { color: #f1c40f; }
        """
        )
        btn.clicked.connect(lambda: self.navigate(direction))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if not self.tasks:
            return

        if event.key() == Qt.Key_Left:
            self.navigate(-1)
        elif event.key() == Qt.Key_Right:
            self.navigate(1)
        elif event.key() == Qt.Key_Space:
            self.open_current_group_preview()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.tasks[self.current_idx]["type"] == "DUPLICATE GROUP":
                self.auto_merge_group()
        elif event.key() == Qt.Key_Backspace:
            task = self.tasks[self.current_idx]
            if task["type"] != "DUPLICATE GROUP" and task["paths"]:
                self.handle_delete(task["paths"][0][0], None)

    def start_analysis(self):
        self.worker = AnalysisWorker(self.processor)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.start()

    def on_analysis_finished(self, blur, dups, ugly):
        self.progress_bar.hide()
        for p, s in blur:
            self.tasks.append({"type": "BLURRY IMAGE", "paths": [(p, s)]})
        for p, s in ugly:
            self.tasks.append({"type": "LOW QUALITY", "paths": [(p, s)]})
        for group in dups:
            self.tasks.append({"type": "DUPLICATE GROUP", "paths": group})
        self.render_task()

    def render_task(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.tasks:
            self.header.setText("🎉 Clean!")
            self.btn_merge.hide()
            return

        task = self.tasks[self.current_idx]
        self.header.setText(
            f"{task['type']} | {self.current_idx + 1} of {len(self.tasks)}"
        )
        self.btn_merge.setVisible(task["type"] == "DUPLICATE GROUP")

        paths_data = task["paths"]
        num = len(paths_data)
        cols = 2 if num > 1 else 1

        for i, (path, score) in enumerate(paths_data):
            card = ImageCard(path, self.handle_delete, score)
            card.clicked.connect(self.open_current_group_preview)
            self.grid.addWidget(card, i // cols, i % cols)

    def open_current_group_preview(self):
        paths = [str(p[0]) for p in self.tasks[self.current_idx]["paths"]]
        if platform.system() == "Darwin":
            subprocess.run(["open", "-a", "Preview"] + paths)

    def handle_delete(self, path, card_widget):
        try:
            send2trash(str(path))
            task = self.tasks[self.current_idx]
            task["paths"] = [item for item in task["paths"] if item[0] != path]
            if card_widget:
                card_widget.deleteLater()

            if not task["paths"] or (
                task["type"] == "DUPLICATE GROUP" and len(task["paths"]) < 2
            ):
                self.tasks.pop(self.current_idx)
                self.navigate(0)
            elif not card_widget:
                self.render_task()
        except Exception as e:
            print(f"Delete error: {e}")

    def auto_merge_group(self):
        task = self.tasks[self.current_idx]
        for item in task["paths"][1:]:
            p = item[0]
            if p.exists():
                send2trash(str(p))
        self.tasks.pop(self.current_idx)
        self.navigate(0)

    def navigate(self, direction):
        if not self.tasks:
            return
        self.current_idx = (self.current_idx + direction) % len(self.tasks)
        self.render_task()
