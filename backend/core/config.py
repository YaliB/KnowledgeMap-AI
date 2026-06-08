from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    #OpenAI
    openai_api_key: str

    #Neo4j
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_dbname: str

    #MongoDB
    mongodb_uri: str
    mongodb_db: str

    #Session
    session_secret: str
    session_expire_days: int

    #File Storage
    upload_dir: str
    max_file_size_mb: int

    #App
    allowed_origins: list[str]

settings = Settings()
