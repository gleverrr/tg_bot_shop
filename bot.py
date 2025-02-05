from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from tg_bot import register_all_handlers
from config import Config
import asyncio

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация всех обработчиков
    register_all_handlers(dp)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())