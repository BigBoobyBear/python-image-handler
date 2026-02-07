# 📸 AI Smart Image Handler

An AI-powered image curation tool optimized for **Apple Silicon (M1 Pro/Max/Ultra)**. This application uses the **NIMA (Neural Image Assessment)** model to automatically score your photos, detect blur, and group duplicates, allowing you to clean up your library with a professional, keyboard-driven workflow.

---

## ✨ Key Features

- **Metal Accelerated:** Utilizes the M1 Pro GPU via TensorFlow's Metal plugin for high-speed AI inference.
- **AI Aesthetic Scoring:** Automatically ranks images on a scale of 1–10 based on technical and artistic quality.
- **Intelligent Grouping:** \* **Duplicates:** Groups identical or near-identical photos and highlights the best version.
- **Blur Detection:** Identifies out-of-focus shots using Laplacian variance.
- **Low Quality:** Filters out "ugly" or poorly composed images.

- **Smart Caching:** Saves AI scores in a hidden `.nima_cache.json` to skip redundant calculations on subsequent runs.
- **Pro Carousel UI:** A distraction-free, "contained" view that maintains image aspect ratios and supports a full-screen review experience.

---

## 🚀 Installation (macOS)

### 1. Requirements

- Python 3.10+
- macOS 12.0+ (for Metal support)

### 2. Setup Environment

```bash
# Install dependencies
pip install tensorflow-metal tensorflow-macos opencv-python PyQt5 send2trash numpy

```

### 3. Run

```bash
python main.py

```

---

## ⌨️ Keyboard Shortcuts (Pro Workflow)

The app is designed to be used without a mouse for maximum efficiency:

| Key           | Action                                                                  |
| ------------- | ----------------------------------------------------------------------- |
| ** / **       | Navigate through tasks (Carousel)                                       |
| **Space**     | Open current group in **macOS Preview**                                 |
| **Enter**     | **Keep Best Version** (Trashes all duplicates except the highest score) |
| **Backspace** | **Delete** the currently focused image                                  |
| **Esc**       | Close the review modal                                                  |

---

## 🛠 Tech Stack

- **Core:** Python 3
- **AI Model:** MobileNetV2 (Backbone) + NIMA Head (Dense Layer)
- **Acceleration:** `tensorflow-metal` (Apple GPU)
- **UI Framework:** PyQt5
- **Image Processing:** OpenCV (Blur & Phash)
- **File Handling:** `send2trash` (Safe deletion to system bin)

---

## 📁 Project Structure

- `main.py`: Entry point and directory selection.
- `logic.py`: The AI "Brain" — handles GPU inference, blur detection, and hashing.
- `review_modal.py`: The main UI controller and carousel logic.
- `image_card.py`: The individual image component with aspect-ratio-aware "contain" scaling.

---

## ⚖️ License

MIT

---

**Would you like me to add a section on how to "tune" the AI sensitivity (e.g., changing what the app considers "blurry") to the README?**
