from fastapi import Depends, FastAPI, UploadFile, File

from src.auth.dependencies import get_current_user
from src.auth.router import router as auth_router

swagger_params = {
    "persistAuthorization": True
}

app = FastAPI(
    swagger_ui_parameters=swagger_params
)

@app.get("/")
async def main():
    return {"Status": "OK"}


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
