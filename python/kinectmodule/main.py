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

    try:
        print("Esperando el primer frame sincronizado...")
        first_color, _, _, _ = kinect.get_synchronized_frames_depth_to_color(
            retries=30,
            retry_delay=0.1,
        )
        if first_color is None:
            print("Error al iniciar los streams:", kinect.get_last_error())
            return

        print("Streams de color y profundidad listos.")
        last_capture_error_time = 0.0
        last_depth_report_time = 0.0

        while True:
            loop_start = time.perf_counter()

            # 1. Obtener captura sincronizada
            color, depth, depth_to_color_map, camera_space_xyz = kinect.get_synchronized_frames_depth_to_color(
                retries=5,
                retry_delay=0.03,
            )
            capture_ms = (time.perf_counter() - loop_start) * 1000

            if color is None:
                now = time.monotonic()
                if now - last_capture_error_time >= 1.0:
                    print("Error obteniendo frames:", kinect.get_last_error())
                    last_capture_error_time = now
                time.sleep(0.05)
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
                camera_space_xyz=camera_space_xyz,
                masks=masks,
            )

            # Reportar una lectura reciente de cada objeto en la terminal.
            now = time.monotonic()
            if now - last_depth_report_time >= 1.0:
                readings = []
                for estimate in object_depths:
                    if result.boxes is None or estimate.instance_id >= len(result.boxes):
                        continue

                    class_id = int(result.boxes.cls[estimate.instance_id].item())
                    if isinstance(result.names, dict):
                        class_name = result.names.get(class_id, str(class_id))
                    else:
                        class_name = result.names[class_id]

                    if estimate.distance_m is None:
                        distance_text = "sin lectura válida"
                    else:
                        distance_text = f"{estimate.distance_m:.2f} m"

                    reliability_notes = []
                    if estimate.valid_pixels < 20:
                        reliability_notes.append("pocas muestras")
                    if estimate.distance_mm is not None and estimate.distance_mm > 4500:
                        reliability_notes.append("más allá de 4.5 m")
                    reliability_text = (
                        f"; baja confiabilidad: {', '.join(reliability_notes)}"
                        if reliability_notes
                        else ""
                    )

                    readings.append(
                        f"{class_name}: {distance_text} "
                        f"({estimate.valid_pixels} píxeles válidos{reliability_text})"
                    )

                if readings:
                    print("Distancia radial | " + " | ".join(readings))
                else:
                    print("Distancia radial | Sin objetos detectados.")
                last_depth_report_time = now

            # 5. Mostrar detecciones con su distancia estimada.
            key = visualizer.show(color_bgr, depth, result)

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
