from fastapi import Depends, FastAPI, UploadFile, File
from starlette.middleware.sessions import SessionMiddleware

from src.auth.router import router as auth_router
from src.notebooks.router import router as notebooks_router
from src.config import settings

swagger_params = {
    "persistAuthorization": True
}

app = FastAPI(
    swagger_ui_parameters=swagger_params
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

@app.get("/")
async def main():
    return {"Status": "OK"}


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(notebooks_router, prefix="/notebooks", tags=["Notebooks"])
