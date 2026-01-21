import uuid

from src.users.models import User
from .models import Notebook, Source
from .schemas import QuestionRequest
from src.ai_providers.vector_store import VectorService

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from pathlib import Path


UPLOAD_DIR = Path("/app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def get_notebook_by_title(title: str, db: AsyncSession):
    query = select(Notebook).where(Notebook.title == title)
    result = await db.execute(query)
    return result.scalars().first()

async def add_notebook(title: str, current_user: User, db: AsyncSession):
    existing_notebook = await get_notebook_by_title(title, db)
    if existing_notebook:
        raise HTTPException(status_code=400, detail="Notebook with this title already exists.")

    new_notebook = Notebook(
        user_id=current_user.id,
        title=title
    )

    db.add(new_notebook)
    await db.commit()
    await db.refresh(new_notebook)
    return new_notebook

async def save_upload_file(
    db: AsyncSession,
    notebook_id: int,
    file,
):
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    dest_path = UPLOAD_DIR / unique_filename

    # Save to disk
    with open(dest_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    new_source = Source(
        notebook_id=notebook_id,
        file_path=str(dest_path),
        title=file.filename,
    )

    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    return new_source

async def send_question_to_llm(
    notebook_id: int,
    request: QuestionRequest,
    vector_service: VectorService,
    current_user: User,
):
    retriever = vector_service.get_retriever(
        notebook_id=notebook_id,
        mode=request.mode,
        source_id=request.source_id,
    )

    docs = await retriever.ainvoke(request.question)

    contexts = [doc.page_content for doc in docs]

    return contexts