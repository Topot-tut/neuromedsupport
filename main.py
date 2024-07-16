import asyncio
import nest_asyncio
from telegram.ext import ApplicationBuilder
from handlers import register_handlers
from config import AI_TOKEN

# Применить nest_asyncio
nest_asyncio.apply()

async def main():
    app = ApplicationBuilder().token(AI_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    register_handlers(app)
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())