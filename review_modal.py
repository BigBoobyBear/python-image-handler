from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QProgressBar,
    QSizePolicy,
    QSlider,
    QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from image_card import ImageCard
from send2trash import send2trash
import image_utils
import os


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

        self.btn_left = QPushButton("❮")
        self.setup_nav_button(self.btn_left, -1)
        self.btn_right = QPushButton("❯")
        self.setup_nav_button(self.btn_right, 1)

        content_container = QWidget()
        self.main_layout = QVBoxLayout(content_container)

        # Control Bar
        self.control_bar = QFrame()
        self.control_bar.setStyleSheet(
            "background: #111; border-radius: 10px; margin: 10px;"
        )
        control_layout = QHBoxLayout(self.control_bar)

        self.slider_label = QLabel("HARSHNESS: 5")
        self.slider_label.setStyleSheet(
            "font-weight: bold; color: #f1c40f; font-size: 11px;"
        )
        self.harsh_slider = QSlider(Qt.Horizontal)
        self.harsh_slider.setRange(0, 20)
        self.harsh_slider.setValue(5)
        self.harsh_slider.setFixedWidth(150)
        self.harsh_slider.sliderReleased.connect(self.update_harshness)

        self.stats_label = QLabel("Potential Savings: 0B")
        self.stats_label.setStyleSheet(
            "color: #27ae60; font-weight: bold; font-size: 11px; margin-left: 20px;"
        )

        control_layout.addStretch()
        control_layout.addWidget(self.slider_label)
        control_layout.addWidget(self.harsh_slider)
        control_layout.addWidget(self.stats_label)
        control_layout.addStretch()
        self.main_layout.addWidget(self.control_bar)

        self.header = QLabel("AI REVIEW")
        self.header.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.header.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.main_layout.addWidget(self.progress_bar)

        self.btn_merge = QPushButton("⚡ KEEP BEST VERSION (ENTER)")
        self.btn_merge.setVisible(False)
        self.btn_merge.setFixedHeight(45)
        self.btn_merge.setStyleSheet(
            "background: #27ae60; color: white; border-radius: 22px; font-weight: bold; font-size: 13px;"
        )
        self.btn_merge.clicked.connect(self.auto_merge_group)
        self.main_layout.addWidget(self.btn_merge)

        self.image_display_area = QWidget()
        self.grid = QGridLayout(self.image_display_area)
        self.grid.setSpacing(20)
        self.main_layout.addWidget(self.image_display_area, stretch=1)

        self.carousel_layout.addWidget(self.btn_left)
        self.carousel_layout.addWidget(content_container, stretch=1)
        self.carousel_layout.addWidget(self.btn_right)

    def setup_nav_button(self, btn, direction):
        btn.setFixedWidth(70)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        btn.setStyleSheet(
            "QPushButton { background: transparent; color: #333; font-size: 45px; border: none; } QPushButton:hover { color: #f1c40f; }"
        )
        btn.clicked.connect(lambda: self.navigate(direction))

    def update_harshness(self):
        val = self.harsh_slider.value()
        self.slider_label.setText(f"HARSHNESS: {val}")
        blur, dups, ugly = self.processor.recluster(val)
        self.on_analysis_finished(blur, dups, ugly)

    def start_analysis(self):
        self.worker = AnalysisWorker(self.processor)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.start()

    def update_stats(self):
        total_bytes = 0
        for task in self.tasks:
            if task["type"] == "DUPLICATES":
                for path, _ in task["paths"][1:]:
                    if path.exists():
                        total_bytes += os.path.getsize(path)
            else:
                for path, _ in task["paths"]:
                    if path.exists():
                        total_bytes += os.path.getsize(path)
        self.stats_label.setText(
            f"Potential Savings: {image_utils.format_size(total_bytes)}"
        )

    def on_analysis_finished(self, blur, dups, ugly):
        self.progress_bar.hide()
        self.tasks = []
        # DUPLICATES first to ensure they take priority in the assigned_paths set
        for group in dups:
            self.tasks.append({"type": "DUPLICATES", "paths": group})
        for p, s in blur:
            self.tasks.append({"type": "BLURRY", "paths": [(p, s)]})
        for p, s in ugly:
            self.tasks.append({"type": "LOW QUALITY", "paths": [(p, s)]})

        self.update_stats()
        self.current_idx = 0
        self.render_task()

    def render_task(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.tasks:
            self.header.setText("🎉 my_photos is clean!")
            self.btn_merge.hide()
            self.update_stats()
            return

        task = self.tasks[self.current_idx]
        self.header.setText(
            f"{task['type']} | {self.current_idx + 1} of {len(self.tasks)}"
        )
        self.btn_merge.setVisible(task["type"] == "DUPLICATES")

        paths = task["paths"]
        cols = 2 if len(paths) > 1 else 1
        for i, (path, score) in enumerate(paths):
            card = ImageCard(path, self.handle_delete, score)
            self.grid.addWidget(card, i // cols, i % cols)

    def navigate(self, direction):
        if not self.tasks:
            return
        self.current_idx = (self.current_idx + direction) % len(self.tasks)
        self.render_task()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if not self.tasks:
            return
        if event.key() == Qt.Key_Left:
            self.navigate(-1)
        elif event.key() == Qt.Key_Right:
            self.navigate(1)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.tasks[self.current_idx]["type"] == "DUPLICATES":
                self.auto_merge_group()
        elif event.key() == Qt.Key_Backspace:
            t = self.tasks[self.current_idx]
            if t["type"] != "DUPLICATES" and t["paths"]:
                self.handle_delete(t["paths"][0][0], None)

    def handle_delete(self, path, card_widget):
        try:
            send2trash(str(path))
            task = self.tasks[self.current_idx]
            task["paths"] = [i for i in task["paths"] if i[0] != path]

            # If a single image task is deleted or a group falls below 2 items
            if not task["paths"] or (
                task["type"] == "DUPLICATES" and len(task["paths"]) < 2
            ):
                self.tasks.pop(self.current_idx)
                if self.current_idx >= len(self.tasks):
                    self.current_idx = 0

            self.render_task()
            self.update_stats()
        except:
            pass

    def auto_merge_group(self):
        task = self.tasks[self.current_idx]
        # Skip index 0 (the best one), trash the rest
        for item in task["paths"][1:]:
            p = item[0]
            if p.exists():
                send2trash(str(p))
        self.tasks.pop(self.current_idx)
        if self.current_idx >= len(self.tasks):
            self.current_idx = 0
        self.render_task()
        self.update_stats()
