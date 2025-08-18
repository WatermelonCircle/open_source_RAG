import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Claude API
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    
    # Application mode
    ADMIN_MODE: bool = os.getenv("ADMIN_MODE", "false").lower() == "true"
    
    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Vector database
    CHROMA_PERSIST_DIR: str = "chroma_db"
    COLLECTION_NAME: str = "documents"
    
    # Text processing
    CHUNK_SIZE: int = 500  # Reduced for better chunking
    CHUNK_OVERLAP: int = 100
    
    # Embedding model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

settings = Settings()