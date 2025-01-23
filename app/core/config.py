import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Email Service API"
    VERSION = "1.0.0"
    API_V1_STR = "/api/v1"
    IMAP_HOST = os.getenv("IMAP_HOST", "outlook.office365.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))

settings = Settings() 