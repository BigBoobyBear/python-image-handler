import urllib.request
from pathlib import Path


def download_weights():
    # This is a direct weight file from a verified NIMA implementation
    url = "https://github.com/titu1994/neural-image-assessment/releases/download/v0.1/mobilenet_weights.h5"
    dest = Path("nima_mobilenet_v2.h5")

    try:
        print(f"Downloading stable NIMA weights...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(dest, "wb") as out_file:
            out_file.write(response.read())

        if dest.exists():
            print(f"✅ Downloaded: {dest.stat().st_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    download_weights()
