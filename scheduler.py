import datetime
import logging
import requests
from config import TODOIST_API_TOKEN

# Инициализация логгера
logger = logging.getLogger(__name__)
last_checked = datetime.datetime.utcnow()


# Функция для получения задач с Todoist API
def get_tasks():
    url = "https://api.todoist.com/rest/v2/"
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# Функция для получения комментариев к задаче с Todoist API
def get_comments(task_id):
    url = f"https://api.todoist.com/rest/v1/comments?task_id={task_id}"
    headers = {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


# Асинхронная функция для проверки комментариев и отправки уведомлений в Telegram
async def check_for_comments(context):
    global last_checked
    try:
        tasks = get_tasks()
        logger.info(f"Checking {len(tasks)} tasks for new comments")
        for task in tasks:
            comments = get_comments(task_id=task["id"])
            logger.info(f"Task {task['id']} has {len(comments)} comments")
            for comment in comments:
                # Попробуем разобрать строку времени с миллисекундами
                try:
                    comment_time = datetime.datetime.strptime(comment["posted_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    # Если не удается разобрать, попробуем без миллисекунд
                    comment_time = datetime.datetime.strptime(comment["posted_at"], "%Y-%m-%dT%H:%M:%SZ")

                if comment_time > last_checked:
                    logger.info(f"New comment found: {comment['content']}")
                    user_id_in_task = task["content"].split('(ID: ')[-1].split(')')[0]
                    logger.info(f"Sending comment to user {user_id_in_task}")
                    await context.bot.send_message(chat_id=user_id_in_task,
                                                   text=f"Ответ по вашему запросу: {comment['content']}")
        last_checked = datetime.datetime.utcnow()
    except Exception as e:
        logger.error(f"Error checking comments: {e}")