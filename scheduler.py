import datetime
import logging
from todoist_api_python.api import TodoistAPI
from config import TODOIST_API_TOKEN

# Инициализация клиента Todoist API
todoist_api = TodoistAPI(TODOIST_API_TOKEN)
logger = logging.getLogger(__name__)
last_checked = datetime.datetime.utcnow()


async def check_for_comments(context):
    global last_checked
    try:
        tasks = todoist_api.get_tasks()
        logger.info(f"Checking {len(tasks)} tasks for new comments")
        for task in tasks:
            comments = todoist_api.get_comments(task_id=task.id)
            logger.info(f"Task {task.id} has {len(comments)} comments")
            for comment in comments:
                # Попробуем разобрать строку времени с миллисекундами
                try:
                    comment_time = datetime.datetime.strptime(comment.posted_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    # Если не удается разобрать, попробуем без миллисекунд
                    comment_time = datetime.datetime.strptime(comment.posted_at, "%Y-%m-%dT%H:%M:%SZ")

                if comment_time > last_checked:
                    logger.info(f"New comment found: {comment.content}")
                    user_id_in_task = task.content.split('(ID: ')[-1].split(')')[0]
                    logger.info(f"Sending comment to user {user_id_in_task}")
                    await context.bot.send_message(chat_id=user_id_in_task,
                                                   text=f"Ответ по вашему запросу: {comment.content}")
        last_checked = datetime.datetime.utcnow()
    except Exception as e:
        logger.error(f"Error checking comments: {e}")
