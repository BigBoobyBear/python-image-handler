import cv2
import imagehash
import logging
from PIL import Image
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ImageProcessor:
    def __init__(self, source_dir, blur_threshold=100.0):
        self.source_dir = Path(source_dir)
        self.blur_threshold = blur_threshold

    def analyze_image(self, img_path):
        try:
            image = cv2.imread(str(img_path))
            if image is None:
                return None

            # Normalization
            height, width = image.shape[:2]
            scale = 1000 / width
            resized = cv2.resize(image, (1000, int(height * scale)))

            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

            with Image.open(img_path) as img:
                img_hash = str(imagehash.phash(img))

            return img_path, blur_score, img_hash
        except Exception as e:
            logging.error(f"Failed to process {img_path}: {e}")
            return None

    def run_analysis(self, progress_callback=None):
        extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        files = [f for f in self.source_dir.iterdir() if f.suffix.lower() in extensions]
        total = len(files)

        blur_list = []
        hash_groups = {}

        if total == 0:
            return [], []

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.analyze_image, f): f for f in files}
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                if result:
                    path, score, img_hash = result
                    if score < self.blur_threshold:
                        blur_list.append(path)
                    hash_groups.setdefault(img_hash, []).append(path)

                if progress_callback:
                    progress_callback(int(((i + 1) / total) * 100))

        duplicate_groups = [paths for paths in hash_groups.values() if len(paths) > 1]
        return blur_list, duplicate_groups
