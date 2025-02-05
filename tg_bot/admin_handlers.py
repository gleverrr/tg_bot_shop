from aiogram import  Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from .models import BannedUser
from .db_connection import get_db_session
from config import Config
from aiogram.filters import Command
from .models import BannedUser, Order
from config import Config
from .review_kb import (
    get_admin_keyboard
)
# Стандартная клавиатура для администратора
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/help")]
        ],
        resize_keyboard=True
    )

# Команда /помощь для администратора
async def help_command(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer(
        "Команды администратора:\n"
        "/ban [user_id] - Заблокировать пользователя\n"
        "/unban [user_id] - Разблокировать пользователя\n"
        "/delete #номер_объявления - Удалить объявление из канала\n"
        "@idchatwebhelbiebot - бот для получения id",
        reply_markup=get_admin_keyboard()
    )

# Команда /ban для блокировки пользователя
async def ban_user_command(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        # Получаем user_id из команды
        user_id_to_ban = int(message.text.split()[1])  # Пример: /ban 123456789
        session = get_db_session()

        # Проверяем, не заблокирован ли пользователь уже
        banned_user = session.query(BannedUser).filter(BannedUser.user_id == user_id_to_ban).first()
        if banned_user:
            await message.answer(f"Пользователь {user_id_to_ban} уже заблокирован.")
            return

        # Блокируем пользователя
        banned_user = BannedUser(user_id=user_id_to_ban)
        session.add(banned_user)
        session.commit()

        await message.answer(f"Пользователь {user_id_to_ban} заблокирован.", reply_markup=get_admin_keyboard())
    except IndexError:
        await message.answer("Используйте команду так: /ban [user_id]", reply_markup=get_admin_keyboard())
    except ValueError:
        await message.answer("Некорректный user_id. Укажите числовой ID.", reply_markup=get_admin_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка при блокировке пользователя: {e}", reply_markup=get_admin_keyboard())

# Команда /unban для разблокировки пользователя
async def unban_user_command(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        # Получаем user_id из команды
        user_id_to_unban = int(message.text.split()[1])  # Пример: /unban 123456789
        session = get_db_session()

        # Проверяем, заблокирован ли пользователь
        banned_user = session.query(BannedUser).filter(BannedUser.user_id == user_id_to_unban).first()
        if not banned_user:
            await message.answer(f"Пользователь {user_id_to_unban} не найден в списке заблокированных.")
            return

        # Разблокируем пользователя
        session.delete(banned_user)
        session.commit()

        await message.answer(f"Пользователь {user_id_to_unban} разблокирован.", reply_markup=get_admin_keyboard())
    except IndexError:
        await message.answer("Используйте команду так: /unban [user_id]", reply_markup=get_admin_keyboard())
    except ValueError:
        await message.answer("Некорректный user_id. Укажите числовой ID.", reply_markup=get_admin_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка при разблокировке пользователя: {e}", reply_markup=get_admin_keyboard())


# tg_bot/admin_handlers.py
async def delete_order_command(message: Message, bot:Bot):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        # Получаем номер объявления из команды
        order_id = int(message.text.split("#")[1])  # Пример: /удалить #123
    except (IndexError, ValueError):
        await message.answer("Используйте команду так: /удалить #номер_объявления", reply_markup=get_admin_keyboard())
        return

    session = get_db_session()
    order = session.query(Order).filter(Order.id == order_id).first()

    if not order:
        await message.answer(f"Объявление #{order_id} не найдено.", reply_markup=get_admin_keyboard())
        return

    if order.is_active == 0:
        await message.answer(f"Объявление #{order_id} уже удалено из канала.", reply_markup=get_admin_keyboard())
        return

    if not order.channel_message_ids:
        await message.answer(
            f"Объявление #{order_id} еще не опубликовано в канале и находится на проверке.",
            reply_markup=get_admin_keyboard()
        )
        return

    # Удаляем сообщение из канала
    try:
        message_ids = order.channel_message_ids.split(",")
        for msg_id in message_ids:
            await bot.delete_message(chat_id=Config.CHANNEL_ID, message_id=int(msg_id))
        # logger.info(f"Сообщение с ID {order.channel_message_ids} удалено из канала.")
    except Exception as e:
        # logger.error(f"Ошибка при удалении сообщения из канала: {e}")
        await message.answer(f"Ошибка при удалении объявления #{order_id}. Обратитесь к разработчику.", reply_markup=get_admin_keyboard())
        return

    # Помечаем объявление как неактивное
    order.is_active = 0
    session.commit()

    await message.answer(f"Объявление #{order_id} успешно удалено из канала.", reply_markup=get_admin_keyboard())
# Регистрация обработчиков
def register_admin_handlers(dp):
    dp.message.register(help_command, Command("help"))
    dp.message.register(ban_user_command, Command("ban"))
    dp.message.register(unban_user_command, Command("unban"))
    dp.message.register(delete_order_command, Command("delete"))  # Новый обработчик

