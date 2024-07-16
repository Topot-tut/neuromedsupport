from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.commands import start, view_requests
from handlers.callbacks import start_button, button_callback_respond, button_callback_next_request
from handlers.messages import handle_problem, handle_admin_response
from config import ADMIN_USERS_ID

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_button, pattern='go'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_problem))
    app.add_handler(CommandHandler("view_requests", view_requests))
    app.add_handler(CallbackQueryHandler(button_callback_respond, pattern=r'^respond_'))
    app.add_handler(CallbackQueryHandler(button_callback_next_request, pattern='next_request'))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=ADMIN_USERS_ID), handle_admin_response))
