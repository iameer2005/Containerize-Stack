import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load the .env file from the project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:dev@localhost:5432/tasks"
)

# Redis configuration (stretch goal)
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# Server port
PORT = int(os.getenv("PORT", 3000))
