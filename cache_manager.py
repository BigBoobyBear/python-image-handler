import json
import os
from pathlib import Path


class CacheManager:
    def __init__(self, directory):
        self.cache_path = Path(directory) / ".nima_cache.json"
        self.data = self._load()

    def _load(self):
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def get(self, filepath):
        path_str = str(filepath)
        if path_str in self.data:
            mtime = os.path.getmtime(filepath)
            if self.data[path_str].get("mtime") == mtime:
                return self.data[path_str]
        return None

    def set(self, filepath, result):
        self.data[str(filepath)] = result

    def save(self):
        with open(self.cache_path, "w") as f:
            json.dump(self.data, f)
