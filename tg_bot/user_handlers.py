from aiogram import Bot, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from .review_states import ReviewStates
from aiogram.types import ReplyKeyboardRemove
import logging
import time
from .review_kb import (
    get_main_keyboard,
    get_product_type_keyboard,
    get_condition_keyboard,
    get_confirmation_keyboard,
    get_admin_keyboard
)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from .models import BannedUser, Order
from .db_connection import get_db_session
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_command(message: Message, bot: Bot):
    await message.answer(
        f"Подпишитесь на наш канал: {Config.CHANNEL_LINK}.\n\n"
        "Если есть вопросы, обратитесь к администратору: @BogGermes.\n\n"
        "Этот бот создан для публикации объявлений о продаже золотых изделий. "
        "Ответственность за передачу денег и товаров мы не несем.\n\n"
        "Команды:\n"
        "/добавить - разместить объявление\n"
        "/удалить - удалить объявление\n"
        "/редактировать - редактировать объявление",
        reply_markup=get_main_keyboard()
    )

async def add_product_command(message: Message, state: FSMContext):
    session = get_db_session()
    try:
        banned_user = session.query(BannedUser).filter(BannedUser.user_id == message.from_user.id).first()
        if banned_user:
            await message.answer("Ой! Извините, вашему аккаунту запрещено выкладывать объявления. "
                                "Если хотите узнать подробности, напишите администратору @BogGermes.")
            return
    finally:
        session.close()  # Закрываем сессию в любом случае

    await message.answer("Выберите тип изделия (если не нашли нужного, введите вручную):",
                         reply_markup=get_product_type_keyboard())
    await state.set_state(ReviewStates.product_type)
# async def process_product_type(message: Message, state: FSMContext):
#     await state.update_data(product_type=message.text)
#     await message.answer("Состояние товара", 
#                          reply_markup=ReplyKeyboardMarkup(
#                              keyboard=[[KeyboardButton(text="новое")],
#                                        [KeyboardButton(text="б/у")]],
#                              resize_keyboard=True
#                          ))
#     await state.set_state(ReviewStates.weight)
async def process_product_type(message: Message, state: FSMContext):
    await state.update_data(product_type=message.text)
    await message.answer("Вес товара:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReviewStates.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("Размер товара:", 
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="не указан")]],
                             resize_keyboard=True
                         ))
    await state.set_state(ReviewStates.size)    
async def process_size(message: Message, state: FSMContext):
    await state.update_data(size=message.text)
    await message.answer("Вставки:", 
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="отсутствуют")]],
                             resize_keyboard=True
                         ))
    await state.set_state(ReviewStates.insertion)
async def process_insertion(message: Message, state: FSMContext):
    await state.update_data(insertion=message.text)
    await message.answer("Состояние товара", 
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="новое")],
                                       [KeyboardButton(text="б/у")]],
                             resize_keyboard=True
                         ))
    await state.set_state(ReviewStates.condition)
async def process_condition(message: Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Введите цену товара:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReviewStates.price)

async def process_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Укажите пробу товара:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                    [KeyboardButton(text="583")],
                                    [KeyboardButton(text="585")],
                                    [KeyboardButton(text="750")],
                                    [KeyboardButton(text="925")],
                                    [KeyboardButton(text="нет")]
                             ],
                             resize_keyboard=True
                         ))
    await state.set_state(ReviewStates.hallmark)

async def process_hallmark(message: Message, state: FSMContext):
    await state.update_data(hallmark=message.text)
    await message.answer("Город (можно не указывать):", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="не указан")]],
        resize_keyboard=True
    ))
    await state.set_state(ReviewStates.city)

async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Дополнительная информация (например, материал, вставки, бренд и т.п.):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReviewStates.additional_info)

