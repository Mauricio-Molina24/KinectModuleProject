import cv2


class FrameVisualizer:
    """Muestra el resultado de YOLO y la profundidad para depuración."""

    def __init__(self, show_depth=True):
        self.show_depth = show_depth

    def show(self, color_bgr, depth_mm, result, object_depths=()):
        annotated = result.plot()

        if result.boxes is not None:
            for estimate in object_depths:
                if estimate.instance_id >= len(result.boxes):
                    continue

                class_id = int(result.boxes.cls[estimate.instance_id].item())
                if isinstance(result.names, dict):
                    class_name = result.names.get(class_id, str(class_id))
                else:
                    class_name = result.names[class_id]

                if estimate.distance_m is None:
                    label = f"{class_name}: sin depth ({estimate.valid_pixels} px)"
                else:
                    label = f"{class_name}: {estimate.distance_m:.2f} m"

                box = result.boxes.xyxy[estimate.instance_id].cpu().numpy().astype(int)
                x1, y1 = int(box[0]), max(20, int(box[1]) - 8)
                cv2.putText(
                    annotated, label, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 255, 0), 2, cv2.LINE_AA,
                )

        cv2.imshow("Kinect RGB + YOLO", annotated)

        if self.show_depth:
            depth_display = cv2.normalize(
                depth_mm, None, 0, 255, cv2.NORM_MINMAX
            ).astype("uint8")
            cv2.imshow("Kinect Depth", depth_display)

        return cv2.waitKey(1) & 0xFF

    @staticmethod
    def close():
        cv2.destroyAllWindows()
