from pathlib import Path

# El peso está junto a este archivo dentro del paquete kinectmodule.
MODEL_PATH = Path(__file__).resolve().parent / "yolov8n-seg.pt"

IMAGE_SIZE = 640
CONFIDENCE = 0.50
IOU = 0.45

DEVICE = 0       # GPU NVIDIA
QUANTIZE = 16    # Inferencia FP16 en GPU; sustituye al argumento obsoleto half.
MIN_VALID_DEPTH_PIXELS = 5