async def process_additional_info(message: Message, state: FSMContext):
    await state.update_data(additional_info=message.text)
    await message.answer("Контакты для связи (например, тег в Telegram, номер телефона, почта и т.п.):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ReviewStates.contacts)

async def process_contacts(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer("Приложите фотографии или видео товара (отправляйте максимум 10 файлов). Когда закончите, нажмите 'далее'.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="далее")]],
                             resize_keyboard=True
                         ))
    await state.set_state(ReviewStates.media)
#############
async def process_media(message: Message, state: FSMContext, bot: Bot):
    if message.photo or message.video:
        # Получаем текущие данные из состояния
        media_data = await state.get_data()
        media_ids = media_data.get("media_ids", [])

        # Добавляем новый медиафайл
        if message.photo:
            media_ids.append(f"photo:{message.photo[-1].file_id}")  # Сохраняем как photo:file_id
        elif message.video:
            media_ids.append(f"video:{message.video.file_id}")  # Сохраняем как video:file_id

        # Обновляем состояние
        await state.update_data(media_ids=media_ids)

        # Не отправляем ответ, просто ждем следующего файла или нажатия "далее"
    elif message.text == "далее":
        # Получаем данные из состояния
        data = await state.get_data()
        media_ids = data.get("media_ids", [])

        # Проверяем, есть ли медиафайлы
        if not media_ids:
            await message.answer("Нужно прислать как минимум 1 фотографию или видео!")
            return

        # Если больше 10 файлов, берем только первые 10
        if len(media_ids) > 10:
            media_ids = media_ids[:10]
            await state.update_data(media_ids=media_ids)
            await message.answer("Вы отправили больше 10 файлов. Будет использовано только первые 10.")

        # Формируем текст объявления
        preview_text = (
            f"Тип изделия: {data['product_type']}\n"
            f"Вес: {data['weight']}\n"
            f"Размер: {data['size']}\n"
            f"Вставки: {data['insertion']}\n"
            f"Состояние: {data['condition']}\n"
            f"Цена: {data['price']}\n"
            f"Проба: {data.get('hallmark', 'нет')}\n"
            f"Город: {data.get('city', 'не указан')}\n"
            f"Дополнительная информация: {data['additional_info']}\n"
            f"Контакты: {data['contacts']}"
        )

        # Формируем медиагруппу
        media_group = []
        for index, media in enumerate(media_ids):
            media_type, file_id = media.split(":")  # Разделяем тип и file_id
            if index == 0:
                # Первый медиафайл с подписью
                if media_type == "photo":
                    media_group.append(types.InputMediaPhoto(media=file_id, caption=preview_text))
                elif media_type == "video":
                    media_group.append(types.InputMediaVideo(media=file_id, caption=preview_text))
            else:
                # Остальные медиафайлы без подписи
                if media_type == "photo":
                    media_group.append(types.InputMediaPhoto(media=file_id))
                elif media_type == "video":
                    media_group.append(types.InputMediaVideo(media=file_id))

        # Отправляем медиагруппу пользователю
        try:
            await bot.send_media_group(message.chat.id, media=media_group)
        except Exception as e:
            # При ошибке завершаем состояние и возвращаем пользователя к начальному сообщению
            await message.answer(
                f"Ошибка при отправке медиафайлов: {e}\n"
                "Пожалуйста, начните заново.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return

        # Предлагаем подтвердить или отменить
        await message.answer(
            "Проверьте данные и подтвердите объявление:",
            reply_markup=get_confirmation_keyboard()
        )
        await state.set_state(ReviewStates.confirmation)
    else:
        await message.answer("Нужно прислать фотографию или видео!")
#########
async def process_confirmation(message: Message, state: FSMContext, bot: Bot):
    if message.text == "Да, подтверждаю":
        # Получаем данные из состояния
        data = await state.get_data()
        media_ids = data.get("media_ids", [])

        # Формируем медиагруппу
        media_group = []
        for index, media in enumerate(media_ids):
            media_type, file_id = media.split(":")
            if index == 0:
                # Первый медиафайл с подписью
                caption = (
                    f"Тип изделия: {data['product_type']}\n"
                    f"Вес: {data['weight']}\n"
                    f"Размер: {data['size']}\n"
                    f"Вставки: {data['insertion']}\n"
                    f"Состояние: {data['condition']}\n"
                    f"Цена: {data['price']}\n"
                    f"Проба: {data.get('hallmark', 'нет')}\n"
                    f"Город: {data.get('city', 'не указан')}\n"  
                    f"Дополнительная информация: {data['additional_info']}\n"
                    f"Контакты: {data['contacts']}"
                )
                if media_type == "photo":
                    media_group.append(types.InputMediaPhoto(media=file_id, caption=caption))
                elif media_type == "video":
                    media_group.append(types.InputMediaVideo(media=file_id, caption=caption))
            else:
                # Остальные медиафайлы без подписи
                if media_type == "photo":
                    media_group.append(types.InputMediaPhoto(media=file_id))
                elif media_type == "video":
                    media_group.append(types.InputMediaVideo(media=file_id))

        # Сохраняем объявление в базу данных
        session = get_db_session()
        try:
            new_order = Order(
                user_id=message.from_user.id,
                product_type=data["product_type"],
                weight=data["weight"],
                size=data['size'], 
                insertion=data['insertion'],
                condition=data["condition"],
                price=data["price"],
                hallmark=data.get("hallmark", "нет"),
                city=data.get('city', 'нет'),
                additional_info=data["additional_info"],
                contacts=data["contacts"],
                media_ids=",".join(media_ids),
                is_active=True
            )
            session.add(new_order)
            session.commit()

            # Отправляем тег пользователя администратору
            try:
                await bot.send_message(
                    Config.ADMIN_IDS[0],
                    f"Новое объявление от @{message.from_user.username}\n"
                    f"User_id: {message.from_user.id}"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения администратору: {e}")
                await message.answer("Ошибка при отправке объявления администратору. Обратитесь к разработчику.")
                return

            # Отправляем медиагруппу администратору и сохраняем все message_id
            try:
                sent_messages = await bot.send_media_group(Config.ADMIN_IDS[0], media=media_group)
                new_order.admin_message_ids = ",".join(str(msg.message_id) for msg in sent_messages)
                session.commit()
            except Exception as e:
                logger.error(f"Ошибка при отправке объявления администратору: {e}")
                await message.answer("Ошибка при отправке объявления администратору. Обратитесь к разработчику.")
                return

            # Отправляем кнопки "Разместить" и "Отказать"
            try:
                admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Разместить", callback_data=f"approve_{new_order.id}")],
                    [InlineKeyboardButton(text="Отказать", callback_data=f"reject_{new_order.id}")]
                ])
                buttons_message = await bot.send_message(
                    Config.ADMIN_IDS[0],
                    "Выберите действие:",
                    reply_markup=admin_keyboard
                )
                new_order.admin_buttons_message_id = buttons_message.message_id
                session.commit()
            except Exception as e:
                logger.error(f"Ошибка при отправке кнопок администратору: {e}")
                return
        finally:
            session.close()  # Закрываем сессию в любом случае

        await message.answer(
            "Отправлено на проверку администратору. Ожидайте подтверждения.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

    elif message.text == "Нет, отменить объявление":
        await message.answer("Объявление отменено.", reply_markup=get_main_keyboard())
        await state.clear()
    else:
        await message.answer("Пожалуйста, выберите 'Да, подтверждаю' или 'Нет, отменить объявление'.")

async def handle_admin_decision(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    action, order_id = callback.data.split("_")
    order_id = int(order_id)

    session = get_db_session()
    try:
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await callback.answer("Объявление не найдено.")
            return

        if action == "approve":
            # Проверяем, активно ли объявление
            if not order.is_active:
                await callback.answer("Объявление уже удалено.")
                return

            # Формируем медиагруппу для канала
            media_group = []
            media_ids = order.media_ids.split(",")
            for index, media in enumerate(media_ids):
                media_type, file_id = media.split(":")
                if index == 0:
                    # Первый медиафайл с подписью
                    caption = (
                        f"Тип изделия: {order.product_type}\n"
                        f"Вес: {order.weight}\n"
                        f"Размер: {order.size}\n"
                        f"Вставки: {order.insertion}\n"
                        f"Состояние: {order.condition}\n"
                        f"Цена: {order.price}\n"
                        f"Проба: {order.hallmark}\n"
                        f"Город: {order.city}\n"
                        f"Дополнительная информация: {order.additional_info}\n"
                        f"Контакты: {order.contacts}\n"
                        f"#ID{order.id}"    
                    )
                    if media_type == "photo":
                        media_group.append(types.InputMediaPhoto(media=file_id, caption=caption))
                    elif media_type == "video":
                        media_group.append(types.InputMediaVideo(media=file_id, caption=caption))
                else:
                    # Остальные медиафайлы без подписи
                    if media_type == "photo":
                        media_group.append(types.InputMediaPhoto(media=file_id))
                    elif media_type == "video":
                        media_group.append(types.InputMediaVideo(media=file_id))

            # Отправляем медиагруппу в канал и сохраняем все message_id
            try:
                sent_messages = await bot.send_media_group(Config.CHANNEL_ID, media=media_group)
                order.channel_message_ids = ",".join(str(msg.message_id) for msg in sent_messages)
                session.commit()
            except Exception as e:
                await callback.answer(f"Ошибка при отправке объявления в канал: {e}")
                return

            # Удаляем сообщение с объявлением и кнопками из чата с администратором
            try:
                # Удаляем сообщение с объявлением (медиагруппу)
                if order.admin_message_ids:
                    admin_message_ids = order.admin_message_ids.split(",")
                    for msg_id in admin_message_ids:
                        try:
                            await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=int(msg_id))
                        except Exception as e:
                            logger.error(f"Ошибка при удалении сообщения из чата с администратором: {e}")

                # Удаляем сообщение с кнопками
                await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=callback.message.message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения с кнопками: {e}")

            # Уведомляем администратора
            await callback.answer("Объявление размещено в канале.")

        elif action == "reject":
            # Отказываем в размещении
            order.is_active = False
            session.commit()

            # Удаляем сообщение с объявлением и кнопками из чата с администратором
            try:
                # Удаляем сообщение с объявлением (медиагруппу)
                if order.admin_message_ids:
                    admin_message_ids = order.admin_message_ids.split(",")
                    for msg_id in admin_message_ids:
                        try:
                            await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=int(msg_id))
                        except Exception as e:
                            logger.error(f"Ошибка при удалении сообщения из чата с администратором: {e}")

                # Удаляем сообщение с кнопками
                await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=callback.message.message_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения с кнопками: {e}")

            # Уведомляем администратора
            await callback.answer("Объявление отклонено.")
    finally:
        session.close()  # Закрываем сессию в любом случае
    await callback.answer()


async def delete_product_command(message: Message, state: FSMContext):
    session = get_db_session()
    try:
        user_id = message.from_user.id
        orders = session.query(Order).filter(Order.user_id == user_id, Order.is_active == True).all()

        if not orders:
            await message.answer("У вас нет активных объявлений.")
            return

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"Удалить объявление #{order.id}")] for order in orders
            ],
            resize_keyboard=True
        )

        await message.answer("Выберите объявление для удаления:", reply_markup=keyboard)
        await state.set_state(ReviewStates.delete_order)
    finally:
        session.close()  # Закрываем сессию в любом случае


