async def initialize_bot(app):
    await app.bot.delete_webhook(drop_pending_updates=True)
