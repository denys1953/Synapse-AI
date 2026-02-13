from src.users import models
from src.users.schemas import Token, UserCreate
from .security import create_access_token, hash_password, verify_password

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_user_by_email(db: AsyncSession, email: str) -> models.User | None:
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_new_user(db: AsyncSession, user_data: UserCreate) -> models.User:
    query = select(models.User).where(models.User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User with this email already exists"
        )
    
    new_user = models.User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Token | None:
    user = await get_user_by_email(db, email)
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password"
        )
    
    token = create_access_token(data={"sub": str(user.email)})
    return Token(access_token=token)

async def get_or_create_google_user(db: AsyncSession, google_user_info: dict) -> models.User:
    email = google_user_info.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account does not have an email.")

    user = await get_user_by_email(db, email)
    if user:
        return user

    new_user = models.User(
        email=email,
        full_name=google_user_info.get("name"),
        hashed_password=None,
        is_active=True
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user