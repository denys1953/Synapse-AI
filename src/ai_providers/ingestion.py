from src.ai_providers.vector_store import VectorService

from fastapi.concurrency import run_in_threadpool
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


async def process_pdf_to_vectorstore(
    file_path: str, 
    notebook_id: int, 
    source_id: int, 
    vector_service: VectorService
):
    loader = PyPDFLoader(file_path)
    documents = await run_in_threadpool(loader.load)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    splits = await run_in_threadpool(text_splitter.split_documents, documents)

    for i, split in enumerate(splits):
        split.metadata["notebook_id"] = notebook_id
        split.metadata["source_id"] = source_id
        split.metadata["chunk_index"] = i

    ids = [f"source_{source_id}_chunk_{i}" for i in range(len(splits))]
    print(ids)

    db = vector_service.get_collection(notebook_id)

    await run_in_threadpool(
        db.add_documents,
        splits,
        ids=ids
    )

    return len(splits)