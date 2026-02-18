import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
import google.generativeai as genai

# 1. Настройка
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

SOURCE_FILE = "training_data/all_transcripts.docx"
CHROMA_PATH = "chroma_db"

if not api_key:
    raise ValueError("[ERROR] GOOGLE_API_KEY not found in .env file")

def get_available_embedding_model():
    """Функция автоматически ищет доступную модель эмбеддинга"""
    print("[INFO] Searching for available embedding models in your Google account...")
    try:
        genai.configure(api_key=api_key)
        for model in genai.list_models():
            if 'embedContent' in model.supported_generation_methods:
                print(f"[OK] Found model: {model.name}")
                return model.name
    except Exception as e:
        print(f"[WARN] Error while searching for models: {e}")
        # Если не удалось найти автоматически, пробуем самую популярную наугад
        return "models/embedding-001"

    return None

def ingest_one_big_file():
    # 2. Выбор модели
    model_name = get_available_embedding_model()
    if not model_name:
        print("[ERROR] No embedding models found! Check your API key.")
        return

    print(f"[INFO] Processing file: {SOURCE_FILE} with model {model_name}")

    if not os.path.exists(SOURCE_FILE):
        print(f"[ERROR] File not found! Please place transcripts in {SOURCE_FILE}")
        return

    # 3. Загрузка
    try:
        loader = Docx2txtLoader(SOURCE_FILE)
        document = loader.load()
        if not document:
             print("[ERROR] File is empty.")
             return
        print(f"[OK] File loaded. Length: {len(document[0].page_content)} characters")
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return

    # 4. Нарезка
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=500,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(document)
    print(f"[OK] File split into {len(chunks)} chunks.")

    # 5. Векторизация и сохранение
    print("[INFO] Creating knowledge base...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        print(f"[SUCCESS] Johnny Harris style saved to '{CHROMA_PATH}'")
    except Exception as e:
        print(f"[ERROR] Failed to create database: {e}")

if __name__ == "__main__":
    ingest_one_big_file()