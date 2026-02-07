import cv2
import os
from pathlib import Path
from ai_engine import AIEngine
from cache_manager import CacheManager
import image_utils


class ImageProcessor:
    def __init__(self, source_dir):
        self.source_dir = Path(source_dir)
        self.ai = AIEngine()
        self.cache = CacheManager(source_dir)
        self.blur_threshold = 100.0

    def process_directory(self, progress_callback=None):
        exts = (".jpg", ".jpeg", ".png", ".webp")
        files = [f for f in self.source_dir.iterdir() if f.suffix.lower() in exts]

        results = {"blur": [], "dups": {}, "ugly": []}

        for i, f in enumerate(files):
            data = self.cache.get(f)
            if not data:
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
                    "hash": image_utils.get_perceptual_hash(gray),
                }
                self.cache.set(f, data)

            # Categorize
            path_obj, score = Path(data["path"]), data["aesthetic"]
            if data["blur"] < self.blur_threshold:
                results["blur"].append((path_obj, score))
            if score < 4.5:
                results["ugly"].append((path_obj, score))
            results["dups"].setdefault(data["hash"], []).append((path_obj, score))

            if progress_callback:
                progress_callback(int(((i + 1) / len(files)) * 100))

        self.cache.save()

        # Clean up duplicates (only return groups > 1)
        final_dups = [
            sorted(g, key=lambda x: x[1], reverse=True)
            for g in results["dups"].values()
            if len(g) > 1
        ]

        return results["blur"], final_dups, results["ugly"]
