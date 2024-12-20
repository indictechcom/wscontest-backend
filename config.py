import os
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

curr_env: str = os.environ["MODE"] if "MODE" in os.environ else "development"
DB_URL: str = "" if curr_env == "production" else "localhost"
DB_USERNAME: Optional[str] = os.getenv("DB_USERNAME")
DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
DB_NAME: Optional[str] = os.getenv("DB_NAME")
TIMEZONE: Optional[str] = os.getenv("TIMEZONE")
CONSUMER_KEY: Optional[str] = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET: Optional[str] = os.getenv("CONSUMER_SECRET")
OAUTH_MWURI: str = (
    "https://meta.wikimedia.org/w/"
    if curr_env == "production"
    else "https://meta.wikimedia.org/w/index.php"
)
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
config = {
    "SQL_URI": f"mariadb+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}:3306/{DB_NAME}",
    "TIMEZONE": TIMEZONE,
    "CONSUMER_KEY": CONSUMER_KEY,
    "CONSUMER_SECRET": CONSUMER_SECRET,
    "OAUTH_MWURI": OAUTH_MWURI,
    "APP_SECRET_KEY" : APP_SECRET_KEY
}

