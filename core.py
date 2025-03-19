import os
import secrets
import time
import jwt
import requests
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

url = os.getenv("AUTHENTIK_URL")
templates = Jinja2Templates(directory="templates")
oauth = OAuth()

oauth.register(
    name='authentik',
    client_id=os.getenv("AUTHENTIK_CLIENT_ID"),
    client_secret=os.getenv("AUTHENTIK_CLIENT_SECRET"),
    authorize_url=f'{url}/application/o/authorize/',
    access_token_url=f'{url}/application/o/token/',
    refresh_token_url=f'{url}/application/o/token/',
    redirect_uri=os.getenv("AUTHENTIK_REDIRECT_URI"),
    client_kwargs={'scope': 'openid profile email usuario_venezolano'},
    jwks_uri=os.getenv("AUTHENTIK_JWKS_URL")
)
