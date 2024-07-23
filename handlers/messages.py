import datetime
import logging

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from todoist_api_python.api import TodoistAPI
from config import TODOIST_API_TOKEN

# Инициализация клиента Todoist API
todoist_api = TodoistAPI(TODOIST_API_TOKEN)
logger = logging.getLogger(__name__)
admin_waiting_for_response = {}

async def handle_problem(update, context):
    current_hour = datetime.datetime.now().hour
    if current_hour >= 22 or current_hour < 10:
        await update.message.reply_text("Рабочее время технической поддержки с 10:00 до 22:00.")
        return

    if context.user_data.get('waiting_for_problem', False):
        user = update.message.from_user
        question = update.message.text

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            logger.info(f"Creating task with content: 'Проблема от {user.first_name} {user.last_name} (ID: {user.id})'")
            logger.info(f"Description: {question}\nДата: {current_time}")

            # Создаем новую задачу в Todoist
            task = todoist_api.add_task(
                content=f"Проблема от {user.first_name} {user.last_name} (ID: {user.id})",
                description=f"{question}\nДата: {current_time}",
                due_string="today"
            )
            await update.message.reply_text(
                'Ваше обращение принято!\nНаша команда уже начала работать над вашей проблемой. В ближайшее время с вами свяжется наш специалист.'
            )
            context.user_data['waiting_for_problem'] = False
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await update.message.reply_text(f"Ошибка при сохранении обращения: {e}")
    else:
        await update.message.reply_text(
            "Чтобы отправить обращение, пожалуйста, нажмите на кнопку 'Написать о проблеме'.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Написать о проблеме", callback_data="go")]])
        )

async def handle_admin_response(update, context):
    print('тута')
    user_id = update.message.from_user.id
    logger.info(f"Admin {user_id} is handling a response")

    if user_id in admin_waiting_for_response:
        request_id = admin_waiting_for_response[user_id]
        response_text = update.message.text

        try:
            # Добавление комментария к задаче
            todoist_api.add_comment(task_id=request_id, content=response_text)
            await update.message.reply_text(f"Ответ на заявку с ID {request_id} сохранен.")

            # Получение задачи для получения user_id
            task = todoist_api.get_task(request_id)
            user_id_in_task = task.content.split('(ID: ')[-1].split(')')[0]
            logger.info(f"Sending update to user {user_id_in_task}")
            await context.bot.send_message(chat_id=user_id_in_task, text=f"Ваш запрос был обновлен: {response_text}")
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            await update.message.reply_text(f"Ошибка при обновлении заявки: {e}")

        del admin_waiting_for_response[user_id]
    else:
        await update.message.reply_text("Нет активных заявок для ответа.")
