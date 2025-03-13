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
   SESSION_SECRET_KEY=TuClaveSecreta

   # URL base del servidor Authentik.
   AUTHENTIK_URL=http://tuservidor:9000

   # Identificador único de la aplicación registrado en Authentik para el flujo OAuth.
   AUTHENTIK_CLIENT_ID=TuClientID

   # Secreto de la aplicación para autenticarse de forma segura en Authentik.
   AUTHENTIK_CLIENT_SECRET=TuClientSecret

   # URL de callback para el flujo OAuth.
   OAUTH_CALLBACK_URL=http://localhost:8000/oauth/callback/

   # URL para obtener el JSON Web Key Set (JWKS) de Authentik.
   AUTHENTIK_JWKS_URL=${AUTHENTIK_URL}/application/o/fastapiruben/jwks/

   # Token interno para acceso a la API interna de Authentik.
   INTERNAL_TOKEN=TuInternalToken
   ```

## Ejecución en Modo Local

Para iniciar el servidor de desarrollo, activa el entorno virtual y ejecuta:

```bash
uvicorn main:app --reload
```

La aplicación estará disponible en `http://localhost:8000`.

## Construir la Imagen Docker

Si prefieres ejecutar la aplicación dentro de un contenedor Docker, sigue estos pasos:

1. **Construir la imagen**

   Asegúrate de tener Docker instalado y ejecuta:

   ```bash
   docker build
   ```

## Ejecución con Docker Compose

El proyecto incluye un archivo `docker-compose.yml` que facilita la gestión del contenedor de la aplicación. Para utilizar Docker Compose, sigue estos pasos:

1. **Construir y levantar el contenedor**

   Desde la raíz del proyecto, ejecuta el siguiente comando para construir la imagen (si es necesario) y levantar el servicio en segundo plano:

   ```bash
   docker-compose up -d
   ```

   Esto leerá las variables de entorno del archivo `.env` y expondrá el servicio en el puerto configurado (por defecto, el puerto 8000).

2. **Verificar que el servicio esté corriendo**

   Puedes ver los contenedores activos con:

   ```bash
   docker-compose ps
   ```

   También puedes revisar los logs para confirmar que la aplicación se inició correctamente:

   ```bash
   docker-compose logs -f
   ```

3. **Acceder a la aplicación**

   Abre tu navegador y visita [http://localhost:8000](http://localhost:8000) para ver la aplicación en ejecución.

4. **Detener y eliminar contenedores**

   Para detener el servicio y remover los contenedores creados, usa:

   ```bash
   docker-compose down
   ```

## Notas Adicionales

- **Actualización de Dependencias:**  
  Cada vez que actualices el archivo `requirements.txt`, puedes reinstalar las dependencias ejecutando:

  ```bash
  pip install -r requirements.txt
  ```

- **Logs y Debug:**  
  Durante el desarrollo, puedes usar el parámetro `--reload` para que el servidor se reinicie automáticamente cuando realices cambios en el código.

- **Entorno de Producción:**  
  Para producción, asegúrate de configurar correctamente las variables de entorno y considerar el uso de un servidor ASGI (por ejemplo, utilizando Gunicorn con Uvicorn workers).

