from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra = "ignore")


    database_url: str
    redis_url: str = "reddis://localhost:6379/0"
    admin_token: str = ""
    safe_browsing_api_key: str = ""

    links_per_key_per_day: int = 100
    requests_per_key_per_day:int = 120

@lru_cache
def get_settings()-> Settings:
    return Settings() 
