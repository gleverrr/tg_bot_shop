from aiogram import Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from .models import BannedUser, Order
from .db_connection import get_db_session
from config import Config
from .review_kb import get_admin_keyboard

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
        "@getmyid_bot - бот для получения id",
        reply_markup=get_admin_keyboard()
    )

# Команда /ban для блокировки пользователя
async def ban_user_command(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    session = None
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
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

# Команда /unban для разблокировки пользователя
async def unban_user_command(message: Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    session = None
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
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

# Команда /delete для удаления объявления из канала
async def delete_order_command(message: Message, bot: Bot):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        # Получаем номер объявления из команды
        order_id = int(message.text.split("#")[1])  # Пример: /удалить #123
    except (IndexError, ValueError):
        await message.answer("Используйте команду так: /delete #номер_объявления", reply_markup=get_admin_keyboard())
        return

    session = None
    try:
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

            try:
                # raise Exception("TEST_ERROR: Message can't be deleted")
                await bot.delete_message(chat_id=Config.CHANNEL_ID, message_id=int(message_ids[0]))
            except Exception as e:
                if "message can't be deleted" in str(e):
                # if "TEST_ERROR" in str(e):

                    # Если сообщение нельзя удалить, редактируем его
                    await bot.edit_message_caption(
                        chat_id=Config.CHANNEL_ID,
                        message_id=int(message_ids[0]),
                        caption="Объявление не актуально"
                    )
                    # Формируем ссылку на сообщение
                    message_link = f"https://t.me/c/{str(Config.CHANNEL_ID).replace('-100', '')}/{message_ids[0]}"
                    
                    # Отправляем администратору запрос на подтверждение
                    admin_id = Config.ADMIN_IDS[0]  # Берем первого администратора
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"Подтвердите удаление объявления: {message_link}\n"
                             f"ID объявления: #{order_id}",
                             reply_markup=get_admin_keyboard()
                    )
                  
                    order.is_active = 0
                    session.commit()

                    # await message.answer(
                    #     f"Сообщение #{order_id} старше 48 часов и не может быть удалено автоматически. "
                    #     "Текст изменен на 'Объявление не актуально'. Администратору отправлен запрос на ручное удаление.",
                    #     reply_markup=get_admin_keyboard()
                    # )
                    return
                else:
                    raise e  # Если это другая ошибка - пробрасываем дальше
            
            # Удаляем остальные сообщения (медиа) - если есть
            for msg_id in message_ids[1:]:
                try:
                    await bot.delete_message(chat_id=Config.CHANNEL_ID, message_id=int(msg_id))
                except:
                    pass  # Игнорируем ошибки при удалении медиа
            order.is_active = 0
            session.commit()

            await message.answer(f"Объявление #{order_id} успешно удалено из канала.", reply_markup=get_admin_keyboard())
        except Exception as e:
            await message.answer(f"Ошибка при удалении объявления #{order_id}. Обратитесь к разработчику. Ошибка: {e}", reply_markup=get_admin_keyboard())
            return
        
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

# Регистрация обработчиков
def register_admin_handlers(dp):
    dp.message.register(help_command, Command("help"))
    dp.message.register(ban_user_command, Command("ban"))
    dp.message.register(unban_user_command, Command("unban"))
    dp.message.register(delete_order_command, Command("delete"))  # Новый обработчик