async def unknown_message(message: Message):
    if message.from_user.id in Config.ADMIN_IDS:
        # Сообщение для администратора
        await message.answer(
            "Команды администратора:\n"
            "/ban [user_id] - Заблокировать пользователя\n"
            "/unban [user_id] - Разблокировать пользователя\n"
            "@idchatwebhelbiebot - бот для получения id",
            reply_markup=get_admin_keyboard()
        )
    else:
        # Сообщение для обычного пользователя
        await message.answer(
            f"Подпишитесь на наш канал: {Config.CHANNEL_LINK}.\n\n"
            "Если есть вопросы, обратитесь к администратору: @BogGermes.\n\n"
            "Этот бот создан для публикации объявлений о продаже золотых изделий. "
            "Ответственность за передачу денег и товаров мы не несем.\n\n"
            "Команды:\n"
            "/добавить - разместить объявление\n"
            "/удалить - удалить объявление\n"
            "/редактировать - редактировать объявление",
            reply_markup=get_main_keyboard()
        )


async def delete_product_command(message: Message, state: FSMContext):
    session = get_db_session()
    try:
        user_id = message.from_user.id
        orders = session.query(Order).filter(Order.user_id == user_id, Order.is_active == True).all()
        if not orders:
            await message.answer("У вас нет активных объявлений.")
            return

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"Удалить объявление #{order.id}")] for order in orders
            ],
            resize_keyboard=True
        )
        await message.answer("Выберите объявление для удаления:", reply_markup=keyboard)
        await state.set_state(ReviewStates.delete_order)
    finally:
        session.close()


