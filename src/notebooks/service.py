import uuid

from src.users.models import User
from .models import Notebook, Source, ChatMessage
from .schemas import QuestionRequest
from src.ai_providers.vector_store import VectorService
from src.ai_providers.service import find_context, get_llm_answer, rephrase_user_query

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from pathlib import Path


UPLOAD_DIR = Path("/app/storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def get_notebook_by_title(title: str, db: AsyncSession):
    query = select(Notebook).where(Notebook.title == title)
    result = await db.execute(query)
    return result.scalars().first()

async def get_user_notebooks(user: User, db: AsyncSession, notebook_id: int = None):
    if notebook_id:
        query = select(Notebook).where(Notebook.user_id == user.id, Notebook.id == notebook_id)
    else:
        query = select(Notebook).where(Notebook.user_id == user.id)
    result = await db.execute(query)
    return result.scalars().all()

async def get_notebook_sources(
    notebook_id: int,
    current_user: User,
    db: AsyncSession,
):
    query = select(Notebook).where(Notebook.id == notebook_id, Notebook.user_id == current_user.id).options(selectinload(Notebook.sources))
    result = await db.execute(query)
    notebook = result.scalars().first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found or access denied.")
    
    return notebook.sources

async def get_notebook_chat_history(
    notebook_id: int,
    limit: int | None,
    current_user: User,
    db: AsyncSession,
):
    notebooks = await get_user_notebooks(current_user, db, notebook_id)
    if not notebooks:
        raise HTTPException(status_code=404, detail="Notebook not found or access denied.")
    
    chat_messages = await get_chat_history(db, notebook_id, limit)
    return chat_messages

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

    new_source = Source(notebook_id=notebook_id, file_path=str(dest_path), title=file.filename)

    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    return new_source

async def save_chat_message(
    db: AsyncSession,
    notebook_id: int,
    message_role: str,
    message_content: str,
):
    new_message = ChatMessage(notebook_id=notebook_id, role=message_role, content=message_content)
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message

async def get_chat_history(
    db: AsyncSession,
    notebook_id: int,
    limit: int = 10,
):
    if limit is None:
        query = select(ChatMessage).where(ChatMessage.notebook_id == notebook_id).order_by(ChatMessage.id.desc())
    else:
        query = select(ChatMessage).where(ChatMessage.notebook_id == notebook_id).order_by(ChatMessage.id.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def send_question_to_llm(
    notebook_id: int,
    request: QuestionRequest,
    vector_service: VectorService,
    current_user: User,
    db: AsyncSession,
):
    notebooks = await get_user_notebooks(current_user, db, notebook_id=notebook_id)
    if not notebooks:
        raise HTTPException(status_code=404, detail="Notebook not found or access denied.")
    
    await save_chat_message(db, notebook_id, "human", request.question)

    chat_history = await get_chat_history(db, notebook_id)
    
    standalone_question = await rephrase_user_query(
        query=request.question,
        chat_history=chat_history[1:] if len(chat_history) > 1 else [],
        llm=vector_service.llm
    )
    
    retrieval_request = request.model_copy()
    retrieval_request.question = standalone_question

    context = await find_context(notebook_id, retrieval_request, vector_service)

    response = await get_llm_answer(
        query=standalone_question, 
        context=context, 
        chat_history=chat_history[1:] if len(chat_history) > 1 else [], 
        llm=vector_service.llm
    )

    await save_chat_message(db, notebook_id, "ai", response.answer)

    return response