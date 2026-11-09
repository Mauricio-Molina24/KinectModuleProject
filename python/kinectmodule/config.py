from pathlib import Path
import torch

# El peso está junto a este archivo dentro del paquete kinectmodule.
MODEL_PATH = Path(__file__).resolve().parent / "yolov8n-seg.pt"

IMAGE_SIZE = 640
CONFIDENCE = 0.50
IOU = 0.45

HAS_CUDA = torch.cuda.is_available()
DEVICE = 0 if HAS_CUDA else "cpu"
QUANTIZE = 16 if HAS_CUDA else None  # FP16 solo en GPU CUDA.
MIN_VALID_DEPTH_PIXELS = 5
