#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Escáner de Cámaras RTSP en la Red
=================================

Script para encontrar cámaras RTSP en la red local.
"""

import subprocess
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def ping_host(ip):
    """Hacer ping a una IP para verificar si está activa."""
    try:
        result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def test_rtsp_port(ip, port=554):
    """Probar si el puerto RTSP está abierto."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_rtsp_connection(ip, port=554):
    """Probar conexión RTSP básica."""
    try:
        # Probar con credenciales comunes
        test_urls = [
            f"rtsp://admin:admin@{ip}:{port}/stream1",
            f"rtsp://admin:123456@{ip}:{port}/stream1", 
            f"rtsp://admin:password@{ip}:{port}/stream1",
            f"rtsp://admin:@{ip}:{port}/stream1",
            f"rtsp://{ip}:{port}/stream1",
            f"rtsp://admin:admin@{ip}:{port}/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://admin:admin@{ip}:{port}/h264/ch1/main/av_stream",
        ]
        
        for url in test_urls:
            try:
                result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', url], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return url
            except:
                continue
        return None
    except:
        return None

def scan_network():
    """Escanear la red en busca de cámaras RTSP."""
    print("🔍 Escaneando red en busca de cámaras RTSP...")
    print("=" * 60)
    
    # Obtener IP de la red local
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = "192.168.0.204"  # IP por defecto
    finally:
        s.close()
    
    network_base = ".".join(local_ip.split(".")[:-1])
    print(f"🌐 Escaneando red: {network_base}.x")
    print(f"🔍 Buscando cámaras RTSP en puerto 554...")
    print("-" * 60)
    
    active_hosts = []
    rtsp_cameras = []
    
    # Escanear hosts activos
    print("📡 Fase 1: Buscando hosts activos...")
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(ping_host, f"{network_base}.{i}"): i for i in range(1, 255)}
        
        for future in futures:
            ip_num = futures[future]
            if future.result():
                ip = f"{network_base}.{ip_num}"
                active_hosts.append(ip)
                print(f"✅ {ip} - Host activo")
    
    print(f"\n📊 Encontrados {len(active_hosts)} hosts activos")
    
    # Probar puertos RTSP
    print("\n📡 Fase 2: Probando puertos RTSP...")
    for ip in active_hosts:
        if test_rtsp_port(ip):
            print(f"🎥 {ip} - Puerto RTSP (554) abierto")
            rtsp_cameras.append(ip)
    
    # Probar conexiones RTSP
    print("\n📡 Fase 3: Probando conexiones RTSP...")
    for ip in rtsp_cameras:
        print(f"🔍 Probando {ip}...")
        working_url = test_rtsp_connection(ip)
        if working_url:
            print(f"✅ {ip} - Cámara RTSP encontrada!")
            print(f"   URL: {working_url}")
        else:
            print(f"❌ {ip} - Puerto abierto pero no responde RTSP")
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL ESCANEO")
    print("=" * 60)
    print(f"🌐 Red escaneada: {network_base}.x")
    print(f"📡 Hosts activos: {len(active_hosts)}")
    print(f"🎥 Cámaras RTSP: {len([ip for ip in rtsp_cameras if test_rtsp_connection(ip)])}")
    
    if active_hosts:
        print(f"\n📋 HOSTS ACTIVOS:")
        for ip in active_hosts:
            print(f"   • {ip}")
    
    if rtsp_cameras:
        print(f"\n🎥 CÁMARAS RTSP ENCONTRADAS:")
        for ip in rtsp_cameras:
            working_url = test_rtsp_connection(ip)
            if working_url:
                print(f"   • {ip} - {working_url}")
            else:
                print(f"   • {ip} - Puerto abierto pero sin respuesta RTSP")

if __name__ == "__main__":
    try:
        scan_network()
    except KeyboardInterrupt:
        print("\n🛑 Escaneo cancelado por el usuario")
    except Exception as e:
        print(f"❌ Error durante el escaneo: {e}")
