import tensorflow as tf
import numpy as np
import cv2


class AIEngine:
    def __init__(self):
        # Setup MobileNetV2 with NIMA head
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(224, 224, 3), include_top=False, weights="imagenet"
        )
        x = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
        x = tf.keras.layers.Dense(10, activation="softmax")(x)
        self.model = tf.keras.models.Model(inputs=base_model.input, outputs=x)
        print("✅ Metal GPU AI Engine Initialized")

    def predict_score(self, rgb_img):
        resized = cv2.resize(rgb_img, (224, 224))
        reshaped = np.expand_dims(resized / 255.0, axis=0)
        predictions = self.model.predict(reshaped, verbose=0)[0]
        # Calculate mean score: Sum of (probability * bucket_index)
        return float(np.sum(predictions * np.arange(1, 11)))
