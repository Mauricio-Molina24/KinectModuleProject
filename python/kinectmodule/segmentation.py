# segmentation.py

from ultralytics import YOLO
import numpy as np

if __package__:
    from .config import MODEL_PATH, IMAGE_SIZE, CONFIDENCE, IOU, DEVICE, QUANTIZE
else:
    # Permite importar esta clase cuando main.py se ejecuta directamente.
    from config import MODEL_PATH, IMAGE_SIZE, CONFIDENCE, IOU, DEVICE, QUANTIZE


class InstanceSegmenter:

    def __init__(self):
        print("Cargando modelo YOLO...")

        self.model = YOLO(MODEL_PATH)

        print("Modelo cargado correctamente.")

    def predict(self, image):

        results = self.model.predict(
            source=image,
            imgsz=IMAGE_SIZE,
            conf=CONFIDENCE,
            iou=IOU,
            device=DEVICE,
            quantize=QUANTIZE,
            retina_masks=True,
            verbose=False
        )

        result = results[0]

        # Recuperar máscaras individuales
        if result.masks is not None:
            masks = result.masks.data.cpu().numpy()
            masks = masks.astype(np.uint8)
        else:
            masks = np.empty(
                (0, image.shape[0], image.shape[1]),
                dtype=np.uint8
            )

        # Comprobar dimensiones
        expected_shape = image.shape[:2]

        if masks.shape[1:] != expected_shape:
            raise RuntimeError(
                f"Dimensiones incorrectas: {masks.shape[1:]}, "
                f"esperadas: {expected_shape}"
            )

        return result, masks
