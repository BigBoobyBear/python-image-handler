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
    QScrollArea,
    QGridLayout,
    QMessageBox,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from image_card import ImageCard
from send2trash import send2trash


class AnalysisWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, list)

    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def run(self):
        blur, dups = self.processor.run_analysis(self.progress.emit)
        self.finished.emit(blur, dups)


class ReviewModal(QMainWindow):
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.tasks = []
        self.current_idx = 0
        self.setWindowTitle("Python Image Handler - Review")
        self.resize(1200, 850)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        self.init_ui()
        self.start_analysis()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)

        self.header = QLabel("Scanning files... Please wait.")
        self.header.setStyleSheet("font-size: 16px; font-weight: bold; color: #f1c40f;")
        self.header.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            """
            QProgressBar { border: 1px solid #333; border-radius: 5px; text-align: center; height: 25px; }
            QProgressBar::chunk { background-color: #2ecc71; }
        """
        )
        self.main_layout.addWidget(self.progress_bar)

        self.btn_merge = QPushButton("⚡ AUTO-CLEAN (Keep Largest File)")
        self.btn_merge.setVisible(False)
        self.btn_merge.setStyleSheet(
            "background: #27ae60; color: white; font-weight: bold; height: 40px;"
        )
        self.btn_merge.clicked.connect(self.auto_merge_group)  # Connection verified
        self.main_layout.addWidget(self.btn_merge)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        self.scroll_content = QWidget()
        self.grid = QGridLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll)

        self.nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("← Previous Task")
        self.btn_next = QPushButton("Next Task →")
        for b in [self.btn_prev, self.btn_next]:
            b.setEnabled(False)
            b.setStyleSheet("height: 40px; background: #34495e; color: white;")
            b.clicked.connect(
                lambda checked, d=(-1 if b == self.btn_prev else 1): self.navigate(d)
            )
        self.nav_layout.addWidget(self.btn_prev)
        self.nav_layout.addWidget(self.btn_next)
        self.main_layout.addLayout(self.nav_layout)

    def start_analysis(self):
        self.worker = AnalysisWorker(self.processor)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.start()

    def on_analysis_finished(self, blur_list, duplicate_groups):
        self.progress_bar.hide()
        for p in blur_list:
            self.tasks.append({"type": "BLURRY", "paths": [p]})
        for paths in duplicate_groups:
            self.tasks.append({"type": "DUPLICATE", "paths": paths})

        self.btn_prev.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.render_task()

    def render_task(self):
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not self.tasks:
            self.header.setText("🎉 All tasks completed!")
            self.btn_merge.hide()
            return

        task = self.tasks[self.current_idx]
        self.header.setText(
            f"Task {self.current_idx + 1}/{len(self.tasks)}: {task['type']} ({len(task['paths'])} items)"
        )
        self.btn_merge.setVisible(task["type"] == "DUPLICATE")

        for i, path in enumerate(task["paths"]):
            card = ImageCard(path, self.handle_delete)
            card.clicked.connect(self.open_current_group_preview)
            self.grid.addWidget(card, i // 3, i % 3)

    def open_current_group_preview(self):
        """Opens all images in the current task group using the system app."""
        if not self.tasks:
            return
        paths = [str(p) for p in self.tasks[self.current_idx]["paths"]]
        try:
            if platform.system() == "Darwin":
                subprocess.run(["open", "-a", "Preview"] + paths)
            elif platform.system() == "Windows":
                for p in paths:
                    os.startfile(p)
            else:
                subprocess.run(["xdg-open"] + paths)
        except Exception as e:
            QMessageBox.warning(
                self, "Preview Error", f"Could not open system preview: {e}"
            )

    def handle_delete(self, path, card_widget):
        try:
            send2trash(str(path))
            task = self.tasks[self.current_idx]
            if path in task["paths"]:
                task["paths"].remove(path)
            card_widget.deleteLater()
            self.check_task_completion()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not delete: {e}")

    def auto_merge_group(self):
        """Implementation of the missing merge function."""
        if not self.tasks:
            return
        task = self.tasks[self.current_idx]
        if task["type"] != "DUPLICATE":
            return

        # Sort by size and keep largest
        sorted_files = sorted(
            task["paths"], key=lambda p: p.stat().st_size, reverse=True
        )
        for p in sorted_files[1:]:
            if p.exists():
                send2trash(str(p))

        self.tasks.pop(self.current_idx)
        # Ensure index stays in range
        if self.current_idx >= len(self.tasks) and self.tasks:
            self.current_idx = 0
        self.render_task()

    def check_task_completion(self):
        if not self.tasks:
            return
        task = self.tasks[self.current_idx]
        if not task["paths"] or (
            task["type"] == "DUPLICATE" and len(task["paths"]) < 2
        ):
            self.tasks.pop(self.current_idx)
            if self.current_idx >= len(self.tasks) and self.tasks:
                self.current_idx = 0
            self.render_task()

    def navigate(self, direction):
        if not self.tasks:
            return
        self.current_idx = (self.current_idx + direction) % len(self.tasks)
        self.render_task()
