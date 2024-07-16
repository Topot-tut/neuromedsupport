import datetime
from todoist_api_python.api import TodoistAPI
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import TODOIST_API_TOKEN, ADMIN_USERS_ID

todoist_api = TodoistAPI(TODOIST_API_TOKEN)
admin_positions = {}
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
            task = todoist_api.add_task(
                content=f"Проблема от {user.first_name} {user.last_name} (ID: {user.id})",
                description=f"{question}\nДата: {current_time}",
                due_string="today"
            )
            await update.message.reply_text('Ваше обращение принято!\nНаша команда уже начала работать над вашей проблемой. В ближайшее время с вами свяжется наш специалист.')
            context.user_data['waiting_for_problem'] = False
        except Exception as e:
            await update.message.reply_text(f"Ошибка при сохранении обращения: {e}")
    else:
        await update.message.reply_text("Чтобы отправить обращение, пожалуйста, нажмите на кнопку 'Написать о проблеме'.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Написать о проблеме", callback_data="go")]]))

async def send_next_request(update, context, user_id):
    try:
        tasks = todoist_api.get_tasks()
        position = context.user_data.get('admin_positions', 0)
        if position < len(tasks):
            task = tasks[position]
            response_message = f"ID: {task.id}\nДата добавления: {task.created_at}\nПользователь: {task.content}\nВопрос: {task.description}\n"
            user_id_in_task = task.content.split('(ID: ')[-1].split(')')[0]
            user_telegram_link = f"tg://user?id={user_id_in_task}"
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
        context.user_data['admin_positions'] += 1
    except Exception as e:
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"Ошибка при получении заявок: {e}")

async def handle_admin_response(update, context):
    user_id = update.message.from_user.id
    if user_id in admin_waiting_for_response:
        request_id = admin_waiting_for_response[user_id]
        response_text = update.message.text
        try:
            todoist_api.add_comment(task_id=request_id, content=response_text)
            await update.message.reply_text(f"Ответ на заявку с ID {request_id} сохранен.")
            comments = todoist_api.get_comments(task_id=request_id)
            for comment in comments:
                await context.bot.send_message(chat_id=user_id, text=f"Комментарий к задаче {request_id}: {comment['content']}")
            del admin_waiting_for_response[user_id]
        except Exception as e:
            await update.message.reply_text(f"Ошибка при обновлении заявки: {e}")
    else:
        await update.message.reply_text("Нет активных заявок для ответа.")
