import time, jwt
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from core import templates
from loggers.logger import get_logger

logger = get_logger("DashboardModule")
router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    
    token = request.session.get('token')
    if not token:
        logger.warning(
            "No se encontró token en la sesión, redirigiendo a login", 
            extra={"device": device, "user": "Anonymous", "ip": ip}
        )
        return RedirectResponse(url="/")
    
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        # Comprobar expiración del token
        if int(time.time()) >= decoded_token.get("exp", 0):
            logger.info(
                "El token ha expirado, limpiando sesión y redirigiendo a login", 
                extra={"device": device, "user": decoded_token.get("preferred_username", "UnknownUser"), "ip": ip}
            )
            request.session.clear()
            return RedirectResponse(url="/")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.error(
            f"Error al decodificar el token: {e}", 
            extra={"device": device, "user": "UnknownUser", "ip": ip}
        )
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
        "uid": decoded_token.get("uid"),
        "rif": decoded_token.get("rif"),
        "telefono": decoded_token.get("telefono"),
        "cedula": decoded_token.get("cedula"),
    }
    if not user_info.get("email"):
        logger.warning(
            "El token decodificado no contiene email, redirigiendo", 
            extra={"device": device, "user": "UnknownUser", "ip": ip}
        )
        return RedirectResponse(url="/")
    
    logger.info(
        "Token verificado y usuario autenticado", 
        extra={"device": device, "user": user_info.get("preferred_username", "UnknownUser"), "ip": ip}
    )
    
    if "Administrador" in user_info.get("groups", []) or "authentik Admins" in user_info.get("groups", []):
        logger.info(
            "Mostrando dashboard de Administrador", 
            extra={"device": device, "user": user_info.get("preferred_username", "UnknownUser"), "ip": ip}
        )
        return templates.TemplateResponse("dashboard_admin.html", {"request": request, "user_info": user_info})
    elif "Desarrollador" in user_info.get("groups", []):
        logger.info(
            "Mostrando dashboard de Desarrollador", 
            extra={"device": device, "user": user_info.get("preferred_username", "UnknownUser"), "ip": ip}
        )
        return templates.TemplateResponse("dashboard_desarrollador.html", {"request": request, "user_info": user_info})
    else:
        logger.info(
            "Mostrando dashboard de Invitado", 
            extra={"device": device, "user": user_info.get("preferred_username", "UnknownUser"), "ip": ip}
        )
        return templates.TemplateResponse("dashboard_invitado.html", {"request": request, "user_info": user_info})

@router.get("/internal-api")
async def internal_api(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    token = request.session.get('token')
    if not token:
        logger.warning(
            "Acceso a internal-api sin token", 
            extra={"device": device, "user": "Anonymous", "ip": ip}
        )
        raise HTTPException(status_code=401, detail="Token no encontrado en la sesión")
    try:
        jwt.decode(token, options={"verify_signature": False})
        logger.info(
            "Acceso permitido a internal-api", 
            extra={"device": device, "user": "UnknownUser", "ip": ip}
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.error(
            f"Token inválido en internal-api: {e}", 
            extra={"device": device, "user": "UnknownUser", "ip": ip}
        )
        request.session.clear()
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return JSONResponse({"message": "Acceso a la API interna permitido", "token": token})