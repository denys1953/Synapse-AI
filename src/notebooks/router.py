from src.ai_providers.dependencies import VectorServiceDep
from src.ai_providers.vector_store import VectorService
from src.ai_providers.ingestion import process_pdf_to_vectorstore
from src.auth.dependencies import get_current_user
from src.database import get_db
from src.users.models import User
from .schemas import NotebookSchema, QuestionRequest
from .service import add_notebook, save_upload_file, send_question_to_llm

from fastapi import APIRouter, Depends, HTTPException, UploadFile


router = APIRouter()
vector_service = VectorService()

@router.post("/add", response_model=NotebookSchema)
async def create_notebook(title: str, current_user: User = Depends(get_current_user), db = Depends(get_db)):
    return await add_notebook(title, current_user, db)

@router.post("/source/{notebook_id}/upload")
async def upload_source_to_notebook(
    notebook_id: int, 
    file: UploadFile, 
    current_user: User = Depends(get_current_user), 
    db = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    source = await save_upload_file(db, notebook_id, file)

    try:
        await process_pdf_to_vectorstore(
            file_path=source.file_path, 
            notebook_id=notebook_id,
            source_id=source.id,
            vector_service=vector_service,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")
    
    return {"message": "File uploaded and indexed", "source_id": source.id}

@router.post("/notebook/{notebook_id}/ask")
async def ask_question(
    notebook_id: int,
    request: QuestionRequest,
    vector_service: VectorServiceDep,
    current_user: User = Depends(get_current_user),
):
    return await send_question_to_llm(notebook_id, request, vector_service, current_user)
