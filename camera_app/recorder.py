#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Grabación de Cámaras RTSP
====================================

Este script graba continuamente streams RTSP usando FFmpeg.
Incluye reconexión automática y segmentación de archivos.

INSTRUCCIONES DE INSTALACIÓN DE FFMPEG EN WINDOWS:
1. Descargar FFmpeg desde: https://ffmpeg.org/download.html
2. Extraer el archivo ZIP a C:\ffmpeg
3. Agregar C:\ffmpeg\bin al PATH del sistema
4. Verificar instalación: ffmpeg -version

Autor: Sistema de Vigilancia RTSP
Fecha: 2024
"""

import json
import os
import subprocess
import time
import signal
import sys
from datetime import datetime
from pathlib import Path


class RTSPRecorder:
    """Clase para manejar la grabación de streams RTSP."""
    
    def __init__(self, config_path="config.json"):
        """
        Inicializar el grabador con configuración.
        
        Args:
            config_path (str): Ruta al archivo de configuración
        """
        self.config = self._load_config(config_path)
        self.processes = {}  # Para almacenar procesos FFmpeg por cámara
        self.running = True
        
        # Configurar manejo de señales para cierre graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path):
        """Cargar configuración desde archivo JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo de configuración: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error al leer configuración JSON: {e}")
            sys.exit(1)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de cierre del sistema."""
        print("\n🛑 Recibida señal de cierre. Deteniendo grabaciones...")
        self.running = False
        self.stop_all_recordings()
        sys.exit(0)
    
    def _create_recordings_directory(self):
        """Crear directorio de grabaciones si no existe."""
        recordings_path = Path(self.config['recordings_path'])
        recordings_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Directorio de grabaciones: {recordings_path.absolute()}")
    
    def _build_ffmpeg_command(self, camera):
        """
        Construir comando FFmpeg para una cámara específica.
        
        Args:
            camera (dict): Configuración de la cámara
            
        Returns:
            list: Comando FFmpeg como lista de argumentos
        """
        # Obtener timestamp actual para el nombre del archivo
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"{self.config['recordings_path']}/{camera['id']}_{timestamp}.mp4"
        
        # Comando FFmpeg optimizado para streams RTSP (sin segmentación)
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',           # Usar TCP para mayor estabilidad
            '-i', camera['rtsp_url'],           # URL de entrada RTSP
            '-c:v', 'copy',                     # Copiar video sin transcodificación
            '-c:a', 'aac',                      # Convertir audio a AAC (compatible con MP4)
            '-t', str(self.config['segment_duration']),  # Duración de grabación (segundos)
            '-loglevel', 'error',               # Solo mostrar errores
            '-y',                               # Sobrescribir archivos existentes
            output_file
        ]
        
        return cmd
    
    def start_recording(self, camera):
        """
        Iniciar grabación para una cámara específica.
        
        Args:
            camera (dict): Configuración de la cámara
        """
        camera_id = camera['id']
        
        if camera_id in self.processes and self.processes[camera_id].poll() is None:
            print(f"⚠️  La cámara {camera_id} ya está grabando")
            return
        
        try:
            cmd = self._build_ffmpeg_command(camera)
            print(f"🎥 Iniciando grabación para {camera['name']} ({camera_id})")
            print(f"📡 URL: {camera['rtsp_url']}")
            
            # Iniciar proceso FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Verificar si el proceso se inició correctamente
            time.sleep(2)  # Esperar un momento para que FFmpeg se inicie
            if process.poll() is not None:
                # El proceso terminó inmediatamente, leer errores
                stdout, stderr = process.communicate()
                print(f"❌ FFmpeg falló inmediatamente:")
                print(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
                print(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
                return
            
            self.processes[camera_id] = process
            print(f"✅ Grabación iniciada - PID: {process.pid}")
            
        except FileNotFoundError:
            print("❌ Error: FFmpeg no encontrado. Verifica la instalación.")
            print("💡 Instrucciones de instalación en los comentarios del archivo.")
        except Exception as e:
            print(f"❌ Error al iniciar grabación para {camera_id}: {e}")
    
    def stop_recording(self, camera_id):
        """
        Detener grabación para una cámara específica.
        
        Args:
            camera_id (str): ID de la cámara
        """
        if camera_id in self.processes:
            process = self.processes[camera_id]
            if process.poll() is None:  # Si el proceso aún está corriendo
                print(f"🛑 Deteniendo grabación para {camera_id} (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
            del self.processes[camera_id]
    
    def stop_all_recordings(self):
        """Detener todas las grabaciones activas."""
        for camera_id in list(self.processes.keys()):
            self.stop_recording(camera_id)
    
    def check_and_restart_recordings(self):
        """Verificar y reiniciar grabaciones que hayan fallado o completado."""
        for camera in self.config['cameras']:
            if not camera['enabled']:
                continue
                
            camera_id = camera['id']
            
            # Si no hay proceso o el proceso terminó (completado o falló)
            if camera_id not in self.processes or self.processes[camera_id].poll() is not None:
                if camera_id in self.processes:
                    # El proceso terminó, verificar si fue exitoso
                    process = self.processes[camera_id]
                    if process.returncode == 0:
                        print(f"✅ Archivo completado para {camera['name']} ({camera_id})")
                    else:
                        print(f"⚠️  Grabación falló para {camera['name']} ({camera_id})")
                    del self.processes[camera_id]
                
                # Iniciar nueva grabación
                print(f"🔄 Iniciando nueva grabación para {camera['name']} ({camera_id})")
                self.start_recording(camera)
    
    def run(self):
        """Ejecutar el grabador principal con reconexión automática."""
        print("🚀 Iniciando Sistema de Grabación RTSP")
        print("=" * 50)
        
        # Crear directorio de grabaciones
        self._create_recordings_directory()
        
        # Iniciar grabaciones para todas las cámaras habilitadas
        for camera in self.config['cameras']:
            if camera['enabled']:
                self.start_recording(camera)
        
        print(f"\n📊 Estado: {len(self.processes)} grabaciones activas")
        print("💡 Presiona Ctrl+C para detener todas las grabaciones")
        print("=" * 50)
        
        # Bucle principal con verificación periódica
        try:
            while self.running:
                time.sleep(self.config['ffmpeg_reconnect_delay'])
                
                # Verificar y reiniciar grabaciones si es necesario
                self.check_and_restart_recordings()
                
                # Mostrar estado cada 5 minutos
                if int(time.time()) % 300 == 0:
                    active_count = sum(1 for p in self.processes.values() if p.poll() is None)
                    print(f"📊 Estado: {active_count} grabaciones activas - {datetime.now().strftime('%H:%M:%S')}")
        
        except KeyboardInterrupt:
            print("\n🛑 Interrupción del usuario")
        finally:
            self.stop_all_recordings()
            print("✅ Sistema de grabación detenido")


def main():
    """Función principal."""
    try:
        recorder = RTSPRecorder()
        recorder.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
