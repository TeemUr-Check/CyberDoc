from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    langflow_api_url: str = "http://127.0.0.1:7860/api/v1/run"
    langflow_flow_id: str = "62fc74d3-9edf-4d49-b702-51cfe82c976c"
    langflow_api_key: str = "sk-ezs36Qqkpcs1Uw0Hak132-jiHd8597jTWwzTa4pGVVM"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    mistral_api_key: str = ""
    request_timeout: float = 120.0
    frontend_dir: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def langflow_run_url(self) -> str:
        return f"{self.langflow_api_url}/{self.langflow_flow_id}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
