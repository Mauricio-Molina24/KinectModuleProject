# main.py

import cv2
import time

if __package__:
    from .kinect_wrapper import KinectWrapper
    from .segmentation import InstanceSegmenter
    from .visualization import FrameVisualizer
    from .performance import PerformanceMonitor
    from .depth_estimator import ObjectDistanceEstimator
    from .config import MIN_VALID_DEPTH_PIXELS
else:
    # Permite ejecutar este archivo directamente desde VS Code.
    from kinect_wrapper import KinectWrapper
    from segmentation import InstanceSegmenter
    from visualization import FrameVisualizer
    from performance import PerformanceMonitor
    from depth_estimator import ObjectDistanceEstimator
    from config import MIN_VALID_DEPTH_PIXELS


def main():

    kinect = KinectWrapper()
    segmenter = InstanceSegmenter()
    visualizer = FrameVisualizer(show_depth=False)
    performance = PerformanceMonitor(report_every=30)
    distance_estimator = ObjectDistanceEstimator(
        min_valid_pixels=MIN_VALID_DEPTH_PIXELS
    )

    print("Inicializando Kinect...")

    if not kinect.initialize():
        print("Error:", kinect.get_last_error())
        return

    print("Kinect inicializada correctamente.")

    time.sleep(1)

    try:
        while True:
            loop_start = time.perf_counter()

            # 1. Obtener captura sincronizada
            color, depth, depth_to_color_map = (
                kinect.get_synchronized_frames_depth_to_color(
                    retries=2,
                    retry_delay=0.01,
                )
            )
            capture_ms = (time.perf_counter() - loop_start) * 1000

            if color is None:
                print("Error obteniendo frames:", kinect.get_last_error())
                # En modo en vivo es mejor descartar un frame que esperar mucho.
                time.sleep(0.01)
                continue

            # 2. Convertir BGRA a BGR
            color_bgr = cv2.cvtColor(
                color,
                cv2.COLOR_BGRA2BGR
            )

            # 3. Ejecutar segmentación
            result, masks = segmenter.predict(color_bgr)

            # 4. Estimar la profundidad de cada máscara usando el mapa Kinect.
            object_depths = distance_estimator.estimate(
                depth_mm=depth,
                depth_to_color_map=depth_to_color_map,
                masks=masks,
            )

            # 5. Mostrar detecciones con su distancia estimada.
            key = visualizer.show(color_bgr, depth, result, object_depths)

            # Informar promedios en bloques, evitando imprimir cada frame.
            yolo_ms = sum(result.speed.values())
            total_ms = (time.perf_counter() - loop_start) * 1000
            performance.record(
                capture_ms=capture_ms,
                yolo_ms=yolo_ms,
                cycle_ms=total_ms,
                attempts=kinect.last_depth_to_color_attempts,
                instances=len(masks),
                map_shape=depth_to_color_map.shape,
            )

            if key == ord("q"):
                break

    finally:

        kinect.shutdown()
        visualizer.close()

        print("Sistema detenido.")


if __name__ == "__main__":
    main()
