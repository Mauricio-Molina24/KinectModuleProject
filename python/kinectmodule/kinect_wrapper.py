import ctypes
import numpy as np
import cv2
import os
import time  # Añadir este import

class KinectWrapper:
    def __init__(self, dll_path="KinectToPython.dll"):
        # Obtener la ruta absoluta de la DLL
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dll_full_path = os.path.join(current_dir, dll_path)
        
        # Cargar la DLL
        self.dll = ctypes.CDLL(dll_full_path)
        
        # Definir los prototipos de las funciones
        self._setup_function_prototypes()
        
        # Obtener dimensiones
        self.color_width = self.dll.kinect_get_color_width()
        self.color_height = self.dll.kinect_get_color_height()
        self.depth_width = self.dll.kinect_get_depth_width()
        self.depth_height = self.dll.kinect_get_depth_height()
        
    def _setup_function_prototypes(self):
        # Configurar los tipos de retorno y parámetros de cada función
        self.dll.kinect_initialize.restype = ctypes.c_bool
        self.dll.kinect_initialize.argtypes = []
        
        self.dll.kinect_shutdown.restype = None
        self.dll.kinect_shutdown.argtypes = []
        
        self.dll.kinect_get_color_frame.restype = ctypes.c_bool
        self.dll.kinect_get_color_frame.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
        
        self.dll.kinect_get_depth_frame.restype = ctypes.c_bool
        self.dll.kinect_get_depth_frame.argtypes = [ctypes.POINTER(ctypes.c_ushort), ctypes.c_int]
        
        self.dll.kinect_get_depth_frame_colored.restype = ctypes.c_bool
        self.dll.kinect_get_depth_frame_colored.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]

        self.dll.kinect_get_synchronized_frames.restype = ctypes.c_bool
        self.dll.kinect_get_synchronized_frames.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int,
            ctypes.POINTER(ctypes.c_ushort), ctypes.c_int,
            ctypes.POINTER(ctypes.c_float), ctypes.c_int,
        ]

        self.dll.kinect_get_synchronized_frames_depth_to_color.restype = ctypes.c_bool
        self.dll.kinect_get_synchronized_frames_depth_to_color.argtypes = [
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int,
            ctypes.POINTER(ctypes.c_ushort), ctypes.c_int,
            ctypes.POINTER(ctypes.c_float), ctypes.c_int,
        ]
        
        self.dll.kinect_get_last_error.restype = ctypes.c_char_p
        self.dll.kinect_get_last_error.argtypes = []
        
        self.dll.kinect_get_color_width.restype = ctypes.c_int
        self.dll.kinect_get_color_height.restype = ctypes.c_int
        self.dll.kinect_get_depth_width.restype = ctypes.c_int
        self.dll.kinect_get_depth_height.restype = ctypes.c_int
    
    def initialize(self):
        """Inicializar el sensor Kinect"""
        return self.dll.kinect_initialize()
    
    def shutdown(self):
        """Apagar el sensor Kinect"""
        self.dll.kinect_shutdown()
    
    def get_last_error(self):
        """Obtener el último mensaje de error"""
        error_msg = self.dll.kinect_get_last_error()
        return error_msg.decode('utf-8') if error_msg else "No error"
    
    def get_color_frame(self):
        """Obtener frame de color como numpy array"""
        buffer_size = self.color_width * self.color_height * 4
        buffer = (ctypes.c_ubyte * buffer_size)()
        
        # Reintentar múltiples veces
        for attempt in range(5):
            if self.dll.kinect_get_color_frame(buffer, buffer_size):
                frame = np.frombuffer(buffer, dtype=np.uint8)
                return frame.reshape((self.color_height, self.color_width, 4))
            time.sleep(0.1)
        return None
    
    def get_depth_frame(self):
        """Obtener frame de profundidad (16-bit) - CON REINTENTOS"""
        buffer_size = self.depth_width * self.depth_height
        buffer = (ctypes.c_ushort * buffer_size)()
        
        # Reintentar múltiples veces (esto es clave)
        for attempt in range(10):
            if self.dll.kinect_get_depth_frame(buffer, buffer_size * 2):  # *2 porque ushort son 2 bytes
                frame = np.frombuffer(buffer, dtype=np.uint16)
                return frame.reshape((self.depth_height, self.depth_width))
            time.sleep(0.1)  # Pequeña pausa entre intentos
        return None
    
    def get_synchronized_frames(self, retries=10, retry_delay=0.05):
        """Return (BGRA color, uint16 depth in mm, float32 RGB->depth map).

        All three arrays are copied from one Kinect MultiSourceFrame. Invalid
        map locations are reported by the SDK as non-finite or out-of-range X/Y.
        """
        color_count = self.color_width * self.color_height * 4
        depth_count = self.depth_width * self.depth_height
        map_float_count = self.color_width * self.color_height * 2
        color = (ctypes.c_ubyte * color_count)()
        depth = (ctypes.c_ushort * depth_count)()
        coordinate_map = (ctypes.c_float * map_float_count)()

        for _ in range(retries):
            ok = self.dll.kinect_get_synchronized_frames(
                color, color_count, depth, depth_count * ctypes.sizeof(ctypes.c_ushort),
                coordinate_map, map_float_count,
            )
            if ok:
                rgb = np.ctypeslib.as_array(color).reshape(
                    self.color_height, self.color_width, 4
                ).copy()
                depth_array = np.ctypeslib.as_array(depth).reshape(
                    self.depth_height, self.depth_width
                ).copy()
                map_array = np.ctypeslib.as_array(coordinate_map).reshape(
                    self.color_height, self.color_width, 2
                ).copy()
                return rgb, depth_array, map_array
            time.sleep(retry_delay)
        return None, None, None

    def get_synchronized_frames_depth_to_color(self, retries=10, retry_delay=0.05):
        """Return BGRA color, uint16 depth (mm), and a depth-resolution map to color.

        The map has shape (depth_height, depth_width, 2); each depth pixel stores
        its corresponding (x, y) coordinate in the original color image.
        """
        color_count = self.color_width * self.color_height * 4
        depth_count = self.depth_width * self.depth_height
        map_float_count = depth_count * 2
        color = (ctypes.c_ubyte * color_count)()
        depth = (ctypes.c_ushort * depth_count)()
        coordinate_map = (ctypes.c_float * map_float_count)()
        self.last_depth_to_color_attempts = 0

        for attempt in range(retries):
            self.last_depth_to_color_attempts = attempt + 1
            ok = self.dll.kinect_get_synchronized_frames_depth_to_color(
                color, color_count,
                depth, depth_count * ctypes.sizeof(ctypes.c_ushort),
                coordinate_map, map_float_count,
            )
            if ok:
                color_array = np.ctypeslib.as_array(color).reshape(
                    self.color_height, self.color_width, 4
                ).copy()
                depth_array = np.ctypeslib.as_array(depth).reshape(
                    self.depth_height, self.depth_width
                ).copy()
                map_array = np.ctypeslib.as_array(coordinate_map).reshape(
                    self.depth_height, self.depth_width, 2
                ).copy()
                return color_array, depth_array, map_array
            time.sleep(retry_delay)
        return None, None, None

    def get_depth_frame_colored(self):
        """Obtener frame de profundidad coloreado (8-bit RGB)"""
        buffer_size = self.depth_width * self.depth_height * 3
        buffer = (ctypes.c_ubyte * buffer_size)()
        
        # Reintentar múltiples veces
        for attempt in range(5):
            if self.dll.kinect_get_depth_frame_colored(buffer, buffer_size):
                frame = np.frombuffer(buffer, dtype=np.uint8)
                return frame.reshape((self.depth_height, self.depth_width, 3))
            time.sleep(0.1)
        return None
    
    # El resto de tus funciones permanecen igual...
    def get_color_frame_bgr(self):
        """Obtener frame en formato BGR (para modelos de ML)"""
        color_frame = self.get_color_frame()
        if color_frame is not None:
            return cv2.cvtColor(color_frame, cv2.COLOR_BGRA2BGR)
        return None

    def get_color_frame_rgb(self):
        """Obtener frame en formato RGB"""
        color_frame = self.get_color_frame()
        if color_frame is not None:
            return cv2.cvtColor(color_frame, cv2.COLOR_BGRA2RGB)
        return None
    
    def get_depth_frame_meters(self):
        """Obtener profundidad en metros (float)"""
        depth_frame = self.get_depth_frame()
        if depth_frame is not None:
            return depth_frame.astype(np.float32) / 1000.0  # mm to meters
        return None

