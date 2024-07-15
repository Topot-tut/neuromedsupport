from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackQueryHandler, CommandHandler, ContextTypes
from todoist_api_python.api import TodoistAPI
import datetime
import requests

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, BotCommand

from config import ADMIN_USERS_ID, TODOIST_API_TOKEN, AI_TOKEN

# Инициализация клиента Todoist API
todoist_api = TodoistAPI(TODOIST_API_TOKEN)

admin_positions = {}

admin_waiting_for_response = {}


async def start (update, context):
    with open('images/canlidestek-1.jpeg', 'rb') as photo:
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=photo, caption="Здравствуйте!" + "\n" + "Этот бот поможет нашей команде как можно быстрее узнать и решить вашу проблему.")
    await update.message.reply_text("Чтобы связаться с нами, нажмите на кнопку ниже", reply_markup={"inline_keyboard": [[{"text": "Написать о проблеме", "callback_data": "go"}]]})


async def start_button(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            "Пожалуйста опишите свою проблему максимально детально в рамках одного сообщения."
            "\n"
            "1. Опишите проблему"
            "\n"
            "2. Когда вы обнаружили проблему"
            "\n"
            "3. Проблема была единожды или регулярно"
        )
        context.user_data['waiting_for_problem'] = True

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
            # Отладочная информация
            print(f"Creating task with content: 'Проблема от {user.first_name} {user.last_name} (ID: {user.id})'")
            print(f"Description: {question}\nДата: {current_time}")

            # Создаем новую задачу в Todoist
            task = todoist_api.add_task(
                content=f"Проблема от {user.first_name} {user.last_name} (ID: {user.id})",
                description=f"{question}\nДата: {current_time}",
                due_string="today"
            )
            await update.message.reply_text(
                'Ваше обращение принято!' + "\n" + ' Наша команда уже начала работать над вашей проблемой. В ближайшее время с вами свяжется наш специалист.')
            # Сброс состояния после приема первого сообщения
            context.user_data['waiting_for_problem'] = False
        except Exception as e:
            # Печать ошибки
            print(f"Error: {e}")
            await update.message.reply_text(f"Ошибка при сохранении обращения: {e}")
    else:
        await update.message.reply_text(
            "Чтобы отправить обращение, пожалуйста, нажмите на кнопку 'Написать о проблеме'.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Написать о проблеме", callback_data="go")]])
        )



async def view_requests(update, context):
    user_id = update.message.from_user.id

    if user_id in ADMIN_USERS_ID:
        # Инициализация позиции просмотра заявок для администратора
        admin_positions[user_id] = 0
        await send_next_request(update, context, user_id)
    else:
        await update.message.reply_text("У вас нет прав на просмотр обращений.")


async def send_next_request(update, context, user_id):
    try:
        tasks = todoist_api.get_tasks()
        position = admin_positions.get(user_id, 0)

        if position < len(tasks):
            task = tasks[position]

            # Отладочная печать всех атрибутов задачи
            print(vars(task))

            response_message = (
                f"ID: {task.id}\n"
                f"Дата добавления: {task.created_at}\n"
                f"Пользователь: {task.content}\n"
                f"Вопрос: {task.description}\n"
            )
            user_id_in_task = task.content.split('(ID: ')[-1].split(')')[0]  # Извлекаем user_id из content
            user_telegram_link = f"tg://user?id={user_id_in_task}"  # Создаем ссылку на пользователя по его user_id

            keyboard = [
                [
                    InlineKeyboardButton("Ответить", callback_data=f"respond_{task.id}"),
                    InlineKeyboardButton("Связаться", url=user_telegram_link),
                    InlineKeyboardButton("Следующее", callback_data="next_request")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(chat_id=update.message.chat_id, text=response_message, reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=update.message.chat_id, text="Больше нет заявок.")
        admin_positions[user_id] += 1
    except Exception as e:
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"Ошибка при получении заявок: {e}")


async def button_callback_respond(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    request_id = data.split("_")[1]
    admin_waiting_for_response[user_id] = request_id
    await query.answer(f"Вы выбрали заявку с ID {request_id}")

async def button_callback_next_request(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()
    await send_next_request(query, context, user_id)



async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in admin_waiting_for_response:
        request_id = admin_waiting_for_response[user_id]
        response_text = update.message.text

        # Находим заявку по ID и обновляем ее статус и добавляем ответ
        try:
            # Обновляем задачу в Todoist
            todoist_api.update_task(request_id, description=f"Ответ: {response_text}\nСтатус: answered")
            await update.message.reply_text(f"Ответ на заявку с ID {request_id} сохранен.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при обновлении заявки: {e}")

        del admin_waiting_for_response[user_id]
    else:
        await update.message.reply_text("Нет активных заявок для ответа.")

app = ApplicationBuilder().token(AI_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start_button, pattern='go'))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_problem))
app.add_handler(CommandHandler("view_requests", view_requests))
app.add_handler(CallbackQueryHandler(button_callback_respond, pattern=r'^respond_'))
# app.add_handler(CallbackQueryHandler(button_callback))
app.add_handler(CallbackQueryHandler(button_callback_next_request, pattern='next_request'))

app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=ADMIN_USERS_ID), handle_admin_response))

app.run_polling()
