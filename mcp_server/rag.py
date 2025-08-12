from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
import os

# ---------------------------------------------------------------------------
#  У цьому файлі формується найпростіший RAG-ланцюжок. Ми беремо тексти з
#  каталогу rag_documents, розбиваємо їх на шматочки, будуємо векторний
#  індекс FAISS та повертаємо retriever, який може шукати релевантні фрагменти.
# ---------------------------------------------------------------------------

_DOCS_DIR = Path(__file__).parent / "rag_documents"
_INDEX_PATH = Path(__file__).parent / ".faiss_index"

# 1) Завантаження документів з диску.
def _load_docs():
    docs = []
    for p in _DOCS_DIR.glob("**/*.txt"):
        loader = TextLoader(str(p), encoding="utf-8")
        docs.extend(loader.load())
    return docs

# 2) Створення або відновлення індексу та повернення retriever'а.
def build_or_load_retriever():
    from .config import settings

    # CharacterTextSplitter ділить текст на перекривані шматки,
    # щоб LLM отримував контекст, але не занадто великий.
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(_load_docs())

    # OpenAIEmbeddings перетворює текст на вектори за допомогою моделі OpenAI.
    embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)  # використовує OPENAI_API_KEY з env

    # Найпростіший варіант – перебудовуємо індекс щоразу в оперативній пам'яті.
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})

# ---------------------------------------------------------------------------
#  Альтернативний приклад (закоментовано): як перейти на Chroma або інший
#  постійний Vector DB збереженням індексу на диску.
# ---------------------------------------------------------------------------
# from langchain_community.vectorstores import Chroma
# def build_or_load_retriever():
#     splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
#     docs = splitter.split_documents(_load_docs())
#     embeddings = OpenAIEmbeddings()
#     vectordb = Chroma.from_documents(docs, embeddings, persist_directory=str(_INDEX_PATH))
#     return vectordb.as_retriever(search_kwargs={"k": 4})
