# llm_config.py
from langchain_groq import ChatGroq

def create_llm():
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0,
        api_key='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'
    )
    return llm
