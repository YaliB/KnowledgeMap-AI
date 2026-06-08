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
    max_file_size_mb: int

    #S3
    use_s3: bool = False
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = ""

    #App
    allowed_origins: list[str]

settings = Settings()
