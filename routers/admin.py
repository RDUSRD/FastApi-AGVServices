from fastapi import APIRouter, Request, HTTPException, Query, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from math import ceil
import os
import requests
import jwt
from core import url, templates
from loggers.logger import get_logger

# Crear una instancia del logger para el módulo de administración
logger = get_logger("AdminModule")

router = APIRouter(prefix="/admin")

def get_logged_in_user(request: Request) -> str:
    """
    Devuelve el email del usuario autenticado desde el token almacenado en la sesión,
    o "UnknownUser" si no se encuentra o ocurre un error.
    """
    token = request.session.get('token')
    if token:
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            return decoded_token.get("preferred_username", "UnknownUser")
        except Exception:
            return "UnknownUser"
    return "UnknownUser"

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, page: int = Query(1, ge=1)):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    token = request.session.get('token')
    current_user = get_logged_in_user(request)
    if not token:
        logger.warning("Acceso a /admin/users sin token", extra={"device": device, "user": current_user, "ip": ip})
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/core/users/", headers=headers)
    if response.status_code != 200:
        logger.error("Error al consultar usuarios", extra={"device": device, "user": current_user, "ip": ip})
        raise HTTPException(status_code=response.status_code, detail="Error al consultar usuarios")
    data = response.json()
    all_users = data.get("results", [])
    per_page = 10
    total_pages = ceil(len(all_users) / per_page)
    users_page = all_users[(page - 1) * per_page : page * per_page]
    logger.info("Listado de usuarios obtenido", extra={"device": device, "user": current_user, "ip": ip})
    context = {
        "request": request,
        "users": users_page,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None,
        "pages": list(range(1, total_pages + 1)),
        "current_page": page
    }
    return templates.TemplateResponse("users.html", context)

@router.get("/groups", response_class=HTMLResponse)
async def admin_groups(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    token = request.session.get('token')
    current_user = get_logged_in_user(request)
    if not token:
        logger.warning("Acceso a /admin/groups sin token", extra={"device": device, "user": current_user, "ip": ip})
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/core/groups/", headers=headers)
    if response.status_code != 200:
        logger.error("Error al consultar grupos", extra={"device": device, "user": current_user, "ip": ip})
        raise HTTPException(status_code=response.status_code, detail="Error al consultar grupos")
    groups = response.json().get("results", [])
    logger.info("Listado de grupos obtenido", extra={"device": device, "user": current_user, "ip": ip})
    return templates.TemplateResponse("groups.html", {"request": request, "groups": groups})

@router.get("/roles", response_class=HTMLResponse)
async def admin_roles(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    token = request.session.get('token')
    current_user = get_logged_in_user(request)
    if not token:
        logger.warning("Acceso a /admin/roles sin token", extra={"device": device, "user": current_user, "ip": ip})
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/rbac/roles/", headers=headers)
    if response.status_code != 200:
        logger.error("Error al consultar roles", extra={"device": device, "user": current_user, "ip": ip})
        raise HTTPException(status_code=response.status_code, detail="Error al consultar roles")
    roles = response.json().get("results", [])
    logger.info("Listado de roles obtenido", extra={"device": device, "user": current_user, "ip": ip})
    return templates.TemplateResponse("roles.html", {"request": request, "roles": roles})

@router.get("/scopes", response_class=HTMLResponse)
async def admin_scopes(request: Request):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    token = request.session.get('token')
    current_user = get_logged_in_user(request)
    if not token:
        logger.warning("Acceso a /admin/scopes sin token", extra={"device": device, "user": current_user, "ip": ip})
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/propertymappings/provider/scope/", headers=headers)
    try:
        data = response.json() if response.text.strip() else {}
    except Exception as e:
        logger.error(f"Error al decodificar JSON en scopes: {e}", extra={"device": device, "user": current_user, "ip": ip})
        data = {}
    scopes = data.get("results", [])
    logger.info("Listado de scopes obtenido", extra={"device": device, "user": current_user, "ip": ip})
    return templates.TemplateResponse("create_scope.html", {"request": request, "scopes": scopes})

@router.post("/scopes")
async def create_scope(
    request: Request,
    mapping_name: str = Form(...),
    scope_name: str = Form(...),
    description: str = Form(...),
    expression: str = Form(...)
):
    device = getattr(request.state, "device", "UnknownDevice")
    ip = getattr(request.state, "ip", "UnknownIP")
    token = request.session.get('token')
    current_user = get_logged_in_user(request)
    if not token:
        logger.warning("Intento de crear scope sin token", extra={"device": device, "user": current_user, "ip": ip})
        return RedirectResponse(url="/")
    scope_data = {
        "name": mapping_name,
        "scope_name": scope_name,
        "description": description,
        "expression": expression
    }
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.post(f"{url}/api/v3/propertymappings/provider/scope/", headers=headers, json=scope_data)
    if response.status_code != 201:
        logger.error("Error al crear scope", extra={"device": device, "user": current_user, "ip": ip})
        raise HTTPException(status_code=response.status_code, detail="Error al crear scope")
    logger.info("Scope creado correctamente", extra={"device": device, "user": current_user, "ip": ip})
    return RedirectResponse(url="/admin/scopes", status_code=303)