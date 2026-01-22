from .vector_store import VectorService
from .schemas import AskQuestionResponse
from .prompts import qa_prompt, rephrase_prompt
from src.users.models import User

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage


def format_docs(docs: list[Document]) -> str:
    formatted = []
    for doc in docs:
        s_id = doc.metadata.get("source_id", "N/A")
        page = doc.metadata.get("page", "?") + 1
        content = doc.page_content.replace("\n", " ").strip()
        formatted.append(f"[Source ID: {s_id}, Page: {page}] | Content: {content}")
    return ("\n\n".join(formatted)).replace("{", "{{").replace("}", "}}")

def prepare_chat_history(db_messages: list) -> list:
    chat_history = []
    for msg in db_messages:
        if msg.role == "human":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))
    return chat_history[::-1]

async def find_context(
    notebook_id: int,
    request: dict,
    vector_service: VectorService,
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
    chat_history: list,
    llm: ChatOpenAI,
):  
    structured_llm = llm.with_structured_output(AskQuestionResponse)

    if chat_history:
        chat_history = prepare_chat_history(chat_history)
        standalone_question = await (rephrase_prompt | structured_llm).ainvoke(
            {
                "input": query, 
                "chat_history": chat_history
            }
        )
        standalone_question = standalone_question.answer
        print("Rephrased question:", standalone_question)
    else:
        standalone_question = query

    chain = qa_prompt | structured_llm

    return await chain.ainvoke(
        {
            "question": standalone_question, 
            "context": context, 
            "chat_history": chat_history
        }
    )
