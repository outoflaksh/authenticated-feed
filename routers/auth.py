import pathlib

from datetime import timedelta
from typing import Optional
from urllib import response
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param

from utils.users_utils import get_user, verify_user, hash_password
from utils.token_utils import create_access_token

from models import User, UserInDB, SignupForm, Token

# Auth flow: username and password are sent once and then a token is returned,
# which then has to be included in the headers of any protected route

router = APIRouter()


class BasicAuth(SecurityBase):
    def __init__(self, scheme_name: str = None, auto_error: bool = True):
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "basic":
            if self.auto_error:
                raise HTTPException(status_code=403, detail="Not authenticated")
            else:
                return None
        return param


basic_auth = BasicAuth(auto_error=False)

BASE_DIR = pathlib.Path(__file__).parent.parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

ACCESS_TOKEN_EXPIRE_MINUTES = 30

users_db = [
    {
        "username": "user1",
        "email": "user@email.com",
        "name": "user1",
        "hashed_password": "$2b$12$bTuZG0mNK2ciF1U2viC1YOuiV6cG2FCIzd..wXMBfpqnQCYbzlm6q",
    }
]


@router.get("/", response_class=HTMLResponse)
def sign_in(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def read_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", status_code=201)
def create_user(username: str = Form(), password: str = Form()):
    user = get_user(username, users_db)

    if user:
        raise HTTPException(status_code=400, detail="Username already in use!")

    # user doesn't already exist
    hashed_password = hash_password(password)
    user = UserInDB(
        username=username,
        hashed_password=hashed_password,
    )

    users_db.append(dict(user))

    return {"detail": "User created successfully!"}


@router.post("/login", response_model=Token)
async def route_login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_user(form_data.username, form_data.password, users_db)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/feed")
    response.status_code = 302
    response.set_cookie(key="token", value=access_token)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(key="token")
    response.status_code = 302
    return response
