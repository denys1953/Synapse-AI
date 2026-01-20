from src.users.models import User
from src.database import get_db
from src.users.schemas import Token, UserCreate, UserRead
from .service import authenticate_user, create_new_user

from fastapi import APIRouter, Depends, HTTPException
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