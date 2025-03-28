# FastAPI-app

Esta es una aplicación simple desarrollada con FastAPI que utiliza Authentik para la autenticación. En este documento se explica cómo instalar las dependencias, configurar el entorno, construir la imagen Docker y ejecutar el contenedor.

## Requisitos

- Python 3.11 o superior.
- [Pip](https://pip.pypa.io/en/stable/)
- (Opcional) [Docker](https://www.docker.com/) para correr la aplicación en un contenedor.

## Instalación y Configuración

1. **Clonar el repositorio**

   ```bash
   git clone https://turepositorio.com/usuario/FastAPI-app.git
   cd FastAPI-app
   ```

2. **Instalar dependencias**

   Se recomienda usar un entorno virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**

   Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido (ajusta los valores según tu configuración):

   ```properties
   # Clave secreta para firmar y validar las sesiones de la aplicación.
   SESSION_SECRET_KEY=RubenKey

   # URL base del servidor Authentik, utilizada para servicios de autenticación y autorización.
   AUTHENTIK_URL=http://agvservicios.dynalias.com:9000

   # Identificador único de la aplicación registrado en Authentik para el flujo OAuth.
   AUTHENTIK_CLIENT_ID=gXLiJXVgp7JLDadAeM9Tg0xSMzRQ2w5sYr4mKJM8

   # Secreto de la aplicación para autenticarse de forma segura en Authentik.
   AUTHENTIK_CLIENT_SECRET=tWwANV4NCRtCwrxxJDjlu42HEZhbCpwy7iYI4IBPdSFJTCl59acMp49mWylnzCv3lBvXzL2w9fHIIXXlSVPFxBgAgbmIH34R2HwmgEmZv6Yatd0lcti79rMZfbil2Ex7

   # URL para acceder al JWKS (JSON Web Key Set) de Authentik, utilizado para validar los tokens JWT.
   AUTHENTIK_JWKS_URL=${AUTHENTIK_URL}/application/o/secondfastapi/jwks/

   # Token interno utilizado para acceder a la API interna de Authentik,
   # por ejemplo, para consultar usuarios, grupos, roles y scopes.
   INTERNAL_TOKEN=s2p6to0iH0zcjYnP8I9fpMjo22Pv1YXYLhkMX3YHhryJw4lc7YVg8M8MX7bH

   # URL base de la aplicación FastAPI (usada internamente y para definir el callback OAuth).
   APP_URL=http://localhost:8000

   # URL callback para el flujo OAuth, utilizada para redirigir al usuario después de autenticarse.
   AUTHENTIK_REDIRECT_URI=${APP_URL}/oauth/callback/

   # URL para terminar la sesión en Authentik (Logout), utilizada para redirigir al usuario al cerrar sesión.
   AUTHENTIK_LOGOUT_URL=${AUTHENTIK_URL}/application/o/secondfastapi/end-session/
   ```

   **Explicación de las variables de entorno:**

   - **SESSION_SECRET_KEY:**  
     Clave para firmar y validar las sesiones de la aplicación.

   - **AUTHENTIK_URL:**  
     URL base del servidor Authentik, utilizada para los endpoints de autenticación y autorización.

   - **AUTHENTIK_CLIENT_ID y AUTHENTIK_CLIENT_SECRET:**  
     Credenciales asignadas cuando registras la aplicación en Authentik para utilizar el flujo OAuth.

   - **AUTHENTIK_JWKS_URL:**  
     URL donde se obtiene el JSON Web Key Set (JWKS) para validar los tokens JWT emitidos por Authentik.

   - **INTERNAL_TOKEN:**  
     Token usado para autenticar peticiones internas a la API de Authentik (por ejemplo, para consultar usuarios, grupos, roles y scopes).

   - **APP_URL:**  
     URL en la que se ejecuta la aplicación FastAPI. Se utiliza para generar el callback OAuth.

   - **AUTHENTIK_REDIRECT_URI:**  
     URI de redirección OAuth; Authentik redirigirá a este endpoint una vez el usuario se autenticado.

   - **AUTHENTIK_LOGOUT_URL:**  
     URL utilizada para cerrar sesión en Authentik, a la que se redirige al efectuar un logout.

## Configuración de Loggers

La configuración de logging se encuentra en el archivo `loggers/logger.py` y está diseñada para proporcionar registros con información adicional que ayuda a la depuración. A continuación se detallan los puntos clave:

- **Uso de `zoneinfo`:**  
  Se utiliza la librería `zoneinfo` (disponible a partir de Python 3.9) para definir la zona horaria (por defecto `"America/Caracas"`). Esto garantiza que los timestamps en los logs se formateen correctamente según la zona horaria configurada. Nota: Al ejecutar la aplicación sin Docker, asegúrate de usar Python 3.9 o superior.

- **Formato Personalizado:**  
  Los logs emplean un formato personalizado en el que se muestran los siguientes campos:
  - **Time:** Fecha y hora.
  - **Level:** Nivel del log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  - **Device:** Información del dispositivo (por ejemplo, el User-Agent), extraída mediante un middleware.
  - **User:** Información del usuario (por ejemplo, correo o username extraído del token).
  - **IP:** La dirección IP del cliente, extraída mediante el middleware.
  - **Func:** La función en la que se realizó el log (puede modificarse mediante el campo extra `custom_func`).
  - **Msg:** El mensaje del log.

- **Rotación de Logs:**  
  Los registros se almacenan en la carpeta `logs` ubicada en la raíz del proyecto. Se utiliza un `RotatingFileHandler` para crear un nuevo archivo diario (nombrado según la fecha, p.ej., `2025-03-28.log`). Cada archivo se rota al alcanzar 10 MB y se mantienen hasta 5 archivos de respaldo.

## Ejecución en Modo Local

Para iniciar el servidor de desarrollo, activa el entorno virtual y ejecuta:

```bash
uvicorn main:app --reload
```

La aplicación estará disponible en [http://localhost:8000](http://localhost:8000).

## Construir la Imagen Docker

Si prefieres ejecutar la aplicación dentro de un contenedor Docker, sigue estos pasos:

1. **Construir la imagen de Docker**

   Asegúrate de tener Docker instalado y ejecuta:

   ```bash
   docker compose build
   ```

## Ejecución con Docker Compose

El proyecto incluye un archivo `docker-compose.yml` que facilita la gestión del contenedor de la aplicación. Para utilizar Docker Compose, sigue estos pasos:

1. **Construir y levantar el contenedor**

   Desde la raíz del proyecto, ejecuta:

   ```bash
   docker-compose up -d
   ```

   Esto leerá las variables de entorno del archivo `.env` y expondrá el servicio en el puerto configurado (por defecto, el 8000).

2. **Verificar que el servicio esté corriendo**

   Verifica los contenedores activos con:

   ```bash
   docker-compose ps
   ```

   Para ver los logs, puedes usar:

   ```bash
   docker-compose logs -f
   ```

3. **Acceder a la aplicación**

   Abre tu navegador y visita [http://localhost:8000](http://localhost:8000) para ver la aplicación en funcionamiento.

4. **Detener y eliminar contenedores**

   Para detener el servicio y remover los contenedores, utiliza:

   ```bash
   docker-compose down
   ```

## Notas Adicionales

- **Actualización de Dependencias:**  
  Si actualizas el archivo `requirements.txt`, reinstala las dependencias ejecutando:

  ```bash
  pip install -r requirements.txt
  ```

- **Logs y Depuración:**  
  Durante el desarrollo, puedes usar el parámetro `--reload` para que el servidor se reinicie automáticamente cuando realices cambios en el código.

- **Entorno de Producción:**  
  Para producción, configura adecuadamente las variables de entorno y considera el uso de un servidor ASGI robusto (por ejemplo, Gunicorn con Uvicorn workers).

---

Esta documentación brinda una descripción completa de la aplicación, desde su instalación hasta la configuración de loggers, teniendo en cuenta la zona horaria con `zoneinfo` y la persistencia de logs en la carpeta `logs`.
