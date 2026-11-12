from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra = "ignore")


    database_url: str
    base_url: str = "http://localhost:8000"
    redis_url: str = "reddis://localhost:6379/0"
    admin_token: str = ""
    safe_browsing_api_key: str = ""

    links_per_key_per_day: int = 100
    requests_per_ip_per_minute: int = 120

    default_block_ttl_seconds: int = 900  
    trust_proxy_headers: bool = False

@lru_cache
def get_settings()-> Settings:
    return Settings() 
