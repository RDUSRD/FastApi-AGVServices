import os
import time
import secrets
from fastapi.staticfiles import StaticFiles
import jwt  # Usado para decodificar tokens JWT sin verificación de firma
import requests
import json
from math import ceil
from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth  # type: ignore # Integración de OAuth con Starlette/FastAPI
from starlette.middleware.sessions import SessionMiddleware
from typing import Dict
from dotenv import load_dotenv # type: ignore

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Crear la aplicación FastAPI
app = FastAPI()

# Configurar el middleware de sesiones. Se usa para mantener el estado de la sesión (ej. token OAuth)
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET_KEY"),  # Clave secreta para firmar la sesión
    session_cookie="session", 
    max_age=3600,  # La sesión dura 1 hora
    same_site="lax"
)

# Montar la carpeta de archivos estáticos (css, imágenes, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# URL base de Authentik (obtenida de las variables de entorno)
url = os.getenv("AUTHENTIK_URL")

# Configuración de OAuth usando Authlib
oauth = OAuth()
oauth.register(
    name='authentik',
    client_id=os.getenv("AUTHENTIK_CLIENT_ID"),
    client_secret=os.getenv("AUTHENTIK_CLIENT_SECRET"),
    authorize_url=f'{url}/application/o/authorize/',
    authorize_params=None,
    access_token_url=f'{url}/application/o/token/',
    access_token_params=None,
    refresh_token_url=f'{url}/application/o/token/',  # Se utiliza para refrescar el token
    redirect_uri=os.getenv("AUTHENTIK_REDIRECT_URI"),
    client_kwargs={'scope': 'openid profile email offline_access'},
    jwks_uri=os.getenv("AUTHENTIK_JWKS_URL")
)

# Configuración del esquema OAuth2 para autorización con código
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f'{url}/application/o/authorize/',
    tokenUrl=f'{url}/application/o/token/',
)

# Configuración de Jinja2 para renderizar las plantillas HTML en la carpeta "templates"
templates = Jinja2Templates(directory="templates")

###############################################################################
# Ruta raíz: Página de login
###############################################################################
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """
    Ruta de inicio que muestra la página de login.
    """
    return templates.TemplateResponse("login.html", {"request": request})


###############################################################################
# Ruta para iniciar el proceso OAuth
###############################################################################
@app.get("/oauth/authorize")
async def oauth_authorize(request: Request):
    """
    Inicia el proceso OAuth redirigiendo al usuario a Authentik para autorización.
    Genera un estado (state) único que se guarda en la sesión y se envía a Authentik.
    """
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    redirect_uri = os.getenv("AUTHENTIK_REDIRECT_URI")
    # Redirige a la URL de autorización con el state para evitar ataques CSRF
    return await oauth.authentik.authorize_redirect(request, redirect_uri, state=state)


###############################################################################
# Ruta de callback del proceso OAuth
###############################################################################
@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """
    Esta ruta se llama como callback desde Authentik una vez que el usuario autoriza.
    Verifica que el parámetro state coincida con el almacenado en la sesión.
    Extrae el access token y lo guarda en la sesión.
    """
    expected_state = request.session.get("oauth_state")
    received_state = request.query_params.get("state")
    if not expected_state or expected_state != received_state:
        raise HTTPException(status_code=400, detail="Mismatching state parameter.")
    
    # Limpia el state después de su verificación
    request.session.pop("oauth_state", None)
    
    token_data = await oauth.authentik.authorize_access_token(request)
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="No se recibió el access token")
    
    # Guardar el token en la sesión para futuras solicitudes
    request.session["token"] = access_token

    return RedirectResponse(url="/dashboard")


