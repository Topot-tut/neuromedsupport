from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.messages import send_next_request
from config import admin_waiting_for_response

async def start_button(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            "Пожалуйста опишите свою проблему максимально детально в рамках одного сообщения.\n"
            "1. Опишите проблему\n"
            "2. Когда вы обнаружили проблему\n"
            "3. Проблема была единожды или регулярно"
        )
        context.user_data['waiting_for_problem'] = True

async def button_callback_respond(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    request_id = data.split("_")[1]
    admin_waiting_for_response[user_id] = request_id
    await query.answer(f"Вы выбрали заявку с ID {request_id}")
    task_url = f"https://todoist.com/showTask?id={request_id}"
    await query.message.reply_text(f"Вы можете ответить на заявку по ссылке: [Перейти к задаче]({task_url})", parse_mode='Markdown')

async def button_callback_next_request(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await send_next_request(query, context, user_id)
