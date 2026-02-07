import cv2
import numpy as np


def get_blur_score(gray_img):
    return float(cv2.Laplacian(gray_img, cv2.CV_64F).var())


def get_perceptual_hash(gray_img):
    """
    Computes a Difference Hash (dHash).
    It tracks gradients, making it robust to brightness/contrast changes.
    """
    resized = cv2.resize(gray_img, (9, 8))
    # Compute difference between adjacent pixels
    diff = resized[:, 1:] > resized[:, :-1]
    return diff.flatten()  # Returns a boolean array for easy comparison


def get_hamming_distance(hash1, hash2):
    """Returns the number of bits that are different."""
    return np.count_nonzero(hash1 != hash2)


def format_size(b):
    for unit in ["", "K", "M", "G"]:
        if b < 1024:
            return f"{b:.1f}{unit}B"
        b /= 1024
    return f"{b:.1f}TB"
