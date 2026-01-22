from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .constants import SYSTEM_INSTRUCTION, REPHRASE_SYSTEM_INSTRUCTION

# Standalone question rephrasing prompt
rephrase_prompt = ChatPromptTemplate.from_messages([
    ("system", REPHRASE_SYSTEM_INSTRUCTION),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# Main RAG answer prompt
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_INSTRUCTION), 
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])