#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Web para Previsualización de Cámaras RTSP
==================================================

Aplicación Flask que proporciona una interfaz web para visualizar
streams RTSP en tiempo real usando OpenCV y MJPEG.

Características:
- Previsualización en tiempo real de streams RTSP
- Interfaz web responsive
- Manejo de errores de conexión
- Preparado para múltiples cámaras

Autor: Sistema de Vigilancia RTSP
Fecha: 2024
"""

import json
import cv2
import threading
import time
from flask import Flask, render_template, Response
from datetime import datetime


class CameraStream:
    """Clase para manejar el streaming de una cámara RTSP."""
    
    def __init__(self, camera_config):
        """
        Inicializar stream de cámara.
        
        Args:
            camera_config (dict): Configuración de la cámara
        """
        self.camera_id = camera_config['id']
        self.camera_name = camera_config['name']
        self.rtsp_url = camera_config['rtsp_url']
        self.cap = None
        self.last_frame = None
        self.last_frame_time = 0
        self.frame_lock = threading.Lock()
        self.running = False
        self.thread = None
        
    def _connect_camera(self):
        """Conectar a la cámara RTSP."""
        try:
            if self.cap is not None:
                self.cap.release()
            
            print(f"📡 Conectando a {self.camera_name} ({self.camera_id})")
            print(f"🔗 URL: {self.rtsp_url}")
            
            # Configurar OpenCV para RTSP
            self.cap = cv2.VideoCapture(self.rtsp_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reducir buffer para menor latencia
            
            if not self.cap.isOpened():
                raise Exception("No se pudo abrir la conexión RTSP")
            
            print(f"✅ Conectado a {self.camera_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a {self.camera_name}: {e}")
            return False
    
    def _capture_frames(self):
        """Hilo para capturar fotogramas continuamente."""
        while self.running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    if not self._connect_camera():
                        time.sleep(5)  # Esperar antes de reintentar
                        continue
                
                ret, frame = self.cap.read()
                
                if ret:
                    with self.frame_lock:
                        self.last_frame = frame
                        self.last_frame_time = time.time()
                else:
                    print(f"⚠️  Error leyendo frame de {self.camera_name}")
                    self.cap.release()
                    self.cap = None
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error en captura de {self.camera_name}: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                time.sleep(5)
    
    def start(self):
        """Iniciar captura de frames."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.thread.start()
            print(f"🎥 Iniciado streaming para {self.camera_name}")
    
    def stop(self):
        """Detener captura de frames."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            self.cap = None
        print(f"🛑 Detenido streaming para {self.camera_name}")
    
    def get_frame(self):
        """
        Obtener el último frame capturado.
        
        Returns:
            numpy.ndarray: Frame como imagen, o None si no hay frame disponible
        """
        with self.frame_lock:
            if self.last_frame is not None and (time.time() - self.last_frame_time) < 10:
                return self.last_frame.copy()
        return None


class RTSPWebServer:
    """Servidor web Flask para previsualización de cámaras."""
    
    def __init__(self, config_path="config.json"):
        """
        Inicializar servidor web.
        
        Args:
            config_path (str): Ruta al archivo de configuración
        """
        self.app = Flask(__name__)
        self.config = self._load_config(config_path)
        self.cameras = {}
        self._setup_routes()
        self._initialize_cameras()
    
    def _load_config(self, config_path):
        """Cargar configuración desde archivo JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo de configuración: {config_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error al leer configuración JSON: {e}")
            return None
    
    def _initialize_cameras(self):
        """Inicializar todas las cámaras configuradas."""
        if not self.config:
            return
            
        for camera_config in self.config['cameras']:
            if camera_config['enabled']:
                camera_id = camera_config['id']
                self.cameras[camera_id] = CameraStream(camera_config)
                self.cameras[camera_id].start()
                print(f"📹 Cámara {camera_id} inicializada")
    
    def _setup_routes(self):
        """Configurar rutas de Flask."""
        
        @self.app.route('/')
        def index():
            """Página principal con previsualización de cámaras."""
            return render_template('index.html', cameras=self.config['cameras'] if self.config else [])
        
        @self.app.route('/video_feed/<camera_id>')
        def video_feed(camera_id):
            """
            Stream de video MJPEG para una cámara específica.
            
            Args:
                camera_id (str): ID de la cámara
                
            Returns:
                Response: Stream MJPEG
            """
            if camera_id not in self.cameras:
                return "Cámara no encontrada", 404
            
            def generate_frames():
                """Generar frames MJPEG."""
                while True:
                    frame = self.cameras[camera_id].get_frame()
                    
                    if frame is not None:
                        # Codificar frame como JPEG
                        ret, buffer = cv2.imencode('.jpg', frame, 
                                                 [cv2.IMWRITE_JPEG_QUALITY, 85])
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
                    time.sleep(0.033)  # ~30 FPS
            
            return Response(generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/video_feed')
        def video_feed_default():
            """Stream de video para la primera cámara disponible."""
            if not self.cameras:
                return "No hay cámaras disponibles", 404
            
            # Usar la primera cámara disponible
            first_camera_id = list(self.cameras.keys())[0]
            return video_feed(first_camera_id)
        
        @self.app.route('/status')
        def status():
            """Endpoint de estado del sistema."""
            status_info = {
                'timestamp': datetime.now().isoformat(),
                'cameras': {}
            }
            
            for camera_id, camera in self.cameras.items():
                status_info['cameras'][camera_id] = {
                    'name': camera.camera_name,
                    'connected': camera.cap is not None and camera.cap.isOpened(),
                    'last_frame': camera.last_frame_time
                }
            
            return status_info
    
    def run(self, host='0.0.0.0', port=None, debug=False):
        """
        Ejecutar servidor Flask.
        
        Args:
            host (str): Host del servidor
            port (int): Puerto del servidor
            debug (bool): Modo debug
        """
        if port is None:
            port = self.config.get('flask_port', 5000) if self.config else 5000
        
        print("🌐 Iniciando Servidor Web de Previsualización")
        print("=" * 50)
        print(f"🔗 URL: http://{host}:{port}")
        print(f"📊 Estado: http://{host}:{port}/status")
        print("=" * 50)
        
        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo servidor web...")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Limpiar recursos al cerrar."""
        for camera in self.cameras.values():
            camera.stop()
        print("✅ Servidor web detenido")


def main():
    """Función principal."""
    try:
        server = RTSPWebServer()
        if server.config:
            server.run()
        else:
            print("❌ No se pudo cargar la configuración")
    except Exception as e:
        print(f"❌ Error fatal: {e}")


if __name__ == "__main__":
    main()
