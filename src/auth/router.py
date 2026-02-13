from src.auth.oauth import oauth
from src.auth.security import create_access_token
from src.database import get_db
from src.users.schemas import Token, UserCreate, UserRead
from .service import authenticate_user, create_new_user, get_or_create_google_user

from starlette.responses import RedirectResponse
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=UserRead)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_new_user(db, user_data)

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    auth_result = await authenticate_user(db, form_data.username, form_data.password)
    return auth_result

@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_auth")

    client = oauth.create_client("google")
    if client is None:
        raise HTTPException(status_code=500, detail="Google OAuth client not configured.")

    return await client.authorize_redirect(request, str(redirect_uri))

@router.get("/google/callback")
async def google_auth(request: Request, db: AsyncSession = Depends(get_db)):
    client = oauth.create_client("google")
    if client is None:
        raise HTTPException(status_code=500, detail="Google OAuth client not configured.")

    try:
        token = await client.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    
    user_info = token.get("userinfo")
    user = await get_or_create_google_user(db, user_info)
    access_token = create_access_token(data={"sub": str(user.email)})

    response = RedirectResponse(url=f"http://localhost:3000/auth-success?token={access_token}")
    return response