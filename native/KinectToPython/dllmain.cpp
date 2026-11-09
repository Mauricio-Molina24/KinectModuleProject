#include "Header.h"
#include <Kinect.h>
#include <opencv2/opencv.hpp>
#include <wrl/client.h>
#include <string>
#include <vector>
#include <cstring>
#include <sstream>

using Microsoft::WRL::ComPtr;

namespace {
    IKinectSensor* pSensor = nullptr;
    IColorFrameReader* pColorReader = nullptr;
    IDepthFrameReader* pDepthReader = nullptr;
    IMultiSourceFrameReader* pMultiSourceReader = nullptr;
    ICoordinateMapper* pCoordinateMapper = nullptr;
    std::string lastError;

    constexpr int colorWidth = 1920;
    constexpr int colorHeight = 1080;
    constexpr int depthWidth = 512;
    constexpr int depthHeight = 424;
    constexpr int colorPixels = colorWidth * colorHeight;
    constexpr int depthPixels = depthWidth * depthHeight;
    constexpr int colorBytes = colorPixels * 4;
    constexpr int depthBytes = depthPixels * sizeof(unsigned short);

    void set_hr_error(const char* operation, HRESULT hr) {
        std::ostringstream msg;
        msg << operation << " failed (HRESULT 0x" << std::hex << static_cast<unsigned long>(hr) << ")";
        lastError = msg.str();
    }

    void release_readers() {
        if (pMultiSourceReader) { pMultiSourceReader->Release(); pMultiSourceReader = nullptr; }
        if (pCoordinateMapper) { pCoordinateMapper->Release(); pCoordinateMapper = nullptr; }
        if (pColorReader) { pColorReader->Release(); pColorReader = nullptr; }
        if (pDepthReader) { pDepthReader->Release(); pDepthReader = nullptr; }
    }
}

KINECT_API bool kinect_initialize() noexcept {
    try {
        if (pSensor && pMultiSourceReader && pCoordinateMapper) return true;
        kinect_shutdown();
        HRESULT hr = GetDefaultKinectSensor(&pSensor);
        if (FAILED(hr) || !pSensor) { set_hr_error("GetDefaultKinectSensor", FAILED(hr) ? hr : E_FAIL); return false; }
        hr = pSensor->Open();
        if (FAILED(hr)) { set_hr_error("IKinectSensor::Open", hr); kinect_shutdown(); return false; }

        ComPtr<IColorFrameSource> colorSource;
        ComPtr<IDepthFrameSource> depthSource;
        hr = pSensor->get_ColorFrameSource(&colorSource);
        if (FAILED(hr)) { set_hr_error("get_ColorFrameSource", hr); kinect_shutdown(); return false; }
        hr = pSensor->get_DepthFrameSource(&depthSource);
        if (FAILED(hr)) { set_hr_error("get_DepthFrameSource", hr); kinect_shutdown(); return false; }
        hr = colorSource->OpenReader(&pColorReader);
        if (FAILED(hr)) { set_hr_error("ColorFrameSource::OpenReader", hr); kinect_shutdown(); return false; }
        hr = depthSource->OpenReader(&pDepthReader);
        if (FAILED(hr)) { set_hr_error("DepthFrameSource::OpenReader", hr); kinect_shutdown(); return false; }
        hr = pSensor->get_CoordinateMapper(&pCoordinateMapper);
        if (FAILED(hr) || !pCoordinateMapper) { set_hr_error("get_CoordinateMapper", FAILED(hr) ? hr : E_FAIL); kinect_shutdown(); return false; }
        hr = pSensor->OpenMultiSourceFrameReader(FrameSourceTypes_Color | FrameSourceTypes_Depth, &pMultiSourceReader);
        if (FAILED(hr) || !pMultiSourceReader) { set_hr_error("OpenMultiSourceFrameReader", FAILED(hr) ? hr : E_FAIL); kinect_shutdown(); return false; }
        lastError = "Kinect initialized successfully";
        return true;
    } catch (...) { lastError = "Unexpected error initializing Kinect"; kinect_shutdown(); return false; }
}

KINECT_API void kinect_shutdown() noexcept {
    release_readers();
    if (pSensor) { pSensor->Close(); pSensor->Release(); pSensor = nullptr; }
}

KINECT_API bool kinect_get_color_frame(unsigned char* buffer, int buffer_size) noexcept {
    if (!buffer || buffer_size < colorBytes || !pColorReader) { lastError = "Invalid color buffer or reader"; return false; }
    ComPtr<IColorFrame> frame;
    HRESULT hr = pColorReader->AcquireLatestFrame(&frame);
    if (FAILED(hr)) { set_hr_error("AcquireLatestFrame(color)", hr); return false; }
    hr = frame->CopyConvertedFrameDataToArray(colorBytes, buffer, ColorImageFormat_Bgra);
    if (FAILED(hr)) { set_hr_error("CopyConvertedFrameDataToArray", hr); return false; }
    lastError = "Color frame acquired successfully";
    return true;
}

