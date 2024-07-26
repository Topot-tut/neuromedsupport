from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
import logging
from handlers.commands import send_next_request, todoist_api

logger = logging.getLogger(__name__)
admin_waiting_for_response = {}


async def start_button(update, context):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            "Пожалуйста, опишите свою проблему максимально детально в рамках одного сообщения."
            "\n"
            "1. Опишите проблему"
            "\n"
            "2. Когда вы обнаружили проблему"
            "\n"
            "3. Проблема была единожды или регулярно"
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

async def button_callback_close_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    task_id = query.data.split("_")[1]

    try:
        todoist_api.update_task(task_id, description="Статус: закрыта")
        await query.answer("Заявка закрыта.")
        await query.edit_message_reply_markup(reply_markup=None)

        await query.message.reply_text(
            "Спасибо за вашу заявку! Пожалуйста, оцените работу техподдержки:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1", callback_data=f"rate_{task_id}_1"),
                 InlineKeyboardButton("2", callback_data=f"rate_{task_id}_2"),
                 InlineKeyboardButton("3", callback_data=f"rate_{task_id}_3"),
                 InlineKeyboardButton("4", callback_data=f"rate_{task_id}_4"),
                 InlineKeyboardButton("5", callback_data=f"rate_{task_id}_5")]
            ])
        )
        context.user_data['waiting_for_rating'] = True
    except Exception as e:
        logger.error(f"Error closing request: {e}")
        await query.answer(f"Ошибка при закрытии заявки: {e}")


async def button_callback_rate(update, context):
    query = update.callback_query
    data = query.data.split("_")
    task_id = data[1]
    rating = data[2]

    try:
        task = todoist_api.get_task(task_id)
        task_description = task.description

        # Добавляем строку "Оценка: [оценка]"
        if "Оценка: " in task_description:
            start_index = task_description.index("Оценка: ")
            end_index = task_description.index("\n", start_index) if "\n" in task_description[start_index:] else len(task_description)
            task_description = task_description[:start_index] + f"Оценка: {rating}" + task_description[end_index:]
        else:
            task_description += f"\nОценка: {rating}"

        todoist_api.update_task(task_id, description=task_description)
        await query.message.reply_text(f"Спасибо за вашу оценку: {rating}!")
    except Exception as e:
        await query.message.reply_text(f"Ошибка при сохранении оценки: {e}")

async def button_callback_rate(update, context):
    query = update.callback_query
    data = query.data.split("_")
    task_id = data[1]
    rating = data[2]

    try:
        task = todoist_api.get_task(task_id)
        task_description = task.description

        # Добавляем строку "Оценка: [оценка]"
        if "Оценка: " in task_description:
            start_index = task_description.index("Оценка: ")
            end_index = task_description.index("\n", start_index) if "\n" in task_description[start_index:] else len(task_description)
            task_description = task_description[:start_index] + f"Оценка: {rating}" + task_description[end_index:]
        else:
            task_description += f"\nОценка: {rating}"

        todoist_api.update_task(task_id, description=task_description)

        # Убираем кнопки с оценками и отправляем сообщение благодарности
        await query.message.edit_reply_markup(reply_markup=None)
        await query.message.reply_text(f"Спасибо за вашу оценку!")
    except Exception as e:
        await query.message.reply_text(f"Ошибка при сохранении оценки: {e}")

# Обработчик для закрытия заявки и оценивания
async def button_callback_close_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    task_id = query.data.split("_")[1]

    try:
        todoist_api.update_task(task_id, description="Статус: закрыта")
        await query.answer("Заявка закрыта.")
        await query.edit_message_reply_markup(reply_markup=None)

        # Предложение оценить работу техподдержки
        await query.message.reply_text(
            "Спасибо за вашу заявку! Пожалуйста, оцените работу техподдержки:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1", callback_data=f"rate_{task_id}_1"),
                 InlineKeyboardButton("2", callback_data=f"rate_{task_id}_2"),
                 InlineKeyboardButton("3", callback_data=f"rate_{task_id}_3"),
                 InlineKeyboardButton("4", callback_data=f"rate_{task_id}_4"),
                 InlineKeyboardButton("5", callback_data=f"rate_{task_id}_5")]
            ])
        )
    except Exception as e:
        logger.error(f"Error closing request: {e}")
        await query.answer(f"Ошибка при закрытии заявки: {e}")

# Обработчик для оценивания
async def button_callback_rate_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("_")
    task_id = data[1]
    rating = data[2]

    try:
        task = todoist_api.get_task(task_id)
        updated_description = task.description + f"\nОценка: {rating}"
        todoist_api.update_task(task_id, description=updated_description)

        await query.answer("Спасибо за вашу оценку!")
        await query.message.reply_text("Спасибо за вашу оценку!")
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error(f"Error updating task with rating: {e}")
        await query.answer(f"Ошибка при обновлении заявки: {e}")
