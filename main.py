import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import AI_TOKEN, ADMIN_USERS_ID, ADMIN_EMAIL, todoist_api, SMTP_USER, SMTP_SERVER, SMTP_PORT, SMTP_PASSWORD
from handlers.commands import start, view_requests
from handlers.callbacks import start_button, button_callback_respond, button_callback_next_request
from handlers.messages import handle_problem, handle_admin_response
from scheduler import check_for_comments
import logging
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting bot...")

# Функция для обработки команды /admins
async def admins(update, context):
    user_id = update.message.from_user.id
    logger.info(f"Received /admins command from {user_id}")
    print(f"Received /admins command from {user_id}")

    if user_id in ADMIN_USERS_ID:
        logger.info(f"User {user_id} is an admin.")
        print(f"User {user_id} is an admin.")
        await update.message.reply_text("Доступные функции", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Сбор статистики", callback_data="collect_stats")]
        ]))
    else:
        logger.info(f"User {user_id} is not authorized.")
        print(f"User {user_id} is not authorized.")
        await update.message.reply_text("У вас нет прав на использование этой команды.")

# Функция для обработки нажатия кнопки "Сбор статистики"
async def button_callback_collect_stats(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id in ADMIN_USERS_ID:
        logger.info(f"Admin {user_id} requested statistics collection")
        print(f"Admin {user_id} requested statistics collection")
        # Сбор статистики
        stats = await collect_statistics()
        logger.info(f"Collected stats: {stats}")
        print(f"Collected stats: {stats}")
        if stats:
            for email in ADMIN_EMAIL:
                result = send_confirmation_email(email, stats, "Статистика по запросам пользователей")
                if result:
                    await query.message.reply_text(f"Статистика отправлена на {email}.")
                else:
                    await query.message.reply_text(f"Не удалось отправить статистику на {email}.")
        else:
            await query.message.reply_text("Нет активных заявок для ответа.")
        await query.answer()
    else:
        await query.message.reply_text("У вас нет прав на использование этой функции.")
        await query.answer()

# Функция для сбора статистики по запросам пользователей
async def collect_statistics():
    logger.info("Starting statistics collection")
    print("Starting statistics collection")
    try:
        tasks = todoist_api.get_tasks()
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to fetch tasks from Todoist: {e}")
        return "Не удалось получить задачи из Todoist. Проверьте соединение."
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return "Произошла непредвиденная ошибка при получении задач из Todoist."

    total_requests = len(tasks)
    logger.info(f"Total requests found: {total_requests}")
    print(f"Total requests found: {total_requests}")

    if total_requests == 0:
        return "Нет активных заявок для ответа."

    stats_message = f"Общее количество запросов: {total_requests}\n\n"

    for task in tasks:
        logger.info(f"Processing task: {task.id}, Content: {task.content}, Description: {task.description}")
        print(f"Processing task: {task.id}, Content: {task.content}, Description: {task.description}")
        stats_message += (
            f"ID: {task.id}\n"
            f"Пользователь: {task.content}\n"
            f"Вопрос: {task.description}\n"
            f"Дата добавления: {task.created_at}\n"
            "----------------------------------------\n"
        )

    logger.info(f"Final stats message: {stats_message}")
    print(f"Final stats message: {stats_message}")
    return stats_message

# Функция для отправки email
def send_confirmation_email(email_address, mail_content, context, excel_file=None, excel_name=None):
    logger.info(f"Attempting to send email to {email_address} with subject '{context}'")
    sender_address = SMTP_USER
    sender_pass = SMTP_PASSWORD
    smtp_port = SMTP_PORT
    smtp_server = SMTP_SERVER
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = email_address
    message['Subject'] = context
    message.attach(MIMEText(mail_content, 'plain'))

    try:
        logger.info(f"Connecting to SMTP server {smtp_server} on port {smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        logger.info(f"Logging in as {sender_address}")
        server.login(sender_address, sender_pass)
        text = message.as_string()
        server.sendmail(sender_address, email_address, text)
        server.quit()
        logger.info("Email sent successfully")
        print("Email sent successfully")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTPException: {e}")
        print(f"SMTPException: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        print(f"Failed to send email: {e}")
        return False

# Инициализация приложения Telegram
app = ApplicationBuilder().token(AI_TOKEN).build()

# Инициализация планировщика
scheduler = AsyncIOScheduler()
scheduler.add_job(check_for_comments, 'interval', minutes=0.5, args=[app])
scheduler.start()

# Добавление обработчиков команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start_button, pattern='go'))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_problem))
app.add_handler(CommandHandler("view_requests", view_requests))
app.add_handler(CallbackQueryHandler(button_callback_respond, pattern=r'^respond_'))
app.add_handler(CallbackQueryHandler(button_callback_next_request, pattern='next_request'))
app.add_handler(CommandHandler("admins", admins))  # Обработчик для команды /admins
app.add_handler(CallbackQueryHandler(button_callback_collect_stats, pattern="collect_stats"))
app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=ADMIN_USERS_ID), handle_admin_response))

# Запуск приложения
logger.info("Running bot polling...")
print("Running bot polling...")
app.run_polling()
