import tensorflow as tf
import sys

print(f"Python version: {sys.version}")
print("Num GPUs Available: ", len(tf.config.list_physical_devices("GPU")))
