#include <iostream>
#include <Windows.h>
#include <Kinect.h>
#include <string>

// Importar las funciones de tu DLL
extern "C" {
    __declspec(dllimport) bool kinect_initialize();
    __declspec(dllimport) void kinect_shutdown();
    __declspec(dllimport) bool kinect_get_depth_frame(unsigned short* buffer, int buffer_size);
    __declspec(dllimport) const char* kinect_get_last_error();
    __declspec(dllimport) int kinect_get_depth_width();
    __declspec(dllimport) int kinect_get_depth_height();
}

int main()
{
    std::cout << "?? Testing Kinect DLL directly..." << std::endl;

    // 1. Inicializar Kinect
    std::cout << "?? Initializing Kinect..." << std::endl;
    if (!kinect_initialize()) {
        std::cout << "? Failed to initialize: " << kinect_get_last_error() << std::endl;
        return 1;
    }
    std::cout << "? Kinect initialized successfully!" << std::endl;

    // 2. Obtener dimensiones
    int depth_width = kinect_get_depth_width();
    int depth_height = kinect_get_depth_height();
    std::cout << "?? Depth dimensions: " << depth_width << "x" << depth_height << std::endl;

    // 3. Preparar buffer para depth frame
    const int buffer_size = depth_width * depth_height;
    unsigned short* depth_buffer = new unsigned short[buffer_size];

    // 4. Intentar obtener depth frame múltiples veces
    std::cout << "?? Attempting to get depth frames..." << std::endl;

    for (int attempt = 0; attempt < 10; attempt++) {
        std::cout << "   Attempt " << (attempt + 1) << ": ";

        if (kinect_get_depth_frame(depth_buffer, buffer_size * sizeof(unsigned short))) {
            std::cout << "? SUCCESS!" << std::endl;

            // Analizar los datos obtenidos
            unsigned short min_val = 0xFFFF;
            unsigned short max_val = 0;
            int valid_pixels = 0;

            for (int i = 0; i < buffer_size; i++) {
                if (depth_buffer[i] > 0 && depth_buffer[i] < 0xFFFF) {
                    valid_pixels++;
                    if (depth_buffer[i] < min_val) min_val = depth_buffer[i];
                    if (depth_buffer[i] > max_val) max_val = depth_buffer[i];
                }
            }

            std::cout << "   ?? Valid pixels: " << valid_pixels << "/" << buffer_size << std::endl;
            std::cout << "   ?? Depth range: " << min_val << " - " << max_val << " mm" << std::endl;
            std::cout << "   ?? First 10 values: ";
            for (int i = 0; i < 10 && i < buffer_size; i++) {
                std::cout << depth_buffer[i] << " ";
            }
            std::cout << std::endl;

            break;
        }
        else {
            std::cout << "? FAILED: " << kinect_get_last_error() << std::endl;
            Sleep(100); // Esperar 100ms entre intentos
        }
    }

    // 5. Limpieza
    delete[] depth_buffer;
    kinect_shutdown();
    std::cout << "?? Kinect shutdown" << std::endl;

    std::cout << "\n?? Test completed. Press Enter to exit..." << std::endl;
    std::cin.get();

    return 0;
}