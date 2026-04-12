# dissmodel/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configurações globais da plataforma.
    O Pydantic lê automaticamente do arquivo .env ou das variáveis do sistema.
    """
    # Valor padrão se nada for configurado
    default_output_base: str = "./outputs"
    
    # Futuramente você pode colocar coisas aqui, como:
    # redis_url: str = "redis://localhost:6379/0"
    # minio_endpoint: str = "localhost:9000"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        # Ignora variáveis no .env que não estejam definidas na classe
        extra = "ignore" 

settings = Settings()