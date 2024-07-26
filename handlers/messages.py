import datetime
import logging

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
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
        await update.message.reply_text("Рабочее время технической поддержки с 10:00 и до 22:00.")
        return

    if context.user_data.get('waiting_for_problem', False):
        user = update.message.from_user
        question = update.message.text

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            logger.info(f"Creating task with content: 'Проблема от {user.first_name} {user.last_name} (ID: {user.id})'")
            logger.info(f"Description: {question}\nДата: {current_time}")

            task = todoist_api.add_task(
                content=f"Проблема от {user.first_name} {user.last_name} (ID: {user.id})",
                description=f"{question}\nДата: {current_time}",
                due_string="today"
            )
            context.user_data['current_task_id'] = task.id
            context.user_data['waiting_for_photo'] = True
            await update.message.reply_text(
                "Ваше обращение принято! Хотите ли добавить фото к своей проблеме?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Да", callback_data="add_photo_yes"),
                     InlineKeyboardButton("Нет", callback_data="add_photo_no")]
                ])
            )
            context.user_data['waiting_for_problem'] = False
        except Exception as e:
            logger.error(f"Error: {e}")
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


async def handle_add_photo_response(update, context):
    query = update.callback_query
    if query.data == "add_photo_yes":
        await query.answer()
        await query.edit_message_text("Пожалуйста, отправьте фото для вашей проблемы.")
    elif query.data == "add_photo_no":
        task_id = context.user_data.get('current_task_id')
        if task_id:
            await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Ваше обращение принято!\nНаша команда уже начала работать над вашей проблемой. В ближайшее время с вами свяжется наш специалист.",
                                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Закрыть заявку", callback_data=f"close_{task_id}")]]))
        context.user_data['waiting_for_photo'] = False
        context.user_data.pop('current_task_id', None)
        await query.answer()


async def handle_photo(update, context):
    if context.user_data.get('waiting_for_photo', False):
        user = update.message.from_user
        photo_file_id = update.message.photo[-1].file_id
        task_id = context.user_data.get('current_task_id')

        try:
            # Добавление комментария с file_id фото в задачу
            logger.info("Adding photo file_id as a comment to the task")
            todoist_api.add_comment(task_id=task_id, content=f"Фото file_id: {photo_file_id}")
            logger.info("Photo file_id comment added successfully")

            await update.message.reply_text("Фото добавлено к вашей заявке. Спасибо!")
            context.user_data['waiting_for_photo'] = False

            # После добавления фото отправляем сообщение о принятии заявки
            await update.message.reply_text(
                "Ваше обращение принято!\nНаша команда уже начала работать над вашей проблемой. В ближайшее время с вами свяжется наш специалист.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Закрыть заявку", callback_data=f"close_{task_id}")]])
            )
            context.user_data.pop('current_task_id', None)
        except Exception as e:
            logger.error(f"Error adding photo comment: {e}")
            await update.message.reply_text(f"Ошибка при добавлении фото к заявке: {e}")

        # Сбрасываем состояние после завершения запроса
        context.user_data.clear()
    else:
        await update.message.reply_text("Чтобы отправить обращение, пожалуйста, нажмите на кнопку 'Написать о проблеме'.")
