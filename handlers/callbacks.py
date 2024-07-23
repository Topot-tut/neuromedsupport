from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging
from handlers.commands import send_next_request, todoist_api

logger = logging.getLogger(__name__)
admin_waiting_for_response = {}


async def start_button(update, context):
    query = update.callback_query
    if query:
        logger.info(f"Received button click 'Написать о проблеме' from {query.from_user.id}")
        await query.answer()
        await query.message.reply_text(
            "Пожалуйста, опишите свою проблему максимально детально в рамках одного сообщения."
            "\n1. Опишите проблему"
            "\n2. Когда вы обнаружили проблему"
            "\n3. Проблема была единожды или регулярно"
        )
        context.user_data['waiting_for_problem'] = True


async def button_callback_respond(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    request_id = data.split("_")[1]
    logger.info(f"Admin {user_id} is responding to request {request_id}")
    admin_waiting_for_response[user_id] = request_id
    await query.answer(f"Вы выбрали заявку с ID {request_id}")

    # Получение информации о задаче
    task = todoist_api.get_task(request_id)
    user_id_in_task = task.content.split('(ID: ')[-1].split(')')[0]
    user_telegram_link = f"https://t.me/{user_id_in_task}"

    # Сообщение с информацией о заявке
    response_message = (
        f"Пользователь: {task.content}\n"
        f"Вопрос: {task.description}\n"
    )

    # Отправка сообщения с информацией о заявке и кнопкой для связи
    await context.bot.send_message(chat_id=user_id, text=response_message, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Связаться", url=user_telegram_link)]
    ]))


async def button_callback_next_request(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    logger.info(f"Admin {user_id} requested next task")
    await query.answer()
    await send_next_request(query, context, user_id)
