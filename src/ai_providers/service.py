from .vector_store import VectorService
from .schemas import AskQuestionResponse
from .constants import SYSTEM_INSTRUCTION
from src.users.models import User
from src.notebooks.schemas import QuestionRequest

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def format_docs(docs: list[Document]) -> str:
    formatted = []
    for doc in docs:
        s_id = doc.metadata.get("source_id", "N/A")
        page = doc.metadata.get("page", "?") + 1
        content = doc.page_content.replace("\n", " ").strip()
        formatted.append(f"[Source ID: {s_id}, Page: {page}] | Content: {content}")
    return ("\n\n".join(formatted)).replace("{", "{{").replace("}", "}}")

async def find_context(
    notebook_id: int,
    request: dict,
    vector_service: VectorService,
    current_user: User,
):
    retriever = vector_service.get_retriever(
        notebook_id=notebook_id,
        mode=request.mode,
        source_id=request.source_id,
    )

    docs = await retriever.ainvoke(request.question)

    return format_docs(docs)

async def get_llm_answer(
    query: str, 
    context: str, 
    llm: ChatOpenAI
):
    structured_llm = llm.with_structured_output(AskQuestionResponse)

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_INSTRUCTION.format(context=context)),
        ("human", "{question}")
    ])

    chain = chat_prompt | structured_llm

    return await chain.ainvoke({"question": query})