async def process_delete_order(message: Message, state: FSMContext, bot: Bot):
    session = None
    try:
        # Получаем ID заказа из текста сообщения
        order_id = int(message.text.split("#")[1])
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id, Order.user_id == message.from_user.id).first()

        if order:
             # Удаляем сообщения из чата с администратором, если они были отправлены
            if order.admin_message_ids:
                admin_message_ids = order.admin_message_ids.split(",")
                for msg_id in admin_message_ids:
                    try:
                        await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=int(msg_id))
                    except Exception as e:
                        logger.error(f"псевдо Ошибка при удалении сообщения из чата с администратором: {e}")

            # Удаляем сообщение с кнопками, если оно было отправлено
            if order.admin_buttons_message_id:
                try:
                    await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=order.admin_buttons_message_id)
                except Exception as e:
                    logger.error(f"псевдо Ошибка при удалении сообщения с кнопками: {e}")
            # Удаляем все сообщения из канала, если они были опубликованы
            if order.channel_message_ids:
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
                            await message.answer(f"Объявление #{order_id} успешно удалено из канала.", reply_markup=get_main_keyboard())
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
                except Exception as e:
                    await message.answer(f"Ошибка при удалении объявления #{order_id}. Обратитесь к администратору.", reply_markup=get_main_keyboard())
                    return

           

            # Помечаем объявление как неактивное
            order.is_active = False
            session.commit()
            await message.answer("Объявление удалено.", reply_markup=get_main_keyboard())
        else:
            await message.answer("Объявление не найдено.", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при удалении объявления: {e}")
        await message.answer("Произошла ошибка при удалении объявления.", reply_markup=get_main_keyboard())
    finally:
        if session:
            session.close()
        await state.clear()


async def edit_product_command(message: Message, state: FSMContext):
    session = get_db_session()
    try:
        user_id = message.from_user.id
        orders = session.query(Order).filter(Order.user_id == user_id, Order.is_active == True).all()

        if not orders:
            await message.answer("У вас нет активных объявлений для редактирования.")
            return

        # Создаем клавиатуру с объявлениями
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=f"Редактировать объявление #{order.id}")] for order in orders
            ],
            resize_keyboard=True
        )

        await message.answer("Медиафайлы объявления редактировать нельзя\nВыберите объявление для редактирования:", reply_markup=keyboard)
        await state.set_state(ReviewStates.edit_order)
    finally:
        session.close()  # Закрываем сессию в любом случае

