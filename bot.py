import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import admin, user, common
from middlewares.anti_spam import AntiSpamMiddleware
from middlewares.subscription import SubscriptionMiddleware
from database.db import init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(AntiSpamMiddleware())
    dp.message.middleware(SubscriptionMiddleware(bot))
    dp.callback_query.middleware(SubscriptionMiddleware(bot))

    # Routers
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # DB init
    await init_db()

    logger.info("Bot ishga tushdi ✅")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
