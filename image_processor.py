import cv2
import os
import numpy as np
from pathlib import Path
from ai_engine import AIEngine
from cache_manager import CacheManager
import image_utils


class ImageProcessor:
    def __init__(self, source_dir):
        self.source_dir = Path(source_dir)
        self.ai = AIEngine()
        self.cache = CacheManager(source_dir)
        self.similarity_threshold = 5
        self.blur_threshold = 110.0
        self.aesthetic_cutoff = 4.5

    def run_analysis(self, progress_callback=None):
        exts = (".jpg", ".jpeg", ".png", ".webp")
        files = [f for f in self.source_dir.iterdir() if f.suffix.lower() in exts]

        for i, f in enumerate(files):
            if not self.cache.get(f):
                img = cv2.imread(str(f))
                if img is None:
                    continue
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                data = {
                    "path": str(f),
                    "mtime": os.path.getmtime(f),
                    "blur": image_utils.get_blur_score(gray),
                    "aesthetic": self.ai.predict_score(rgb),
                    "hash": image_utils.get_perceptual_hash(gray).tolist(),
                }
                self.cache.set(f, data)
            if progress_callback:
                progress_callback(int(((i + 1) / len(files)) * 100))

        self.cache.save()
        return self.recluster(self.similarity_threshold)

    def recluster(self, harshness):
        self.similarity_threshold = harshness
        self.blur_threshold = 75 + (harshness * 8)
        self.aesthetic_cutoff = 3.5 + (harshness * 0.2)

        data_list = list(self.cache.data.values())
        groups = []

        # 1. Structural Grouping
        for item in data_list:
            item_hash = np.array(item["hash"])
            matched = False
            for group in groups:
                target_hash = np.array(group[0]["hash"])
                dist = np.count_nonzero(item_hash != target_hash)
                if dist <= self.similarity_threshold:
                    group.append(item)
                    matched = True
                    break
            if not matched:
                groups.append([item])

        # 2. Priority Filtering (Remove Redundancy)
        duplicate_groups = []
        blur_list = []
        ugly_list = []
        assigned_paths = set()

        # Priority 1: Duplicates (Groups)
        for group in groups:
            if len(group) > 1:
                sorted_group = sorted(group, key=lambda x: x["aesthetic"], reverse=True)
                paths = [(Path(x["path"]), x["aesthetic"]) for x in sorted_group]
                duplicate_groups.append(paths)
                for p, _ in paths:
                    assigned_paths.add(str(p))

        # Priority 2 & 3: Individual Blurry or Low Quality
        for item in data_list:
            path_str = item["path"]
            if path_str in assigned_paths:
                continue  # Skip if already in a duplicate group

            p, s = Path(path_str), item["aesthetic"]
            if item["blur"] < self.blur_threshold:
                blur_list.append((p, s))
                assigned_paths.add(path_str)
            elif s < self.aesthetic_cutoff:
                ugly_list.append((p, s))
                assigned_paths.add(path_str)

        return blur_list, duplicate_groups, ugly_list
