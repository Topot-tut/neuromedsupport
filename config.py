import datetime
from todoist_api_python.api import TodoistAPI
import logging
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())


ADMIN_USERS_ID = list(map(int, os.environ.get("ADMIN_USERS_ID").split(",")))
TODOIST_API_TOKEN = os.environ.get("TODOIST_API_TOKEN")

AI_TOKEN = os.environ.get("AI_TOKEN")
todoist_api = TodoistAPI(TODOIST_API_TOKEN)
logger = logging.getLogger(__name__)
last_checked = datetime.datetime.utcnow()
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL").split(",")

# Настройки SMTP сервера для отправки email
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = os.environ.get("SMTP_PORT")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

LANGCHAIN_KEY = os.environ.get("LANGCHAIN_KEY")
