# Guía de Instalación - Docling Service

## Instalación Rápida con Docker

### 1. Instalación desde GitHub

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/docling-service.git
cd docling-service

# Configurar variables de entorno (opcional)
cp .env.example .env

# Ejecutar con Docker Compose
docker-compose up -d
```

### 2. Instalación desde Docker Hub (Recomendado)

```bash
# Descargar solo los archivos necesarios
curl -O https://raw.githubusercontent.com/tu-usuario/docling-service/main/docker-compose.prod.yml
curl -O https://raw.githubusercontent.com/tu-usuario/docling-service/main/.env.example

# Configurar
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar
docker-compose -f docker-compose.prod.yml up -d
```

## Instalación en NAS

### Synology DSM

1. **Instalar Docker** desde el Package Center
2. **Crear carpeta** en File Station: `/docker/docling-service`
3. **Subir archivos**:
   - `docker-compose.prod.yml`
   - `.env`
4. **Ejecutar via SSH**:
   ```bash
   cd /volume1/docker/docling-service
   sudo docker-compose -f docker-compose.prod.yml up -d
   ```

### QNAP

1. **Container Station** → Crear → Docker Compose
2. **Pegar contenido** de `docker-compose.prod.yml`
3. **Configurar variables** según tu red
4. **Iniciar**

### TrueNAS Scale

1. **Apps** → Available Applications
2. **Custom App** → Docker Compose
3. **Usar** `docker-compose.prod.yml`
4. **Configurar networking** (bridge mode)

## Instalación Local (Docker Desktop)

### Windows
```powershell
# PowerShell como administrador
git clone https://github.com/tu-usuario/docling-service.git
cd docling-service
docker-compose up -d
```

### macOS
```bash
# Terminal
git clone https://github.com/tu-usuario/docling-service.git
cd docling-service
docker-compose up -d
```

### Linux
```bash
# Terminal
git clone https://github.com/tu-usuario/docling-service.git
cd docling-service
sudo docker-compose up -d
```

## Configuración de Red

### Para uso local (misma máquina)
```bash
# El servicio estará en: http://localhost:8000
```

### Para uso en red local
1. **Encontrar IP** de la máquina servidor:
   ```bash
   # Linux/macOS
   hostname -I
   
   # Windows
   ipconfig | findstr IPv4
   ```

2. **Configurar firewall** (si es necesario):
   ```bash
   # Linux (UFW)
   sudo ufw allow 8000
   
   # Windows
   # Agregar regla en Windows Defender Firewall
   ```

3. **Usar desde otros dispositivos**:
   ```
   http://IP_DEL_SERVIDOR:8000
   ```

## Verificación de Instalación

```bash
# Health check
curl http://localhost:8000/health

# O desde otra máquina
curl http://IP_DEL_SERVIDOR:8000/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "0:05:23",
  "gpu_available": true,
  "hardware": "NVIDIA RTX 4090"
}
```

## Actualizaciones

### Actualizar desde Git
```bash
cd docling-service
git pull origin main
docker-compose up -d --build
```

### Actualizar imagen Docker
```bash
docker-compose pull
docker-compose up -d
```

## Configuraciones Avanzadas

### Con Nginx (Puerto 80)
```bash
docker-compose -f docker-compose.prod.yml --profile nginx up -d
```

### Cambiar puerto
```bash
# Editar .env
PORT=8080

# O usar variable de entorno
PORT=8080 docker-compose up -d
```

### Límites de memoria
```bash
# En docker-compose.yml agregar:
deploy:
  resources:
    limits:
      memory: 4G
```

## Solución de Problemas

### Puerto ocupado
```bash
# Cambiar puerto en .env
PORT=8001
```

### Problemas de permisos
```bash
# Linux - agregar usuario a grupo docker
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar
```

### Memoria insuficiente
```bash
# Verificar disponible
docker system df
docker system prune -f  # Limpiar
```

### Logs del servicio
```bash
docker-compose logs -f docling-service
```