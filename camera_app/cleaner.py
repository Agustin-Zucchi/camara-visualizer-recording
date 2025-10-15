#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Limpieza Automática de Grabaciones
=============================================

Script para eliminar automáticamente grabaciones antiguas basándose
en la fecha de modificación del sistema de archivos.

Este script está diseñado para ejecutarse periódicamente (ej: cada hora)
usando el Programador de Tareas de Windows o cron en Linux.

INSTRUCCIONES PARA WINDOWS TASK SCHEDULER:
1. Abrir "Programador de tareas" (Task Scheduler)
2. Crear tarea básica
3. Configurar para ejecutar cada hora
4. Acción: Iniciar programa
5. Programa: python.exe
6. Argumentos: C:\ruta\completa\al\cleaner.py
7. Directorio de inicio: C:\ruta\completa\al\camera_app

Autor: Sistema de Vigilancia RTSP
Fecha: 2024
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


class RecordingCleaner:
    """Clase para manejar la limpieza automática de grabaciones."""
    
    def __init__(self, config_path="config.json"):
        """
        Inicializar el limpiador con configuración.
        
        Args:
            config_path (str): Ruta al archivo de configuración
        """
        self.config = self._load_config(config_path)
        self.recordings_path = Path(self.config['recordings_path'])
        self.retention_days = self.config['retention_days']
        self.cutoff_date = datetime.now() - timedelta(days=self.retention_days)
    
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
    
    def _is_old_file(self, file_path):
        """
        Verificar si un archivo es más antiguo que el período de retención.
        
        Args:
            file_path (Path): Ruta al archivo
            
        Returns:
            bool: True si el archivo debe ser eliminado
        """
        try:
            # Usar fecha de modificación del sistema (más confiable)
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_mtime < self.cutoff_date
        except (OSError, ValueError) as e:
            print(f"⚠️  Error verificando fecha de {file_path}: {e}")
            return False
    
    def _is_video_file(self, file_path):
        """
        Verificar si un archivo es un video válido.
        
        Args:
            file_path (Path): Ruta al archivo
            
        Returns:
            bool: True si es un archivo de video
        """
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        return file_path.suffix.lower() in video_extensions
    
    def _get_file_info(self, file_path):
        """
        Obtener información detallada de un archivo.
        
        Args:
            file_path (Path): Ruta al archivo
            
        Returns:
            dict: Información del archivo
        """
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
            }
        except (OSError, ValueError) as e:
            print(f"⚠️  Error obteniendo info de {file_path}: {e}")
            return None
    
    def scan_recordings(self):
        """
        Escanear directorio de grabaciones y clasificar archivos.
        
        Returns:
            tuple: (archivos_a_eliminar, archivos_a_conservar, estadisticas)
        """
        if not self.recordings_path.exists():
            print(f"⚠️  El directorio de grabaciones no existe: {self.recordings_path}")
            return [], [], {'total_files': 0, 'total_size_mb': 0}
        
        files_to_delete = []
        files_to_keep = []
        total_size = 0
        
        print(f"🔍 Escaneando directorio: {self.recordings_path.absolute()}")
        print(f"📅 Eliminando archivos anteriores a: {self.cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Período de retención: {self.retention_days} días")
        print("-" * 60)
        
        try:
            for file_path in self.recordings_path.iterdir():
                if file_path.is_file():
                    file_info = self._get_file_info(file_path)
                    if not file_info:
                        continue
                    
                    total_size += file_info['size_mb']
                    
                    # Solo procesar archivos de video
                    if self._is_video_file(file_path):
                        if self._is_old_file(file_path):
                            files_to_delete.append((file_path, file_info))
                        else:
                            files_to_keep.append((file_path, file_info))
                    else:
                        print(f"⏭️  Saltando archivo no-video: {file_path.name}")
        
        except PermissionError:
            print(f"❌ Error: Sin permisos para acceder a {self.recordings_path}")
            return [], [], {'total_files': 0, 'total_size_mb': 0}
        except Exception as e:
            print(f"❌ Error escaneando directorio: {e}")
            return [], [], {'total_files': 0, 'total_size_mb': 0}
        
        stats = {
            'total_files': len(files_to_delete) + len(files_to_keep),
            'total_size_mb': round(total_size, 2),
            'files_to_delete': len(files_to_delete),
            'files_to_keep': len(files_to_keep)
        }
        
        return files_to_delete, files_to_keep, stats
    
    def delete_old_files(self, files_to_delete):
        """
        Eliminar archivos antiguos.
        
        Args:
            files_to_delete (list): Lista de archivos a eliminar
            
        Returns:
            dict: Estadísticas de eliminación
        """
        deleted_count = 0
        deleted_size = 0
        errors = 0
        
        if not files_to_delete:
            print("✅ No hay archivos para eliminar")
            return {'deleted': 0, 'size_freed_mb': 0, 'errors': 0}
        
        print(f"🗑️  Eliminando {len(files_to_delete)} archivos antiguos...")
        print("-" * 60)
        
        for file_path, file_info in files_to_delete:
            try:
                print(f"🗑️  Eliminando: {file_info['name']} "
                      f"({file_info['size_mb']} MB, {file_info['age_days']} días)")
                
                file_path.unlink()  # Eliminar archivo
                deleted_count += 1
                deleted_size += file_info['size_mb']
                
            except PermissionError:
                print(f"❌ Error: Sin permisos para eliminar {file_info['name']}")
                errors += 1
            except FileNotFoundError:
                print(f"⚠️  Archivo ya eliminado: {file_info['name']}")
            except Exception as e:
                print(f"❌ Error eliminando {file_info['name']}: {e}")
                errors += 1
        
        print("-" * 60)
        print(f"✅ Eliminación completada:")
        print(f"   📁 Archivos eliminados: {deleted_count}")
        print(f"   💾 Espacio liberado: {round(deleted_size, 2)} MB")
        if errors > 0:
            print(f"   ❌ Errores: {errors}")
        
        return {
            'deleted': deleted_count,
            'size_freed_mb': round(deleted_size, 2),
            'errors': errors
        }
    
    def show_summary(self, files_to_keep, stats, deletion_stats):
        """
        Mostrar resumen de la operación de limpieza.
        
        Args:
            files_to_keep (list): Archivos conservados
            stats (dict): Estadísticas de escaneo
            deletion_stats (dict): Estadísticas de eliminación
        """
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE LIMPIEZA")
        print("=" * 60)
        print(f"📁 Total de archivos escaneados: {stats['total_files']}")
        print(f"💾 Tamaño total: {stats['total_size_mb']} MB")
        print(f"🗑️  Archivos eliminados: {deletion_stats['deleted']}")
        print(f"💾 Espacio liberado: {deletion_stats['size_freed_mb']} MB")
        print(f"📦 Archivos conservados: {len(files_to_keep)}")
        
        if deletion_stats['errors'] > 0:
            print(f"❌ Errores durante eliminación: {deletion_stats['errors']}")
        
        print(f"⏰ Fecha de corte: {self.cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Período de retención: {self.retention_days} días")
        print("=" * 60)
    
    def run(self, dry_run=False):
        """
        Ejecutar proceso completo de limpieza.
        
        Args:
            dry_run (bool): Si es True, solo mostrar qué se eliminaría sin eliminar
        """
        print("🧹 Iniciando Limpieza Automática de Grabaciones")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if dry_run:
            print("🔍 MODO DRY-RUN: Solo mostrando qué se eliminaría")
        
        # Escanear archivos
        files_to_delete, files_to_keep, stats = self.scan_recordings()
        
        if not files_to_delete:
            print("✅ No hay archivos para eliminar")
            return
        
        # Mostrar archivos que se eliminarían
        print(f"\n📋 Archivos a eliminar ({len(files_to_delete)}):")
        for file_path, file_info in files_to_delete:
            print(f"   🗑️  {file_info['name']} - {file_info['size_mb']} MB - {file_info['age_days']} días")
        
        if not dry_run:
            # Eliminar archivos
            deletion_stats = self.delete_old_files(files_to_delete)
            self.show_summary(files_to_keep, stats, deletion_stats)
        else:
            print("\n🔍 DRY-RUN: Los archivos NO fueron eliminados")
            print(f"💾 Espacio que se liberaría: {sum(info['size_mb'] for _, info in files_to_delete)} MB")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpieza automática de grabaciones RTSP')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Mostrar qué se eliminaría sin eliminar realmente')
    parser.add_argument('--config', default='config.json',
                       help='Ruta al archivo de configuración')
    
    args = parser.parse_args()
    
    try:
        cleaner = RecordingCleaner(args.config)
        cleaner.run(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n🛑 Operación cancelada por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
