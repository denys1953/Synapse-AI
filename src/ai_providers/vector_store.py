from src.config import settings

import chromadb
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor


class VectorService:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMADB_HOST, 
            port=settings.CHROMADB_PORT
        )
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL_NAME, temperature=0.5)

    def get_collection(self, notebook_id: int):
        collection_name = f"notebook_{notebook_id}" 
        
        return Chroma(
            collection_name=collection_name,
            client=self.client,
            embedding_function=self.embeddings
        ) 

    def get_retriever(self, notebook_id: int, mode: str = "base", source_ids: list[int] = None):
        db = self.get_collection(notebook_id)

        search_filter = {"notebook_id": notebook_id}
        if source_ids:
            search_filter = {
                "$and": [
                    {"notebook_id": notebook_id},
                    {"source_id": {"$in": source_ids}}
                ]
            }

        if mode == "mmr":
            return db.as_retriever(search_type="mmr", search_kwargs={"k": 5, "filter": search_filter})

        if mode == "multiquery" and self.llm:
            return MultiQueryRetriever.from_llm(
                retriever=db.as_retriever(search_kwargs={"filter": search_filter}), 
                llm=self.llm
            )

        return db.as_retriever(search_kwargs={"k": 5, "filter": search_filter})