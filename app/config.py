import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    LINE_CHANNEL_SECRET: str = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN: str = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    MONTHLY_BUDGET: float = float(os.getenv("MONTHLY_BUDGET", "20000"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")


settings = Settings()
