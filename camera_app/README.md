# Sistema de Vigilancia RTSP

Sistema completo de vigilancia de cámaras RTSP con grabación continua 24/7, previsualización web y limpieza automática de archivos antiguos.

## 🚀 Características

- **Previsualización en tiempo real** via web browser
- **Grabación continua 24/7** con segmentación automática
- **Limpieza automática** de archivos antiguos (7 días por defecto)
- **Reconexión automática** en caso de pérdida de conexión
- **Interfaz web responsive** preparada para múltiples cámaras
- **Configuración centralizada** via archivo JSON

## 📋 Requisitos

### Software Necesario
- Python 3.7 o superior
- FFmpeg (para grabación de video)
- Navegador web moderno

### Instalación de FFmpeg en Windows
1. Descargar FFmpeg desde: https://ffmpeg.org/download.html
2. Extraer el archivo ZIP a `C:\ffmpeg`
3. Agregar `C:\ffmpeg\bin` al PATH del sistema
4. Verificar instalación: `ffmpeg -version`

## 🛠️ Instalación

1. **Clonar o descargar** el proyecto
2. **Instalar dependencias Python**:
   ```bash
   cd camera_app
   pip install -r requirements.txt
   ```

3. **Configurar cámaras** editando `config.json`:
   ```json
   {
     "cameras": [
       {
         "id": "cam1",
         "name": "Cámara Principal",
         "rtsp_url": "rtsp://usuario:password@192.168.0.244:554/stream1",
         "enabled": true
       }
     ],
     "recordings_path": "recordings",
     "retention_days": 7,
     "segment_duration": 3600,
     "flask_port": 5000,
     "ffmpeg_reconnect_delay": 10
   }
   ```

## 🎯 Uso

### 1. Iniciar Grabación
```bash
python recorder.py
```
- Inicia grabación continua de todas las cámaras habilitadas
- Archivos se guardan en el directorio `recordings/`
- Segmentación automática cada hora
- Reconexión automática en caso de fallos

### 2. Iniciar Servidor Web
```bash
python app.py
```
- Abrir navegador en: http://localhost:5000
- Previsualización en tiempo real
- Interfaz responsive para múltiples cámaras

### 3. Limpieza Automática
```bash
# Ejecutar manualmente
python cleaner.py

# Modo dry-run (solo mostrar qué se eliminaría)
python cleaner.py --dry-run
```

## ⚙️ Configuración Avanzada

### Múltiples Cámaras
Para agregar más cámaras, editar `config.json`:
```json
{
  "cameras": [
    {
      "id": "cam1",
      "name": "Cámara Principal",
      "rtsp_url": "rtsp://user:pass@192.168.0.244:554/stream1",
      "enabled": true
    },
    {
      "id": "cam2", 
      "name": "Cámara Secundaria",
      "rtsp_url": "rtsp://user:pass@192.168.0.245:554/stream1",
      "enabled": true
    }
  ]
}
```

### Programar Limpieza Automática (Windows)
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Configurar para ejecutar cada hora
4. Acción: Iniciar programa
5. Programa: `python.exe`
6. Argumentos: `C:\ruta\completa\al\cleaner.py`
7. Directorio: `C:\ruta\completa\al\camera_app`

## 📁 Estructura de Archivos

```
camera_app/
├── app.py              # Servidor web Flask
├── recorder.py         # Script de grabación
├── cleaner.py          # Script de limpieza
├── config.json         # Configuración
├── requirements.txt    # Dependencias Python
├── README.md          # Este archivo
├── templates/
│   └── index.html     # Interfaz web
└── recordings/        # Directorio de grabaciones
    ├── cam1_2024-01-15_10-30-00.mp4
    ├── cam1_2024-01-15_11-30-00.mp4
    └── ...
```

## 🔧 Solución de Problemas

### Error: "FFmpeg no encontrado"
- Verificar que FFmpeg esté instalado y en el PATH
- Reiniciar terminal después de instalar FFmpeg

### Error: "No se pudo conectar a la cámara"
- Verificar URL RTSP y credenciales
- Comprobar conectividad de red
- Verificar que la cámara esté encendida

### Error: "Sin permisos para escribir"
- Verificar permisos del directorio `recordings/`
- Ejecutar como administrador si es necesario

### Stream no se muestra en el navegador
- Verificar que el puerto 5000 esté libre
- Comprobar firewall/antivirus
- Probar en modo incógnito del navegador

## 📊 Monitoreo

### Estado del Sistema
- Visitar: http://localhost:5000/status
- Muestra estado de todas las cámaras
- Información de última conexión

### Logs
- Los scripts muestran información detallada en consola
- Errores se muestran con emojis para fácil identificación

## 🔒 Seguridad

- **Cambiar credenciales** por defecto en `config.json`
- **Usar HTTPS** en producción
- **Configurar firewall** para restringir acceso
- **Respaldar configuraciones** regularmente

## 📈 Rendimiento

### Optimizaciones Incluidas
- FFmpeg con `-c copy` (sin transcodificación)
- Buffer reducido en OpenCV para menor latencia
- Segmentación eficiente de archivos
- Limpieza automática para ahorrar espacio

### Recomendaciones
- Usar SSD para grabaciones
- Monitorear uso de CPU y memoria
- Ajustar calidad de video según necesidades

## 🤝 Soporte

Para problemas o mejoras:
1. Verificar logs de consola
2. Comprobar configuración
3. Revisar conectividad de red
4. Consultar documentación de FFmpeg

## 📄 Licencia

Sistema de Vigilancia RTSP - Uso interno
