import cv2


class FrameVisualizer:
    """Muestra el resultado de YOLO y la profundidad para depuración."""

    def __init__(self, show_depth=True):
        self.show_depth = show_depth

    def show(self, color_bgr, depth_mm, result):
        annotated = result.plot()

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
