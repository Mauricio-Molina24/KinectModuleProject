from pathlib import Path
import time

from kinectmodule import KinectWrapper
from ultralytics import YOLO


def main():
    # Este peso de segmentación ya está incluido en la carpeta kinectmodule.
    model_path = Path(__file__).parent / "kinectmodule" / "yolov8n-seg.pt"
    model = YOLO(str(model_path))

    kinect = KinectWrapper()
    if not kinect.initialize():
        raise RuntimeError(kinect.get_last_error())

    try:
        # El Kinect puede tardar un momento en empezar a producir frames.
        time.sleep(1.0)
        while True:
            # La función devuelve un frame BGR, listo para pasarlo a YOLO.
            rgb = kinect.get_color_frame_bgr()
            if rgb is None:
                print("No se pudo obtener el frame:", kinect.get_last_error())
                time.sleep(0.1)
                continue

            results = model.predict(source=rgb, verbose=False)
            # Aquí puedes usar o mostrar results.
    finally:
        kinect.shutdown()


if __name__ == "__main__":
    main()
