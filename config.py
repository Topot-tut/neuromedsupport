import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
ADMIN_USERS_ID = list(map(int, os.getenv("ADMIN_USERS_ID").split(',')))
TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')
AI_TOKEN = os.getenv('AI_TOKEN')