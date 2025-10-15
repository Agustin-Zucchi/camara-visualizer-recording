#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inicio del Sistema de Vigilancia RTSP
==============================================

Script principal para iniciar todos los componentes del sistema:
- Grabación continua (recorder.py)
- Servidor web (app.py)
- Limpieza automática (cleaner.py)

Uso:
    python start_system.py [--no-recorder] [--no-web] [--no-cleaner]

Autor: Sistema de Vigilancia RTSP
Fecha: 2024
"""

import subprocess
import threading
import time
import signal
import sys
import argparse
import os
from pathlib import Path


class SystemManager:
    """Gestor principal del sistema de vigilancia."""
    
    def __init__(self):
        """Inicializar el gestor del sistema."""
        self.processes = {}
        self.running = True
        
        # Configurar manejo de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de cierre del sistema."""
        print("\n🛑 Recibida señal de cierre. Deteniendo sistema...")
        self.running = False
        self.stop_all_processes()
        sys.exit(0)
    
    def start_process(self, name, command, args=None):
        """
        Iniciar un proceso en segundo plano.
        
        Args:
            name (str): Nombre del proceso
            command (str): Comando a ejecutar
            args (list): Argumentos adicionales
        """
        try:
            cmd = [command] + (args or [])
            print(f"🚀 Iniciando {name}...")
            
            process = subprocess.Popen(
                cmd,
                stdout=None,  # No capturar stdout para evitar bloqueos
                stderr=None,  # No capturar stderr para evitar bloqueos
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.processes[name] = process
            print(f"✅ {name} iniciado - PID: {process.pid}")
            
        except FileNotFoundError:
            print(f"❌ Error: No se encontró el comando {command}")
            print(f"💡 Asegúrate de que Python esté instalado y en el PATH")
        except Exception as e:
            print(f"❌ Error iniciando {name}: {e}")
    
    def stop_process(self, name):
        """Detener un proceso específico."""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:
                print(f"🛑 Deteniendo {name} (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
            del self.processes[name]
    
    def stop_all_processes(self):
        """Detener todos los procesos activos."""
        for name in list(self.processes.keys()):
            self.stop_process(name)
    
    def check_processes(self):
        """Verificar estado de todos los procesos."""
        for name, process in list(self.processes.items()):
            if process.poll() is not None:
                print(f"⚠️  {name} se detuvo inesperadamente")
                del self.processes[name]
    
    def run_cleaner_periodically(self):
        """Ejecutar limpieza periódicamente en un hilo separado."""
        while self.running:
            try:
                time.sleep(3600)  # Esperar 1 hora
                if self.running:
                    print("🧹 Ejecutando limpieza automática...")
                    subprocess.run([sys.executable, "cleaner.py"], 
                                 stdout=None, stderr=None)
            except Exception as e:
                print(f"❌ Error en limpieza automática: {e}")
    
    def run(self, start_recorder=True, start_web=True, start_cleaner=True):
        """
        Ejecutar el sistema completo.
        
        Args:
            start_recorder (bool): Iniciar grabación
            start_web (bool): Iniciar servidor web
            start_cleaner (bool): Iniciar limpieza automática
        """
        print("🎥 Sistema de Vigilancia RTSP")
        print("=" * 50)
        
        # Verificar que estamos en el directorio correcto
        if not Path("config.json").exists():
            print("❌ Error: No se encontró config.json")
            print("💡 Asegúrate de ejecutar este script desde el directorio camera_app")
            return
        
        # Iniciar componentes según configuración
        if start_recorder:
            self.start_process("Grabador", sys.executable, ["recorder.py"])
        
        if start_web:
            self.start_process("Servidor Web", sys.executable, ["app.py"])
        
        if start_cleaner:
            # Iniciar limpieza en hilo separado
            cleaner_thread = threading.Thread(target=self.run_cleaner_periodically, daemon=True)
            cleaner_thread.start()
            print("✅ Limpieza automática programada")
        
        print(f"\n📊 Sistema iniciado con {len(self.processes)} componentes activos")
        print("💡 Presiona Ctrl+C para detener todo el sistema")
        print("=" * 50)
        
        # Bucle principal de monitoreo
        try:
            while self.running:
                time.sleep(30)  # Verificar cada 30 segundos
                self.check_processes()
                
                # Mostrar estado cada 5 minutos
                if int(time.time()) % 300 == 0:
                    active_count = len(self.processes)
                    print(f"📊 Estado: {active_count} componentes activos - {time.strftime('%H:%M:%S')}")
        
        except KeyboardInterrupt:
            print("\n🛑 Interrupción del usuario")
        finally:
            self.stop_all_processes()
            print("✅ Sistema detenido completamente")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Sistema de Vigilancia RTSP')
    parser.add_argument('--no-recorder', action='store_true',
                       help='No iniciar el grabador')
    parser.add_argument('--no-web', action='store_true',
                       help='No iniciar el servidor web')
    parser.add_argument('--no-cleaner', action='store_true',
                       help='No iniciar la limpieza automática')
    
    args = parser.parse_args()
    
    try:
        manager = SystemManager()
        manager.run(
            start_recorder=not args.no_recorder,
            start_web=not args.no_web,
            start_cleaner=not args.no_cleaner
        )
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
