import os
from dotenv import load_dotenv

load_dotenv()  # Load the .env file

SECRET_KEY = "picasso_super_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

