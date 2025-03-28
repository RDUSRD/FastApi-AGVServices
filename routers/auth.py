from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import secrets
import os
from core import oauth, templates
from loggers.logger import get_logger

# Crear una instancia del logger para el módulo de autenticación
logger = get_logger("AuthModule")

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    logger.info("Mostrando página de login", extra={"device": device, "user": "Anonymous", "ip": ip, "custom_func": "HomePage"})
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/oauth/authorize")
async def oauth_authorize(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    redirect_uri = os.getenv("AUTHENTIK_REDIRECT_URI")
    logger.info("Iniciando flujo OAuth", extra={"device": device, "user": "Anonymous", "ip": ip})
    return await oauth.authentik.authorize_redirect(request, redirect_uri, state=state)

@router.get("/oauth/callback")
async def oauth_callback(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    expected_state = request.session.get("oauth_state")
    received_state = request.query_params.get("state")
    if not expected_state or expected_state != received_state:
        logger.error("State parameter mismatch in callback", extra={"device": device, "user": "Anonymous", "ip": ip})
        raise HTTPException(status_code=400, detail="Mismatching state parameter.")
    request.session.pop("oauth_state", None)
    token_data = await oauth.authentik.authorize_access_token(request)
    access_token = token_data.get("access_token")
    if not access_token:
        logger.error("No se recibió el access token", extra={"device": device, "user": "Anonymous", "ip": ip})
        raise HTTPException(status_code=400, detail="No se recibió el access token")
    request.session["token"] = access_token
    logger.info("Access token recibido y almacenado en sesión", extra={"device": device, "user": "AuthenticatedUser", "ip": ip})
    return RedirectResponse(url="/dashboard")

@router.get("/logout")
async def logout(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    request.session.clear()
    logger.info("Cierre de sesión local", extra={"device": device, "user": "Anonymous", "ip": ip})
    return RedirectResponse(url="/")

@router.get("/logout-authentik")
async def logout_authentik(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    request.session.clear()
    logger.info("Cierre de sesión en Authentik", extra={"device": device, "user": "Anonymous", "ip": ip})
    return RedirectResponse(url=os.getenv("AUTHENTIK_LOGOUT_URL"))