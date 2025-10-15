// JavaScript para Sistema de Vigilancia de Cámaras

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const gridView = document.getElementById('grid-view');
    const focusView = document.getElementById('focus-view');
    const focusImage = document.getElementById('focus-image');
    const focusTitle = document.getElementById('focus-title');
    const focusSubtitle = document.getElementById('focus-subtitle');
    const backButton = document.getElementById('back-button');
    const stopRecordingBtn = document.getElementById('stop-recording-btn');
    const stopSystemBtn = document.getElementById('stop-system-btn');
    
    // Obtener todos los contenedores de cámara
    const cameraContainers = document.querySelectorAll('.camera-container');
    
    // Añadir event listeners a cada cámara
    cameraContainers.forEach(container => {
        container.addEventListener('click', function() {
            const cameraId = this.dataset.cameraId;
            const cameraName = this.dataset.cameraName;
            const streamImg = this.querySelector('.camera-stream');
            
            if (streamImg && streamImg.src) {
                // Cambiar a vista de enfoque
                showFocusView(streamImg.src, cameraName, cameraId);
            }
        });
        
        // Añadir efecto de hover con información adicional
        container.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        container.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Event listener para el botón de volver
    backButton.addEventListener('click', function() {
        showGridView();
    });
    
    // Event listener para el botón de detener grabación
    stopRecordingBtn.addEventListener('click', function() {
        if (confirm('¿Estás seguro de que quieres detener todas las grabaciones activas?')) {
            stopRecording();
        }
    });
    
    // Event listener para el botón de detener sistema
    stopSystemBtn.addEventListener('click', function() {
        if (confirm('¿Estás seguro de que quieres detener todo el sistema de vigilancia?')) {
            stopSystem();
        }
    });
    
    // Event listener para cerrar con tecla Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !focusView.classList.contains('hidden')) {
            showGridView();
        }
    });
    
    // Función para mostrar vista de enfoque
    function showFocusView(streamUrl, cameraName, cameraId) {
        // Actualizar elementos de la vista de enfoque
        focusImage.src = streamUrl;
        focusTitle.textContent = cameraName;
        focusSubtitle.textContent = `ID: ${cameraId}`;
        
        // Ocultar vista de cuadrícula y mostrar vista de enfoque
        gridView.classList.add('hidden');
        focusView.classList.remove('hidden');
        
        // Añadir animación de entrada
        focusView.style.opacity = '0';
        focusView.style.transform = 'scale(0.9)';
        
        requestAnimationFrame(() => {
            focusView.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            focusView.style.opacity = '1';
            focusView.style.transform = 'scale(1)';
        });
        
        // Enfocar el botón de volver para accesibilidad
        backButton.focus();
        
        // Log para debugging
        console.log(`Vista de enfoque activada para: ${cameraName} (${cameraId})`);
    }
    
    // Función para mostrar vista de cuadrícula
    function showGridView() {
        // Ocultar vista de enfoque y mostrar vista de cuadrícula
        focusView.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        focusView.style.opacity = '0';
        focusView.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            focusView.classList.add('hidden');
            gridView.classList.remove('hidden');
            
            // Resetear estilos de transición
            focusView.style.transition = '';
            focusView.style.opacity = '';
            focusView.style.transform = '';
            
            // Limpiar la imagen para liberar memoria
            focusImage.src = '';
        }, 300);
        
        console.log('Vuelto a vista de cuadrícula');
    }
    
    // Función para manejar errores de imagen
    function handleImageError(img, placeholder) {
        img.style.display = 'none';
        if (placeholder) {
            placeholder.style.display = 'flex';
        }
    }
    
    // Añadir event listeners para manejo de errores de imagen
    const cameraStreams = document.querySelectorAll('.camera-stream');
    cameraStreams.forEach(stream => {
        const container = stream.closest('.camera-container');
        const placeholder = container.querySelector('.camera-loading');
        
        stream.addEventListener('error', function() {
            handleImageError(this, placeholder);
            console.warn(`Error cargando stream para cámara: ${container.dataset.cameraId}`);
        });
        
        stream.addEventListener('load', function() {
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            this.style.display = 'block';
        });
    });
    
    // Función para actualizar streams (útil para debugging)
    function refreshAllStreams() {
        cameraStreams.forEach(stream => {
            const originalSrc = stream.src;
            stream.src = '';
            setTimeout(() => {
                stream.src = originalSrc + '?t=' + Date.now();
            }, 100);
        });
        console.log('Todos los streams actualizados');
    }
    
    // Función para verificar estado de conexión
    function checkStreamStatus() {
        cameraStreams.forEach(stream => {
            const container = stream.closest('.camera-container');
            const cameraId = container.dataset.cameraId;
            
            // Verificar si la imagen se está cargando correctamente
            if (stream.complete && stream.naturalWidth === 0) {
                console.warn(`Stream no disponible para cámara: ${cameraId}`);
            } else if (stream.complete && stream.naturalWidth > 0) {
                console.log(`Stream activo para cámara: ${cameraId}`);
            }
        });
    }
    
    // Verificar estado cada 30 segundos
    setInterval(checkStreamStatus, 30000);
    
    // Añadir funcionalidad de doble clic para pantalla completa
    focusImage.addEventListener('dblclick', function() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            focusView.requestFullscreen().catch(err => {
                console.log('No se pudo activar pantalla completa:', err);
            });
        }
    });
    
    // Manejar cambios de pantalla completa
    document.addEventListener('fullscreenchange', function() {
        if (document.fullscreenElement) {
            console.log('Pantalla completa activada');
        } else {
            console.log('Pantalla completa desactivada');
        }
    });
    
    // Función para obtener información del sistema
    function getSystemInfo() {
        return {
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`,
            viewportSize: `${window.innerWidth}x${window.innerHeight}`,
            timestamp: new Date().toISOString()
        };
    }
    
    // Log información del sistema al cargar
    console.log('Sistema de Vigilancia cargado:', getSystemInfo());
    
    // Función para manejar redimensionamiento de ventana
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            console.log('Ventana redimensionada:', `${window.innerWidth}x${window.innerHeight}`);
        }, 250);
    });
    
    // Función para manejar visibilidad de la página
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('Página oculta - pausando verificación de streams');
        } else {
            console.log('Página visible - reanudando verificación de streams');
            checkStreamStatus();
        }
    });
    
    // Función para detener grabaciones
    function stopRecording() {
        // Mostrar mensaje de confirmación
        stopRecordingBtn.textContent = '🔄 Deteniendo...';
        stopRecordingBtn.disabled = true;
        
        // Intentar detener las grabaciones via API
        fetch('/stop_recordings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                alert('Grabaciones detenidas correctamente');
                stopRecordingBtn.textContent = '✅ Grabaciones Detenidas';
                setTimeout(() => {
                    stopRecordingBtn.textContent = '🎥 Detener Grabación';
                    stopRecordingBtn.disabled = false;
                }, 3000);
            } else {
                throw new Error('Error al detener las grabaciones');
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('Error al detener las grabaciones. Verifica que el sistema de grabación esté ejecutándose.');
            stopRecordingBtn.textContent = '🎥 Detener Grabación';
            stopRecordingBtn.disabled = false;
        });
    }
    
    // Función para detener el sistema
    function stopSystem() {
        // Mostrar mensaje de confirmación
        stopSystemBtn.textContent = '🔄 Deteniendo...';
        stopSystemBtn.disabled = true;
        
        // Intentar detener el sistema via API (si existe)
        fetch('/stop_system', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        }).then(response => {
            if (response.ok) {
                alert('Sistema detenido correctamente');
                window.close();
            } else {
                throw new Error('Error al detener el sistema');
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('Error al detener el sistema via web. Usa Ctrl+C en la terminal.');
            stopSystemBtn.textContent = '🛑 Detener Sistema';
            stopSystemBtn.disabled = false;
        });
    }
    
    // Exponer funciones globales para debugging (opcional)
    window.surveillanceSystem = {
        refreshAllStreams,
        checkStreamStatus,
        showFocusView,
        showGridView,
        getSystemInfo,
        stopRecording,
        stopSystem
    };
    
    console.log('Sistema de Vigilancia inicializado correctamente');
});
