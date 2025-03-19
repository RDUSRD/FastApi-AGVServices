import os
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth  # type: ignore # Para el flujo OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv  # type: ignore
# Incluir routers de la aplicación
from routers import auth, dashboard, admin

# Cargar configuración del entorno
load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI()

# Incluir routers de la aplicación
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

# Middleware de sesiones para mantener el estado (por ejemplo, token OAuth)
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET_KEY"),
    session_cookie="session",
    max_age=3600,
    same_site="lax"
)

# Servir archivos estáticos (CSS, imágenes, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# URL base de Authentik (desde .env)
url = os.getenv("AUTHENTIK_URL")

# Configuración del cliente OAuth con Authentik
oauth = OAuth()
oauth.register(
    name='authentik',
    client_id=os.getenv("AUTHENTIK_CLIENT_ID"),
    client_secret=os.getenv("AUTHENTIK_CLIENT_SECRET"),
    authorize_url=f'{url}/application/o/authorize/',
    access_token_url=f'{url}/application/o/token/',
    refresh_token_url=f'{url}/application/o/token/',
    redirect_uri=os.getenv("AUTHENTIK_REDIRECT_URI"),
    client_kwargs={'scope': 'openid profile email offline_access'},
    jwks_uri=os.getenv("AUTHENTIK_JWKS_URL")
)

# Esquema OAuth2 para autorización con código
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f'{url}/application/o/authorize/',
    tokenUrl=f'{url}/application/o/token/',
)

# Configuración de plantillas Jinja2
templates = Jinja2Templates(directory="templates")


