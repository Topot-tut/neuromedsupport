from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from todoist_api_python.api import TodoistAPI

from config import ADMIN_USERS_ID, logger, TODOIST_API_TOKEN
from scheduler import get_tasks, get_comments

admin_positions = {}
todoist_api = TodoistAPI(TODOIST_API_TOKEN)


def get_todoist_task_url(task_id):
    return f"https://todoist.com/showTask?id={task_id}"


async def start(update, context):
    logger.info(f"Received /start command from {update.message.from_user.id}")
    with open('images/canlidestek-1.jpeg', 'rb') as photo:
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=photo, caption="Здравствуйте!" + "\n" + "Этот бот поможет нашей команде как можно быстрее узнать и решить вашу проблему.")
    await update.message.reply_text("Чтобы связаться с нами, нажмите на кнопку ниже", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Написать о проблеме", callback_data="go")]]))


async def view_requests(update, context):
    user_id = update.message.from_user.id
    logger.info(f"Received /view_requests command from {user_id}")

    if user_id in ADMIN_USERS_ID:
        admin_positions[user_id] = 0
        await send_next_request(update, context, user_id)
    else:
        await update.message.reply_text("У вас нет прав на просмотр обращений.")


async def send_next_request(update, context, user_id):
    try:
        logger.info("Fetching tasks from Todoist")
        tasks = get_tasks()
        position = admin_positions.get(user_id, 0)

        if position < len(tasks):
            task = tasks[position]
            logger.info(f"Sending task {task['id']} to admin {user_id}")

            response_message = (
                f"ID: {task['id']}\n"
                f"Дата добавления: {task['created_at']}\n"
                f"Пользователь: {task['content']}\n"
                f"Вопрос: {task['description']}\n"
            )
            comments = get_comments(task_id=task['id'])
            photo_file_id = None
            for comment in comments:
                if comment['content'].startswith("Фото file_id:"):
                    photo_file_id = comment['content'].split("Фото file_id: ")[-1]
                    logger.info(f"Photo file_id found in comments: {photo_file_id}")

            user_id_in_task = task['content'].split('(ID: ')[-1].split(')')[0]
            user_telegram_link = f"tg://user?id={user_id_in_task}"
            logger.info(f"User Telegram link: {user_telegram_link}")

            keyboard = [
                [
                    InlineKeyboardButton("Ответить", url=get_todoist_task_url(task['id'])),
                    InlineKeyboardButton("Связаться", url=user_telegram_link),
                    InlineKeyboardButton("Следующее", callback_data="next_request")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if photo_file_id:
                logger.info("Sending task with photo")
                await context.bot.send_photo(chat_id=update.message.chat_id, photo=photo_file_id, caption=response_message, reply_markup=reply_markup)
            else:
                logger.info("Sending task without photo")
                await context.bot.send_message(chat_id=update.message.chat_id, text=response_message, reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text="Больше нет заявок.")
        admin_positions[user_id] += 1
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"Ошибка при получении заявок: {e}")