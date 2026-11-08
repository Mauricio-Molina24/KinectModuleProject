#pragma once
// kinect_module.h
#pragma once

// Definición para exportar/importar funciones de la DLL
#ifdef KINECTMODULE_EXPORTS
#define KINECT_API __declspec(dllexport)
#else
#define KINECT_API __declspec(dllimport)
#endif

// Includes necesarios (solo forward declarations para el encabezado)
#include <Kinect.h>

// Las funciones de C++ deben usar extern "C" para ser compatibles con Python
extern "C" {

    // FUNCIONES DE INICIALIZACIÓN
    KINECT_API bool kinect_initialize() noexcept;
    KINECT_API void kinect_shutdown() noexcept;

    // FUNCIONES DE OBTENCIÓN DE FRAMES
    KINECT_API bool kinect_get_color_frame(unsigned char* buffer, int buffer_size) noexcept;
    KINECT_API bool kinect_get_depth_frame(unsigned short* buffer, int buffer_size) noexcept;
    KINECT_API bool kinect_get_depth_frame_colored(unsigned char* buffer, int buffer_size) noexcept;

    // RGB, depth y mapa RGB->Depth calculados desde el mismo MultiSourceFrame.
    KINECT_API bool kinect_get_synchronized_frames(
        unsigned char* color_buffer, int color_buffer_size,
        unsigned short* depth_buffer, int depth_buffer_size,
        float* coordinate_map_buffer, int coordinate_map_float_count) noexcept;    // Mismo frame sincronizado, pero con mapa Depth->Color (resolución de depth).    KINECT_API bool kinect_get_synchronized_frames_depth_to_color(        unsigned char* color_buffer, int color_buffer_size,        unsigned short* depth_buffer, int depth_buffer_size,        float* coordinate_map_buffer, int coordinate_map_float_count) noexcept;

    // FUNCIONES DE INFORMACIÓN
    KINECT_API int kinect_get_color_width() noexcept;
    KINECT_API int kinect_get_color_height() noexcept;
    KINECT_API int kinect_get_depth_width() noexcept;
    KINECT_API int kinect_get_depth_height() noexcept;

    // FUNCIONES DE UTILIDAD
    KINECT_API const char* kinect_get_last_error() noexcept;

    // FUNCIONES ADICIONALES ÚTILES
    KINECT_API bool kinect_is_available() noexcept;
    KINECT_API void kinect_set_mirror_mode(bool enable) noexcept;
}