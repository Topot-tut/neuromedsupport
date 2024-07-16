from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from BotHelpMed import send_next_request
from config import ADMIN_USERS_ID
from handlers.messages import admin_positions


async def start(update, context):
    with open('images/canlidestek-1.jpeg', 'rb') as photo:
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=photo, caption="Здравствуйте!" + "\n" + "Этот бот поможет нашей команде как можно быстрее узнать и решить вашу проблему.")
    await update.message.reply_text("Чтобы связаться с нами, нажмите на кнопку ниже", reply_markup={"inline_keyboard": [[{"text": "Написать о проблеме", "callback_data": "go"}]]})

async def view_requests(update, context):
    user_id = update.message.from_user.id
    if user_id in ADMIN_USERS_ID:
        # Инициализация позиции просмотра заявок для администратора
        admin_positions[user_id] = 0
        await send_next_request(update, context, user_id)
    else:
        await update.message.reply_text("У вас нет прав на просмотр обращений.")