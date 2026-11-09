from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ObjectDepth:
    """Distancia radial robusta de una máscara y cantidad de muestras usadas."""

    instance_id: int
    distance_mm: float | None
    valid_pixels: int

    @property
    def distance_m(self):
        return None if self.distance_mm is None else self.distance_mm / 1000.0


class ObjectDistanceEstimator:
    """Asocia máscaras RGB con puntos 3D y estima su distancia radial."""

    def __init__(self, min_valid_pixels=5):
        self.min_valid_pixels = min_valid_pixels

    def estimate(self, depth_mm, depth_to_color_map, camera_space_xyz, masks):
        depth = np.asarray(depth_mm)
        coordinate_map = np.asarray(depth_to_color_map, dtype=np.float32)
        camera_space = np.asarray(camera_space_xyz, dtype=np.float32)
        masks = np.asarray(masks)

        if depth.ndim != 2:
            raise ValueError(f"Depth debe ser 2D; recibido: {depth.shape}")
        if coordinate_map.shape != (*depth.shape, 2):
            raise ValueError(
                "El mapa depth->color debe tener forma "
                f"{(*depth.shape, 2)}; recibido: {coordinate_map.shape}"
            )
        if camera_space.shape != (*depth.shape, 3):
            raise ValueError(
                "El mapa de cámara debe tener forma "
                f"{(*depth.shape, 3)}; recibido: {camera_space.shape}"
            )
        if masks.ndim != 3:
            raise ValueError(f"Las máscaras deben ser 3D (N,H,W); recibido: {masks.shape}")

        color_height, color_width = masks.shape[1:]
        color_x = coordinate_map[..., 0]
        color_y = coordinate_map[..., 1]

        valid_map = (
            np.isfinite(color_x)
            & np.isfinite(color_y)
            & (color_x >= 0)
            & (color_x < color_width)
            & (color_y >= 0)
            & (color_y < color_height)
        )

        color_x_index = np.zeros(depth.shape, dtype=np.int32)
        color_y_index = np.zeros(depth.shape, dtype=np.int32)
        color_x_index[valid_map] = np.rint(color_x[valid_map]).astype(np.int32)
        color_y_index[valid_map] = np.rint(color_y[valid_map]).astype(np.int32)

        # Redondear puede llevar coordenadas del borde justo fuera de la imagen.
        valid_map &= (
            (color_x_index >= 0)
            & (color_x_index < color_width)
            & (color_y_index >= 0)
            & (color_y_index < color_height)
        )
        valid_depth = (depth > 0) & (depth < np.iinfo(np.uint16).max)
        valid_camera = np.isfinite(camera_space).all(axis=2) & (camera_space[..., 2] > 0)
        candidates = valid_map & valid_depth & valid_camera

        camera_points = camera_space[candidates]
        radial_distances_mm = np.linalg.norm(camera_points, axis=1) * 1000.0
        mapped_x = color_x_index[candidates]
        mapped_y = color_y_index[candidates]

        estimates = []
        for instance_id, mask in enumerate(masks):
            if mask.shape != (color_height, color_width):
                raise ValueError(
                    f"Máscara {instance_id} tiene forma {mask.shape}; "
                    f"esperada: {(color_height, color_width)}"
                )

            inside_mask = mask[mapped_y, mapped_x] != 0
            samples = radial_distances_mm[inside_mask]
            valid_pixels = int(samples.size)
            distance_mm = (
                float(np.median(samples))
                if valid_pixels >= self.min_valid_pixels
                else None
            )
            estimates.append(ObjectDepth(instance_id, distance_mm, valid_pixels))

        return estimates
