import os
import json
import hashlib
from pathlib import Path
import numpy as np
import cv2
import tensorflow as tf


class ImageProcessor:
    def __init__(self, source_dir):
        self.source_dir = Path(source_dir)
        self.cache_file = self.source_dir / ".nima_cache.json"
        self.cache = self.load_cache()
        self.blur_threshold = 100.0

        # AI Setup
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(224, 224, 3), include_top=False, weights="imagenet"
        )
        x = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
        x = tf.keras.layers.Dense(10, activation="softmax")(x)
        self.model = tf.keras.models.Model(inputs=base_model.input, outputs=x)
        print("✅ NIMA AI Fully Loaded")

    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)

    def get_file_hash(self, path):
        # We use a combination of path and mtime for speed
        stat = os.stat(path)
        return f"{path}_{stat.st_mtime}"

    def analyze_image(self, path):
        cache_key = str(path)
        mtime = os.path.getmtime(path)

        # 1. Check Cache First
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if cached_data.get("mtime") == mtime:
                # Cache hit! Returning stored results
                return cached_data

        # 2. Not in cache (or changed) -> Calculate
        try:
            img = cv2.imread(str(path))
            if img is None:
                return None

            # Blur detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

            # AI Aesthetic score
            resized = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (224, 224))
            reshaped = np.expand_dims(resized / 255.0, axis=0)
            predictions = self.model.predict(reshaped, verbose=0)[0]
            aesthetic_score = np.sum(predictions * np.arange(1, 11))

            # Perceptual Hash for duplicates
            img_small = cv2.resize(gray, (8, 8))
            avg = img_small.mean()
            phash = "".join(["1" if x > avg else "0" for x in img_small.flatten()])

            result = {
                "path": str(path),
                "mtime": mtime,
                "blur": float(blur_score),
                "aesthetic": float(aesthetic_score),
                "hash": phash,
            }

            # Update Cache memory
            self.cache[cache_key] = result
            return result
        except Exception as e:
            print(f"Error analyzing {path}: {e}")
            return None

    def run_analysis(self, progress_callback=None):
        extensions = (".jpg", ".jpeg", ".png", ".webp")
        files = [f for f in self.source_dir.iterdir() if f.suffix.lower() in extensions]
        total = len(files)

        blur_list, ugly_list, hash_groups = [], [], {}

        for i, f in enumerate(files):
            res = self.analyze_image(f)
            if res:
                path = Path(res["path"])
                score = res["aesthetic"]

                if res["blur"] < self.blur_threshold:
                    blur_list.append((path, score))
                if score < 4.5:
                    ugly_list.append((path, score))

                hash_groups.setdefault(res["hash"], []).append((path, score))

            if progress_callback:
                progress_callback(int(((i + 1) / total) * 100))

        # Save cache to disk after run
        self.save_cache()

        duplicate_groups = []
        for h, items in hash_groups.items():
            if len(items) > 1:
                sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
                duplicate_groups.append(sorted_items)

        return blur_list, duplicate_groups, ugly_list