KINECT_API bool kinect_get_depth_frame(unsigned short* buffer, int buffer_size) noexcept {
    if (!buffer || buffer_size < depthBytes || !pDepthReader) { lastError = "Invalid depth buffer or reader"; return false; }
    ComPtr<IDepthFrame> frame;
    HRESULT hr = pDepthReader->AcquireLatestFrame(&frame);
    if (FAILED(hr)) { set_hr_error("AcquireLatestFrame(depth)", hr); return false; }
    UINT count = 0;
    UINT16* data = nullptr;
    hr = frame->AccessUnderlyingBuffer(&count, &data);
    if (FAILED(hr)) { set_hr_error("AccessUnderlyingBuffer", hr); return false; }
    if (count != depthPixels || !data) { lastError = "Depth frame size mismatch"; return false; }
    std::memcpy(buffer, data, depthBytes);
    lastError = "Depth frame acquired successfully";
    return true;
}

KINECT_API bool kinect_get_synchronized_frames(unsigned char* color_buffer, int color_buffer_size,
    unsigned short* depth_buffer, int depth_buffer_size, float* map_buffer, int map_float_count) noexcept {
    if (!color_buffer || color_buffer_size < colorBytes || !depth_buffer || depth_buffer_size < depthBytes ||
        !map_buffer || map_float_count < colorPixels * 2 || !pMultiSourceReader || !pCoordinateMapper) {
        lastError = "Invalid synchronized-frame buffers or readers"; return false;
    }
    try {
        ComPtr<IMultiSourceFrame> multi;
        HRESULT hr = pMultiSourceReader->AcquireLatestFrame(&multi);
        if (FAILED(hr)) { set_hr_error("AcquireLatestFrame(multi-source)", hr); return false; }
        ComPtr<IColorFrameReference> colorRef;
        ComPtr<IDepthFrameReference> depthRef;
        hr = multi->get_ColorFrameReference(&colorRef);
        if (FAILED(hr)) { set_hr_error("get_ColorFrameReference", hr); return false; }
        hr = multi->get_DepthFrameReference(&depthRef);
        if (FAILED(hr)) { set_hr_error("get_DepthFrameReference", hr); return false; }
        ComPtr<IColorFrame> colorFrame;
        ComPtr<IDepthFrame> depthFrame;
        hr = colorRef->AcquireFrame(&colorFrame);
        if (FAILED(hr)) { set_hr_error("AcquireFrame(color)", hr); return false; }
        hr = depthRef->AcquireFrame(&depthFrame);
        if (FAILED(hr)) { set_hr_error("AcquireFrame(depth)", hr); return false; }

        std::vector<unsigned char> colorTemp(colorBytes);
        std::vector<UINT16> depthTemp(depthPixels);
        std::vector<DepthSpacePoint> mapTemp(colorPixels);
        hr = colorFrame->CopyConvertedFrameDataToArray(colorBytes, colorTemp.data(), ColorImageFormat_Bgra);
        if (FAILED(hr)) { set_hr_error("CopyConvertedFrameDataToArray", hr); return false; }
        UINT depthCount = 0;
        UINT16* depthData = nullptr;
        hr = depthFrame->AccessUnderlyingBuffer(&depthCount, &depthData);
        if (FAILED(hr)) { set_hr_error("AccessUnderlyingBuffer", hr); return false; }
        if (depthCount != depthPixels || !depthData) { lastError = "Depth frame size mismatch"; return false; }
        std::memcpy(depthTemp.data(), depthData, depthBytes);
        hr = pCoordinateMapper->MapColorFrameToDepthSpace(depthCount, depthData, colorPixels, mapTemp.data());
        if (FAILED(hr)) { set_hr_error("MapColorFrameToDepthSpace", hr); return false; }

        // Commit output only after the full capture and mapping succeeded.
        std::memcpy(color_buffer, colorTemp.data(), colorBytes);
        std::memcpy(depth_buffer, depthTemp.data(), depthBytes);
        static_assert(sizeof(DepthSpacePoint) == sizeof(float) * 2, "Unexpected DepthSpacePoint layout");
        std::memcpy(map_buffer, mapTemp.data(), colorPixels * sizeof(DepthSpacePoint));
        lastError = "Synchronized color, depth and coordinate map acquired successfully";
        return true;
    } catch (...) { lastError = "Unexpected error acquiring synchronized frames"; return false; }
}

