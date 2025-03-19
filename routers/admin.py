from fastapi import APIRouter, Request, HTTPException, Query, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from math import ceil
import os, requests
from core import url, templates

router = APIRouter(prefix="/admin")

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, page: int = Query(1, ge=1)):
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
    total_pages = ceil(len(all_users) / per_page)
    users_page = all_users[(page - 1) * per_page : page * per_page]
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
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/core/groups/", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al consultar grupos")
    groups = response.json().get("results", [])
    return templates.TemplateResponse("groups.html", {"request": request, "groups": groups})

@router.get("/roles", response_class=HTMLResponse)
async def admin_roles(request: Request):
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/rbac/roles/", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al consultar roles")
    roles = response.json().get("results", [])
    return templates.TemplateResponse("roles.html", {"request": request, "roles": roles})

@router.get("/scopes", response_class=HTMLResponse)
async def admin_scopes(request: Request):
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url="/")
    headers = {"Authorization": f"Bearer {os.getenv('INTERNAL_TOKEN')}"}
    response = requests.get(f"{url}/api/v3/propertymappings/provider/scope/", headers=headers)
    try:
        data = response.json() if response.text.strip() else {}
    except Exception as e:
        print(f"Error decoding JSON: {e}")
        data = {}
    scopes = data.get("results", [])
    return templates.TemplateResponse("create_scope.html", {"request": request, "scopes": scopes})

@router.post("/scopes")
async def create_scope(
    request: Request,
    mapping_name: str = Form(...),
    scope_name: str = Form(...),
    description: str = Form(...),
    expression: str = Form(...)
):
    token = request.session.get('token')
    if not token:
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
        raise HTTPException(status_code=response.status_code, detail="Error al crear scope")
    return RedirectResponse(url="/admin/scopes", status_code=303)