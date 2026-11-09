# KinectModuleProject

Aplicación experimental para capturar frames sincronizados de una Microsoft Kinect v2, segmentar objetos en la imagen RGB con YOLO y estimar la distancia radial de cada máscara usando las coordenadas 3D de cámara del Kinect.

## Requisitos del sistema

- Windows x64.
- Sensor Microsoft Kinect v2 y Kinect for Windows SDK 2.0 instalado.
- Python 3.10 o 3.11 de 64 bits.
- Se recomienda una GPU compatible con PyTorch para procesar video en tiempo real. Sin aceleración por GPU, el programa puede funcionar en CPU, pero será bastante más lento.
- Microsoft Visual Studio 2022 con la carga de trabajo de C++ si se desea compilar el DLL.
- OpenCV C++ 4.12.0 para compilar el DLL. La DLL de ejecución `opencv_world4120.dll` se incluye junto al wrapper.

## Preparar Python

Desde la carpeta raíz del repositorio, crea un entorno e instala las dependencias comunes:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

El archivo `requirements.txt` instala las dependencias comunes y no fija un modelo de GPU ni una versión de CUDA. Para aceleración NVIDIA, instala PyTorch con la opción de Windows/Pip/CUDA compatible con el controlador, usando el [selector oficial de PyTorch](https://pytorch.org/get-started/locally/). Si no hay CUDA disponible, el proyecto selecciona CPU automáticamente; la inferencia será más lenta. `requirements-cu130.txt` queda como perfil opcional para reproducir el entorno de una PC específica, no como requisito del proyecto.

## Ejecutar

Con el Kinect conectada y el SDK instalado:

```powershell
python .\python\kinectmodule\main.py
```

El modelo de ejemplo `yolov8n-seg.pt` se encuentra junto al módulo. Se puede cambiar la ruta y los parámetros en `python/kinectmodule/config.py`. La cámara entrega color BGRA; el programa lo convierte a BGR para YOLO. La captura sincronizada incluye la imagen depth, el mapa depth→color y las coordenadas 3D de cámara. El estimador usa estas últimas para reportar distancia radial al objeto; no toma el piso como referencia.

## DLL nativo

El wrapper de Python carga `python/kinectmodule/KinectToPython.dll`; `opencv_world4120.dll` debe permanecer en esa misma carpeta para que Windows encuentre la dependencia nativa de OpenCV.

El proyecto de Visual Studio está en `native/KinectToPython.sln`. Para compilar en otro equipo, instala Kinect SDK 2.0 y OpenCV C++ 4.12.0, configura la variable de entorno `OPENCV_ROOT` con la carpeta raíz de OpenCV y compila `Release | x64`. Luego copia el DLL generado a `python/kinectmodule/`. El proyecto requiere el toolset MSVC v143 (Visual Studio 2022).

## Licencia

El código de este proyecto se publica bajo AGPL-3.0; consulta `LICENSE`. Ultralytics indica que su software y modelos están sujetos a AGPL-3.0 por defecto, salvo que se tenga una licencia Enterprise. OpenCV se distribuye bajo Apache-2.0; su texto de licencia está en `THIRD_PARTY_LICENSES/OPENCV-LICENSE.txt`. Revisa los términos de cada componente antes de usar el proyecto en un producto o servicio.

## Estado

Primera versión funcional en desarrollo. La captura y los tiempos dependen del hardware, los controladores y la GPU disponibles.
