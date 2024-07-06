import os 
from dotenc import load_dotenv 
load_dotenv()

curr_env = os.environ['MODE'] if 'MODE' in os.environ else 'development'
DB_URL = "" if curr_env == 'production' else "localhost"
DB_USERNAME = os.getenv('DB_USERNAME') if curr_env == 'production' else "my_user"
DB_PASSWORD = os.getenv('DB_PASSWORD') if curr_env == 'production' else "my_password"
DB_NAME = os.getenv('DB_NAME') if curr_env == 'production' else "my_database"
TIMEZONE = os.getenv('TIMEZONE')

config = {
    'SQL_URI':   f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}:3306/{DB_NAME}',
    'TIMEZONE': TIMEZONE,
}