async def process_edit_order(message: Message, state: FSMContext):
    session = None
    try:
        # Получаем ID заказа из текста сообщения
        order_id = int(message.text.split("#")[1])
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id, Order.user_id == message.from_user.id).first()

        if not order:
            await message.answer("Объявление не найдено.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        # Сохраняем ID заказа в состоянии
        await state.update_data(order_id=order_id)

        # Предлагаем редактировать тип изделия
        await message.answer(
            f"Текущий тип изделия: {order.product_type}\n"
            "Введите новый тип изделия или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Оставить без изменений")],            
                    [KeyboardButton(text="Кольца и перстни")],
                    [KeyboardButton(text="Серьги")],
                    [KeyboardButton(text="Кулоны и подвески")],
                    [KeyboardButton(text="Браслеты")],
                    [KeyboardButton(text="Пирсинг")],
                    [KeyboardButton(text="Цепи")],
                    [KeyboardButton(text="Колье")],
                    [KeyboardButton(text="Шармы")],
                    [KeyboardButton(text="Броши")],
                    [KeyboardButton(text="Комплекты")],
                    [KeyboardButton(text="Религиозные изделия")],
                    [KeyboardButton(text="Антиквариат")],
                    [KeyboardButton(text="Монеты")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_product_type)
    except Exception as e:
        logger.error(f"Ошибка при выборе объявления для редактирования: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_keyboard())
        await state.clear()
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае
############################
# async def process_edit_product_type(message: Message, state: FSMContext):
#     session = None
#     try:
#         data = await state.get_data()
#         order_id = data.get("order_id")
#         session = get_db_session()
#         order = session.query(Order).filter(Order.id == order_id).first()

#         if not order:
#             await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
#             await state.clear()
#             return

#         if message.text == "Оставить без изменений":
#             # Берем данные из базы данных
#             await state.update_data(product_type=order.product_type)
#             await message.answer("Тип изделия остался без изменений.")
#         else:
#             # Обновляем данные в состоянии
#             await state.update_data(product_type=message.text)
#             await message.answer("Тип изделия изменен.")

#         # Переходим к следующему шагу (редактирование состояния)
#         await message.answer(
#             f"Текущее состояние изделия: {order.condition}\n"
#             "Введите новое состояние товара или нажмите 'Оставить без изменений':",
#             reply_markup=ReplyKeyboardMarkup(
#                 keyboard=[
#                     [KeyboardButton(text="Оставить без изменений")],
#                     [KeyboardButton(text="новое")],
#                     [KeyboardButton(text="б/у")]
#                 ],
#                 resize_keyboard=True
#             )
#         )
#         await state.set_state(ReviewStates.edit_condition)
#     finally:
#         if session:
#             session.close()  # Закрываем сессию в любом случае
async def process_edit_product_type(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(product_type=order.product_type)
            await message.answer("Тип изделия остался без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(product_type=message.text)
            await message.answer("Тип изделия изменен.")

        # Переходим к следующему шагу (редактирование состояния)
        await message.answer(
            f"Текущий вес изделия: {order.weight}\n"
            "Введите новый вес или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Оставить без изменений")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_weight)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае
async def process_edit_weight(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(weight=order.weight)
            await message.answer("Вес товара остался без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(weight=message.text)
            await message.answer("Вес товара товара изменен.")

        # Переходим к следующему шагу (редактирование состояния)
        await message.answer(
            f"Текущий размер: {order.size}\n"
            "Введите новый размер товара или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Оставить без изменений")],
                    [KeyboardButton(text="не указан")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_size)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае
async def process_edit_size(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(size=order.size)
            await message.answer("Размер товара остался без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(size=message.text)
            await message.answer("Размер товара изменено.")

        # Переходим к следующему шагу (редактирование цены)
        await message.answer(
            f"Текущие вставки: {order.insertion}\n"
            "Введите новое описание вставок или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Оставить без изменений")]],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_insertion)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

async def process_edit_insertion(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(insertion=order.insertion)
            await message.answer("Вставки остались без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(insertion=message.text)
            await message.answer("Информация о вставках изменена.")

        # Переходим к следующему шагу (редактирование состояния)
        await message.answer(
            f"Текущее состояние изделия: {order.condition}\n"
            "Введите новое состояние товара или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Оставить без изменений")],
                    [KeyboardButton(text="новое")],
                    [KeyboardButton(text="б/у")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_condition)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае
async def process_edit_condition(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(condition=order.condition)
            await message.answer("Состояние товара осталось без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(condition=message.text)
            await message.answer("Состояние товара изменено.")

        # Переходим к следующему шагу (редактирование цены)
        await message.answer(
            f"Текущая цена изделия: {order.price}\n"
            "Введите новую цену товара или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Оставить без изменений")]],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_price)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае
async def process_edit_price(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(price=order.price)
            await message.answer("Цена товара осталась без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(price=message.text)
            await message.answer("Цена товара изменена.")

        # Переходим к следующему шагу (редактирование пробы)
        await message.answer(
            f"Текущая проба изделия: {order.hallmark}\n"
            "Введите новую пробу товара или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Оставить без изменений")],
                    [KeyboardButton(text="583")],
                    [KeyboardButton(text="585")],
                    [KeyboardButton(text="750")],
                    [KeyboardButton(text="925")],
                    [KeyboardButton(text="нет")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_hallmark)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

async def process_edit_hallmark(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(hallmark=order.hallmark)
            await message.answer("Проба товара осталась без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(hallmark=message.text)
            await message.answer("Проба товара изменена.")

        # Переходим к следующему шагу (редактирование дополнительной информации)
        await message.answer(
            f"Текущий город: {order.city}\n"
            "Введите актуальную информацию или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Оставить без изменений")],
                    [KeyboardButton(text="не указан")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_city)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае
async def process_edit_city(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(city=order.city)
            await message.answer("Город остался без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(city=message.text)
            await message.answer("Город изменен.")

        # Переходим к следующему шагу (редактирование дополнительной информации)
        await message.answer(
            f"Текущая дополнительная информация: {order.additional_info}\n"
            "Введите новую дополнительную информацию или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Оставить без изменений")]],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_additional_info)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

async def process_edit_additional_info(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(additional_info=order.additional_info)
            await message.answer("Дополнительная информация осталась без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(additional_info=message.text)
            await message.answer("Дополнительная информация изменена.")

        # Переходим к следующему шагу (редактирование контактов)
        await message.answer(
            f"Текущие контакты: {order.contacts}\n"
            "Введите новые контакты для связи или нажмите 'Оставить без изменений':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Оставить без изменений")]],
                resize_keyboard=True
            )
        )
        await state.set_state(ReviewStates.edit_contacts)
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае


async def process_edit_contacts(message: Message, state: FSMContext):
    session = None
    try:
        data = await state.get_data()
        order_id = data.get("order_id")
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        if message.text == "Оставить без изменений":
            # Берем данные из базы данных
            await state.update_data(contacts=order.contacts)
            await message.answer("Контакты остались без изменений.")
        else:
            # Обновляем данные в состоянии
            await state.update_data(contacts=message.text)
            await message.answer("Контакты изменены.")

        # Формируем итоговый текст объявления
        data = await state.get_data()
        preview_text = (
            f"Тип изделия: {data.get('product_type', order.product_type)}\n"
            f"Вес: {data.get('weight', order.weight)}\n"
            f"Размер: {data.get('size', order.size)}\n"
            f"Вставки: {data.get('insertion', order.insertion)}\n"
            f"Состояние: {data.get('condition', order.condition)}\n"
            f"Цена: {data.get('price', order.price)}\n"
            f"Проба: {data.get('hallmark', order.hallmark)}\n"
            f"Город: {data.get('city', order.city)}\n"
            f"Дополнительная информация: {data.get('additional_info', order.additional_info)}\n"
            f"Контакты: {data.get('contacts', order.contacts)}\n"
            f"#ID{order.id}"
        )

        # Отправляем пользователю итоговый текст
        await message.answer(
            "Проверьте данные и подтвердите изменения:\n\n"
            f"{preview_text}",
            reply_markup=get_confirmation_keyboard()
        )
        await state.set_state(ReviewStates.edit_confirmation)  # Переходим в edit_confirmation
    finally:
        if session:
            session.close()  # Закрываем сессию в любом случае

async def process_edit_confirmation(message: Message, state: FSMContext, bot: Bot):
    if message.text == "Да, подтверждаю":
        # Получаем данные из состояния
        data = await state.get_data()
        order_id = data.get("order_id")

        session = get_db_session()
        try:
            order = session.query(Order).filter(Order.id == order_id).first()

            if not order:
                await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
                await state.clear()
                return

            # Обновляем данные в базе
            order.product_type = data.get("product_type", order.product_type)
            order.weight= data.get("weight", order.weight)
            order.size = data.get("size", order.size)
            order.insertion = data.get("insertion", order.insertion)
            order.condition = data.get("condition", order.condition)
            order.price = data.get("price", order.price)
            order.hallmark = data.get("hallmark", order.hallmark)
            order.city = data.get("city", order.city)
            order.additional_info = data.get("additional_info", order.additional_info)
            order.contacts = data.get("contacts", order.contacts)

            session.commit()

            # Формируем текст объявления
            caption = (
                f"Тип изделия: {order.product_type}\n"
                f"Вес: {order.weight}\n"
                f"Размер: {order.size}\n"
                f"Вставки: {order.insertion}\n"
                f"Состояние: {order.condition}\n"
                f"Цена: {order.price}\n"
                f"Проба: {order.hallmark}\n"
                f"Город: {order.city}\n"
                f"Дополнительная информация: {order.additional_info}\n"
                f"Контакты: {order.contacts}\n"
                f"#ID{order.id}"
            )

            if order.channel_message_ids:
                # Если объявление уже опубликовано в канале, редактируем его там
                try:
                    # Редактируем подпись (caption) первого сообщения в медиагруппе
                    first_message_id = int(order.channel_message_ids.split(",")[0])
                    await bot.edit_message_caption(
                        chat_id=Config.CHANNEL_ID,
                        message_id=first_message_id,
                        caption=caption
                    )
                except Exception as e:
                    logger.error(f"Ошибка при редактировании сообщения в канале: {e}")
                    await message.answer("Ошибка при редактировании сообщения. Обратитесь к администратору.", reply_markup=get_main_keyboard())
                    await state.clear()
                    return

                # Уведомляем администратора об изменении
                await bot.send_message(
                    Config.ADMIN_IDS[0],
                    f"Объявление https://t.me/c/{str(Config.CHANNEL_ID).replace('-100', '')}/{order.channel_message_ids.split(',')[0]} было изменено."
                )
            else:
                # Если объявление еще не опубликовано, редактируем его в чате с администратором
                try:
                    # Редактируем подпись (caption) первого сообщения в медиагруппе
                    first_message_id = int(order.admin_message_ids.split(",")[0])
                    await bot.edit_message_caption(
                        chat_id=Config.ADMIN_IDS[0],
                        message_id=first_message_id,
                        caption=caption
                    )
                except Exception as e:
                    logger.error(f"Ошибка при редактировании сообщения в чате с администратором: {e}")
                    await message.answer("Ошибка при редактировании сообщения. Обратитесь к администратору.", reply_markup=get_main_keyboard())
                    await state.clear()
                    return

            await message.answer("Объявление успешно обновлено.", reply_markup=get_main_keyboard())
        finally:
            session.close()  # Закрываем сессию в любом случае
    else:
        await message.answer("Редактирование отменено.", reply_markup=get_main_keyboard())

    await state.clear()
def register_user_handlers(dp):
    # Основные команды
    dp.message.register(start_command, Command("start"))
    dp.message.register(start_command, Command("помощь"))
    dp.message.register(add_product_command, Command("добавить"))
    dp.message.register(delete_product_command, Command("удалить"))
    dp.message.register(edit_product_command, Command("редактировать"))

    # Обработчики для добавления товара
    dp.message.register(process_product_type, ReviewStates.product_type)
    dp.message.register(process_weight, ReviewStates.weight)
    dp.message.register(process_size, ReviewStates.size)
    dp.message.register(process_insertion, ReviewStates.insertion)
    dp.message.register(process_condition, ReviewStates.condition)
    dp.message.register(process_price, ReviewStates.price)
    dp.message.register(process_hallmark, ReviewStates.hallmark)
    dp.message.register(process_city, ReviewStates.city)
    dp.message.register(process_additional_info, ReviewStates.additional_info)
    dp.message.register(process_contacts, ReviewStates.contacts)
    dp.message.register(process_media, ReviewStates.media)
    dp.message.register(process_confirmation, ReviewStates.confirmation)

    # Обработчики для удаления товара
    dp.message.register(process_delete_order, ReviewStates.delete_order)

    # Обработчики для редактирования товара
    dp.message.register(process_edit_order, ReviewStates.edit_order)
    dp.message.register(process_edit_product_type, ReviewStates.edit_product_type)
    dp.message.register(process_edit_weight, ReviewStates.edit_weight)
    dp.message.register(process_edit_size, ReviewStates.edit_size)
    dp.message.register(process_edit_insertion, ReviewStates.edit_insertion)
    dp.message.register(process_edit_condition, ReviewStates.edit_condition)
    dp.message.register(process_edit_price, ReviewStates.edit_price)
    dp.message.register(process_edit_hallmark, ReviewStates.edit_hallmark)
    dp.message.register(process_edit_city, ReviewStates.edit_city)
    dp.message.register(process_edit_additional_info, ReviewStates.edit_additional_info)
    dp.message.register(process_edit_contacts, ReviewStates.edit_contacts)
    dp.message.register(process_edit_confirmation, ReviewStates.edit_confirmation)
    # Обработчик для неизвестных сообщений
    dp.message.register(unknown_message)

    # Обработчики callback-запросов
    dp.callback_query.register(handle_admin_decision)