###############################################################################
# Ruta del Dashboard: Diferentes vistas según los grupos del usuario
###############################################################################
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Muestra el dashboard correspondiente según el grupo del usuario.
    Primero se verifica que el token de sesión sea válido y no esté expirado.
    Se decodifica el token para extraer información del usuario.
    Según los grupos, se redirige a dashboards diferentes:
      - "Administrador" -> dashboard_admin.html
      - "Desarrollador" -> dashboard_desarrollador.html
      - Por defecto (invitado) -> dashboard_invitado.html
    """
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    try:
        # Se decodifica el token sin verificar la firma (solo para obtener los datos)
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        exp = decoded_token.get("exp", 0)
        now = int(time.time())
        if now >= exp:
            print("Token expirado")
            request.session.clear()
            return RedirectResponse(url="/")
    except jwt.ExpiredSignatureError:
        print("Token expirado (exception)")
        request.session.clear()
        return RedirectResponse(url="/")
    except jwt.InvalidTokenError:
        print("Token inválido")
        request.session.clear()
        return RedirectResponse(url="/")
    
    user_info = {
        "email": decoded_token.get("email"),
        "email_verified": decoded_token.get("email_verified"),
        "name": decoded_token.get("name"),
        "given_name": decoded_token.get("given_name"),
        "preferred_username": decoded_token.get("preferred_username"),
        "nickname": decoded_token.get("nickname"),
        "groups": decoded_token.get("groups"),
        "uid": decoded_token.get("uid")
    }
    if not user_info["email"]:
        return RedirectResponse(url="/")
    if "Administrador" or "authentik Admins" in user_info["groups"]:
        return templates.TemplateResponse("dashboard_admin.html", {"request": request, "user_info": user_info})
    elif "Desarrollador" in user_info["groups"]:
        return templates.TemplateResponse("dashboard_desarrollador.html", {"request": request, "user_info": user_info})
    else:
        return templates.TemplateResponse("dashboard_invitado.html", {"request": request, "user_info": user_info})


###############################################################################
# Ruta para simular acceso a una API interna
###############################################################################
@app.get("/internal-api")
async def internal_api(request: Request):
    """
    Simula un acceso a una API interna.
    Verifica que el token de sesión exista y sea válido.
    En un caso real se usaría 'token' en la cabecera de autenticación de otra API.
    """
    token = request.session.get('token')
    if not token:
        raise HTTPException(status_code=401, detail="Token no encontrado en la sesión")
    try:
        jwt.decode(token, options={"verify_signature": False})
    except jwt.ExpiredSignatureError:
        request.session.clear()
        return RedirectResponse(url="/")
    except jwt.InvalidTokenError:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return JSONResponse({"message": "Acceso a la API interna permitido", "token": token})


###############################################################################
# Rutas de Logout
###############################################################################
@app.get("/logout")
async def logout(request: Request):
    """
    Cierra la sesión del usuario eliminando la información almacenada.
    """
    request.session.clear()
    return RedirectResponse(url="/")


@app.get("/logout-authentik")
async def logout_authentik(request: Request):
    """
    Cierra la sesión local y redirige a la URL de logout de Authentik.
    """
    request.session.clear()
    return RedirectResponse(url=os.getenv("AUTHENTIK_LOGOUT_URL"))


###############################################################################
# Rutas de Administración de Usuarios, Grupos y Roles
###############################################################################

# Usuarios
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, page: int = Query(1, ge=1)):
    """
    Obtiene la lista de usuarios desde la API de Authentik.
    Implementa paginación (10 usuarios por página) y renderiza la plantilla 'users.html'.
    """
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/core/users/", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al consultar usuarios")
    
    data = response.json()
    all_users = data.get("results", [])
    
    per_page = 10
    total = len(all_users)
    total_pages = ceil(total / per_page)
    
    start = (page - 1) * per_page
    end = page * per_page
    users_page = all_users[start:end]
    
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None
    pages = list(range(1, total_pages + 1))
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users_page,
        "prev_page": prev_page,
        "next_page": next_page,
        "pages": pages,
        "current_page": page
    })

# Grupos
@app.get("/admin/groups", response_class=HTMLResponse)
async def admin_groups(request: Request):
    """
    Obtiene la lista de grupos desde la API de Authentik y renderiza la plantilla 'groups.html'.
    """
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/core/groups/", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al consultar grupos")
    data = response.json()
    groups = data.get("results", [])
    return templates.TemplateResponse("groups.html", {"request": request, "groups": groups})

# Roles
@app.get("/admin/roles", response_class=HTMLResponse)
async def admin_roles(request: Request):
    """
    Obtiene la lista de roles desde la API de Authentik y renderiza la plantilla 'roles.html'.
    """
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/rbac/roles/", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al consultar roles")
    data = response.json()
    roles = data.get("results", [])
    return templates.TemplateResponse("roles.html", {"request": request, "roles": roles})

###############################################################################
# Rutas de Administración de Scopes (Mappings)
###############################################################################

# GET para listar scopes
@app.get("/admin/scopes", response_class=HTMLResponse)
async def admin_scopes(request: Request):
    """
    Obtiene la lista de mappings (scopes) desde la API de Authentik.
    Se llama al endpoint correspondiente de la API y se renderiza la plantilla 'create_scope.html'.
    Si la respuesta de la API no es válida, se maneja el error y se define data como un diccionario vacío.
    """
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    
    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"
    }
    response = requests.get(f"{url}/api/v3/propertymappings/provider/scope/", headers=headers)
    
    print("Scopes response status:", response.status_code)
    try:
        if not response.text.strip():
            data = {}
        else:
            data = response.json()
    except Exception as e:
        print(f"Error decoding JSON: {e}")
        data = {}
    
    scopes = data.get("results", [])
    return templates.TemplateResponse("create_scope.html", {"request": request, "scopes": scopes})

# POST para crear un nuevo scope (mapping)
@app.post("/admin/scopes")
async def create_scope(
    request: Request,
    mapping_name: str = Form(...),
    scope_name: str = Form(...),
    description: str = Form(...),
    expression: str = Form(...)
):
    """
    Recibe los datos del formulario para crear un nuevo scope mapping en Authentik.
    Se extraen los campos enviados por el formulario: mapping_name, scope_name, description y expression.
    Se arma un diccionario 'scope_data' con estos valores y se realiza una petición POST a la API de Authentik.
    En caso de error en la creación, se lanza una excepción HTTP; de lo contrario, se redirige al listado de scopes.
    """
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    
    # Armar el diccionario a enviar a la API basado en los datos del formulario
    scope_data = {
        "name": mapping_name,
        "scope_name": scope_name,
        "description": description,
        "expression": expression
    }
    
    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"
    }
    response = requests.post(f"{url}/api/v3/propertymappings/provider/scope/", headers=headers, json=scope_data)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code, detail="Error al crear scope")
    return RedirectResponse(url="/admin/scopes", status_code=303)