import os
import time
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from typing import Dict
import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configurar middleware de sesión
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET_KEY"), 
    session_cookie="session", 
    max_age=3600, 
    same_site="lax"
)

url = os.getenv("AUTHENTIK_URL")

# Configurar OAuth
oauth = OAuth()
oauth.register(
    name='authentik',
    client_id=os.getenv("AUTHENTIK_CLIENT_ID"),
    client_secret=os.getenv("AUTHENTIK_CLIENT_SECRET"),
    authorize_url=f'{url}/application/o/authorize/',
    authorize_params=None,
    access_token_url=f'{url}/application/o/token/',
    access_token_params=None,
    # Es importante que Authentik emita también un refresh token
    refresh_token_url=f'{url}/application/o/token/',  
    redirect_uri=os.getenv("OAUTH_CALLBACK_URL"),
    client_kwargs={'scope': 'openid profile email'},
    jwks_uri=os.getenv("AUTHENTIK_JWKS_URL")
)

# Configurar OAuth2AuthorizationCodeBearer
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f'{url}/application/o/authorize/',
    tokenUrl=f'{url}/application/o/token/',
)

templates = Jinja2Templates(directory="templates")

# Ruta de inicio: página de login
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Ruta para iniciar el proceso OAuth
@app.get("/oauth/authorize")
async def oauth_authorize(request: Request):
    redirect_uri = os.getenv("OAUTH_CALLBACK_URL")
    return await oauth.authentik.authorize_redirect(request, redirect_uri)

# Ruta de callback del proceso OAuth
@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    token = await oauth.authentik.authorize_access_token(request)
    # Almacena el access token y, si existe, el refresh token
    request.session['token'] = token['access_token']
    if 'refresh_token' in token:
        request.session['refresh_token'] = token['refresh_token']
    return RedirectResponse(url="/dashboard")

# Función de ayuda para refrescar el token
async def refresh_access_token(request: Request):
    refresh_token = request.session.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No se encontró refresh token en la sesión")
    new_tokens = await oauth.authentik.refresh_token(f'{url}/application/o/token/', refresh_token=refresh_token)
    request.session['token'] = new_tokens['access_token']
    # Actualiza el refresh token si viene en la respuesta
    if 'refresh_token' in new_tokens:
        request.session['refresh_token'] = new_tokens['refresh_token']
    return new_tokens['access_token']

# Ruta del dashboard con control de expiración y refresh
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    try:
        # Decodifica sin verificar la firma para extraer la fecha de expiración
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        exp = decoded_token.get("exp", 0)
        now = int(time.time())
        # Si el token expira en menos de 5 minutos, refresca
        if exp - now < 300:
            token = await refresh_access_token(request)
            decoded_token = jwt.decode(token, options={"verify_signature": False})
    except jwt.ExpiredSignatureError:
        return RedirectResponse(url="/")
    except jwt.InvalidTokenError:
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
    # Redirigir a dashboards diferentes según los grupos del usuario
    if "Administrador" in user_info["groups"]:
        return templates.TemplateResponse("dashboard_admin.html", {"request": request, "user_info": user_info})
    elif "Desarrollador" in user_info["groups"]:
        return templates.TemplateResponse("dashboard_desarrollador.html", {"request": request, "user_info": user_info})
    else:
        return templates.TemplateResponse("dashboard_invitado.html", {"request": request, "user_info": user_info})

# Ruta para simular acceso a la API interna usando el token de sesión
@app.get("/internal-api")
async def internal_api(request: Request):
    token = request.session.get('token')
    if not token:
        raise HTTPException(status_code=401, detail="Token no encontrado en la sesión")
    try:
        # Decodifica el token para verificar que sea válido (sin verificar la firma)
        jwt.decode(token, options={"verify_signature": False})
    except jwt.ExpiredSignatureError:
        # Si se detecta expiración, se puede intentar refrescar antes de continuar
        token = await refresh_access_token(request)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Aquí se simula un acceso a la API interna; en un caso real se usaría 'token' en una cabecera de autenticación
    return JSONResponse({"message": "Acceso a la API interna permitido", "token": token})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/logout-authentik")
async def logout_authentik(request: Request):
    request.session.clear()
    return RedirectResponse(url=f'{url}/application/o/fastapiruben/end-session/')

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    token = request.session.get('token')
    if not token:  # Si no está logueado, redirige a login
        return RedirectResponse(url="/")
    # Token fijo para este endpoint interno
    internal_token = os.getenv("INTERNAL_TOKEN")
    headers = {"Authorization": f"Bearer {internal_token}"}
    response = requests.get(f"{url}/api/v3/core/users/", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al consultar usuarios")
    data = response.json()
    users = data.get("results", [])
    return templates.TemplateResponse("users.html", {"request": request, "users": users})