import os

from dotenv import load_dotenv

load_dotenv()

curr_env = os.environ["MODE"] if "MODE" in os.environ else "development"
DB_URL = "" if curr_env == "production" else "localhost"
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
TIMEZONE = os.getenv("TIMEZONE")
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
APP_NAME = os.getenv("CONSUMER_APP_NAME")
SIGNING_KEY = os.getenv("SIGNING_KEY")
OAUTH_MWURI = (
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
    "APP_SECRET_KEY" : APP_SECRET_KEY,
    "APP_NAME" : APP_NAME,
    "SIGNING_KEY" : SIGNING_KEY
}
