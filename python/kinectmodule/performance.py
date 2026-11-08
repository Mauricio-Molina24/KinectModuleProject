
class PerformanceMonitor:
    """Acumula métricas y las informa por bloques de frames."""

    def __init__(self, report_every=30):
        self.report_every = report_every
        self.reset()

    def reset(self):
        self.frames = 0
        self.capture_ms = 0.0
        self.yolo_ms = 0.0
        self.cycle_ms = 0.0
        self.capture_attempts = 0

    def record(self, capture_ms, yolo_ms, cycle_ms, attempts, instances, map_shape):
        self.frames += 1
        self.capture_ms += capture_ms
        self.yolo_ms += yolo_ms
        self.cycle_ms += cycle_ms
        self.capture_attempts += attempts

        if self.frames < self.report_every:
            return

        count = self.frames
        avg_capture = self.capture_ms / count
        avg_yolo = self.yolo_ms / count
        avg_cycle = self.cycle_ms / count
        avg_attempts = self.capture_attempts / count
        fps = 1000 / avg_cycle if avg_cycle > 0 else 0

        print(
            f"Promedio captura: {avg_capture:.1f} ms | "
            f"Promedio YOLO: {avg_yolo:.1f} ms | "
            f"Promedio ciclo: {avg_cycle:.1f} ms | "
            f"Intentos captura: {avg_attempts:.2f} | "
            f"FPS aprox.: {fps:.1f} | "
            f"Instancias: {instances} | "
            f"Mapa depth->color: {map_shape}"
        )
        self.reset()
