from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
import time, jwt
from core import templates

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        if int(time.time()) >= decoded_token.get("exp", 0):
            request.session.clear()
            return RedirectResponse(url="/")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
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
    if "Administrador" in user_info["groups"] or "authentik Admins" in user_info["groups"]:
        return templates.TemplateResponse("dashboard_admin.html", {"request": request, "user_info": user_info})
    elif "Desarrollador" in user_info["groups"]:
        return templates.TemplateResponse("dashboard_desarrollador.html", {"request": request, "user_info": user_info})
    else:
        return templates.TemplateResponse("dashboard_invitado.html", {"request": request, "user_info": user_info})

@router.get("/internal-api")
async def internal_api(request: Request):
    token = request.session.get('token')
    if not token:
        raise HTTPException(status_code=401, detail="Token no encontrado en la sesión")
    try:
        jwt.decode(token, options={"verify_signature": False})
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        request.session.clear()
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return JSONResponse({"message": "Acceso a la API interna permitido", "token": token})