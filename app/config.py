import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Claude API
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application mode
    ADMIN_MODE: bool = os.getenv("ADMIN_MODE", "false").lower() == "true"
    
    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Text processing
    CHUNK_SIZE: int = 500  # Optimized for OpenAI embeddings
    CHUNK_OVERLAP: int = 100
    
    # OpenAI Embedding Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI model
    EMBEDDING_DIMENSIONS: int = 1536  # Output dimensions
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

settings = Settings()