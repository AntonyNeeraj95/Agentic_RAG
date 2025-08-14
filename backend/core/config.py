from pydantic import Field

class Settings:
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Agenticrag"
    API_TITLE: str = "Agenticrag API"
    API_DESCRIPTION: str = "Agenticrag API"
    API_VERSION: str = "1.0.0"


settings = Settings()