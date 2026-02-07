import cv2
import numpy as np


def get_blur_score(gray_img):
    return float(cv2.Laplacian(gray_img, cv2.CV_64F).var())


def get_perceptual_hash(gray_img):
    img_small = cv2.resize(gray_img, (8, 8))
    avg = img_small.mean()
    return "".join(["1" if x > avg else "0" for x in img_small.flatten()])


def format_size(b):
    for unit in ["", "K", "M", "G"]:
        if b < 1024:
            return f"{b:.1f}{unit}B"
        b /= 1024
    return f"{b:.1f}TB"
