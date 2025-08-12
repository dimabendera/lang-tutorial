from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
import os

_DOCS_DIR = Path(__file__).parent / "rag_documents"
_INDEX_PATH = Path(__file__).parent / ".faiss_index"

# 1) Підготовка документів
def _load_docs():
    docs = []
    for p in _DOCS_DIR.glob("**/*.txt"):
        loader = TextLoader(str(p), encoding="utf-8")
        docs.extend(loader.load())
    return docs

# 2) Створення/завантаження індексу
def build_or_load_retriever():
    from .config import settings

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(_load_docs())
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)  # використовує OPENAI_API_KEY з env

    # Простий варіант: завжди перебудовуємо індекс у пам'яті
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})

# Альтернатива (закоментовано): як перейти на Chroma або інший Vector DB
# from langchain_community.vectorstores import Chroma
# def build_or_load_retriever():
#     splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
#     docs = splitter.split_documents(_load_docs())
#     embeddings = OpenAIEmbeddings()
#     vectordb = Chroma.from_documents(docs, embeddings, persist_directory=str(_INDEX_PATH))
#     return vectordb.as_retriever(search_kwargs={"k": 4})
