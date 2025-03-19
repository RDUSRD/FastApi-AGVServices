from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import secrets
import os
from core import oauth, templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/oauth/authorize")
async def oauth_authorize(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    redirect_uri = os.getenv("AUTHENTIK_REDIRECT_URI")
    return await oauth.authentik.authorize_redirect(request, redirect_uri, state=state)

@router.get("/oauth/callback")
async def oauth_callback(request: Request):
    expected_state = request.session.get("oauth_state")
    received_state = request.query_params.get("state")
    if not expected_state or expected_state != received_state:
        raise HTTPException(status_code=400, detail="Mismatching state parameter.")
    request.session.pop("oauth_state", None)
    token_data = await oauth.authentik.authorize_access_token(request)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No se recibió el access token")
    request.session["token"] = access_token
    return RedirectResponse(url="/dashboard")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@router.get("/logout-authentik")
async def logout_authentik(request: Request):
    request.session.clear()
    return RedirectResponse(url=os.getenv("AUTHENTIK_LOGOUT_URL"))