extern "C" KINECT_API bool kinect_get_synchronized_frames_depth_to_color(
    unsigned char* color_buffer, int color_buffer_size,
    unsigned short* depth_buffer, int depth_buffer_size,
    float* map_buffer, int map_float_count,
    float* camera_space_buffer, int camera_space_float_count) noexcept {
    if (!color_buffer || color_buffer_size < colorBytes || !depth_buffer || depth_buffer_size < depthBytes ||
        !map_buffer || map_float_count < depthPixels * 2 ||
        !camera_space_buffer || camera_space_float_count < depthPixels * 3 ||
        !pMultiSourceReader || !pCoordinateMapper) {
        lastError = "Invalid synchronized-frame buffers or readers"; return false;
    }
    try {
        ComPtr<IMultiSourceFrame> multi;
        HRESULT hr = pMultiSourceReader->AcquireLatestFrame(&multi);
        if (FAILED(hr)) { set_hr_error("AcquireLatestFrame(multi-source)", hr); return false; }
        ComPtr<IColorFrameReference> colorRef;
        ComPtr<IDepthFrameReference> depthRef;
        hr = multi->get_ColorFrameReference(&colorRef);
        if (FAILED(hr)) { set_hr_error("get_ColorFrameReference", hr); return false; }
        hr = multi->get_DepthFrameReference(&depthRef);
        if (FAILED(hr)) { set_hr_error("get_DepthFrameReference", hr); return false; }
        ComPtr<IColorFrame> colorFrame;
        ComPtr<IDepthFrame> depthFrame;
        hr = colorRef->AcquireFrame(&colorFrame);
        if (FAILED(hr)) { set_hr_error("AcquireFrame(color)", hr); return false; }
        hr = depthRef->AcquireFrame(&depthFrame);
        if (FAILED(hr)) { set_hr_error("AcquireFrame(depth)", hr); return false; }

        std::vector<unsigned char> colorTemp(colorBytes);
        std::vector<UINT16> depthTemp(depthPixels);
        std::vector<ColorSpacePoint> mapTemp(depthPixels);
        std::vector<CameraSpacePoint> cameraSpaceTemp(depthPixels);
        hr = colorFrame->CopyConvertedFrameDataToArray(colorBytes, colorTemp.data(), ColorImageFormat_Bgra);
        if (FAILED(hr)) { set_hr_error("CopyConvertedFrameDataToArray", hr); return false; }
        UINT depthCount = 0;
        UINT16* depthData = nullptr;
        hr = depthFrame->AccessUnderlyingBuffer(&depthCount, &depthData);
        if (FAILED(hr)) { set_hr_error("AccessUnderlyingBuffer", hr); return false; }
        if (depthCount != depthPixels || !depthData) { lastError = "Depth frame size mismatch"; return false; }
        std::memcpy(depthTemp.data(), depthData, depthBytes);
        hr = pCoordinateMapper->MapDepthFrameToColorSpace(
            depthCount, depthData, depthPixels, mapTemp.data());
        if (FAILED(hr)) { set_hr_error("MapDepthFrameToColorSpace", hr); return false; }
        hr = pCoordinateMapper->MapDepthFrameToCameraSpace(
            depthCount, depthData, depthPixels, cameraSpaceTemp.data());
        if (FAILED(hr)) { set_hr_error("MapDepthFrameToCameraSpace", hr); return false; }

        std::memcpy(color_buffer, colorTemp.data(), colorBytes);
        std::memcpy(depth_buffer, depthTemp.data(), depthBytes);
        static_assert(sizeof(ColorSpacePoint) == sizeof(float) * 2, "Unexpected ColorSpacePoint layout");
        static_assert(sizeof(CameraSpacePoint) == sizeof(float) * 3, "Unexpected CameraSpacePoint layout");
        std::memcpy(map_buffer, mapTemp.data(), depthPixels * sizeof(ColorSpacePoint));
        std::memcpy(camera_space_buffer, cameraSpaceTemp.data(), depthPixels * sizeof(CameraSpacePoint));
        lastError = "Synchronized color, depth and camera-space map acquired successfully";
        return true;
    } catch (...) { lastError = "Unexpected error acquiring synchronized frames"; return false; }
}

KINECT_API bool kinect_get_depth_frame_colored(unsigned char* buffer, int buffer_size) noexcept {
    if (!buffer || buffer_size < depthPixels * 3) { lastError = "Invalid colored depth buffer"; return false; }
    try {
        std::vector<unsigned short> depth(depthPixels);
        if (!kinect_get_depth_frame(depth.data(), depthBytes)) return false;
        cv::Mat depthImage(depthHeight, depthWidth, CV_16U, depth.data());
        double minVal = 0, maxVal = 0;
        cv::minMaxIdx(depthImage, &minVal, &maxVal);
        if (maxVal <= minVal) { lastError = "Depth frame has no displayable range"; return false; }
        cv::Mat display;
        depthImage.convertTo(display, CV_8U, 255.0 / (maxVal - minVal), -minVal * 255.0 / (maxVal - minVal));
        cv::applyColorMap(display, display, cv::COLORMAP_JET);
        cv::cvtColor(display, display, cv::COLOR_BGR2RGB);
        std::memcpy(buffer, display.data, depthPixels * 3);
        return true;
    } catch (...) { lastError = "Unexpected error coloring depth frame"; return false; }
}

KINECT_API int kinect_get_color_width() noexcept { return colorWidth; }
KINECT_API int kinect_get_color_height() noexcept { return colorHeight; }
KINECT_API int kinect_get_depth_width() noexcept { return depthWidth; }
KINECT_API int kinect_get_depth_height() noexcept { return depthHeight; }
KINECT_API const char* kinect_get_last_error() noexcept { return lastError.c_str(); }
KINECT_API bool kinect_is_available() noexcept { return pSensor != nullptr; }
KINECT_API void kinect_set_mirror_mode(bool enable) noexcept { (void)enable; }
