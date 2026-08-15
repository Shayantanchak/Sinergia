import os

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Sinergia M&A Engine")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sinergia.db")
    ENV: str = os.getenv("ENV", "development")

settings = Settings()
