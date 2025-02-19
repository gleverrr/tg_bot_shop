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
        f"Подпишитесь на наш канал: {Config.CHANNEL_LINK}, а также на чат для обсуждения: {Config.CHAT_LINK}.\n\n"
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
    banned_user = session.query(BannedUser).filter(BannedUser.user_id == message.from_user.id).first()
    if banned_user:
        await message.answer("Ой! Извините, вашему аккаунту запрещено выкладывать объявления. "
                             "Если хотите узнать подробности, напишите администратору @BogGermes.")
        return

    await message.answer("Выберите тип изделия (если не нашли нужного, введите вручную):",
                         reply_markup=get_product_type_keyboard())
    await state.set_state(ReviewStates.product_type)

async def process_product_type(message: Message, state: FSMContext):
    await state.update_data(product_type=message.text)
    await message.answer("Состояние товара:", 
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



async def process_contacts(message: Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer(
        "Приложите фотографии или видео товара (максимум 10 файлов). "
        "Когда закончите, нажмите 'далее'.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="далее")]],
            resize_keyboard=True
        )
    )
    await state.set_state(ReviewStates.media)




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
        new_order = Order(
            user_id=message.from_user.id,
            product_type=data["product_type"],
            condition=data["condition"],
            price=data["price"],
            hallmark=data.get("hallmark", "нет"),
            city = data.get('city', 'нет'),
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
            # logger.info("Кнопки 'Разместить' и 'Отказать' отправлены администратору.")
        except Exception as e:
            logger.error(f"Ошибка при отправке кнопок администратору: {e}")
            # await message.answer("Ошибка при отправке кнопок администратору. Обратитесь к разработчику.")
            return

        # Уведомляем пользователя
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
            # logger.info(f"Сообщения с ID {order.channel_message_ids} отправлены в канал.")
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
                        # logger.info(f"Сообщение с ID {msg_id} удалено из чата с администратором.")
                    except Exception as e:
    
                        logger.error(f"Ошибка при удалении сообщения из чата с администратором: {e}")

            # Удаляем сообщение с кнопками
            await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=callback.message.message_id)
            # logger.info(f"Сообщение с кнопками (ID {callback.message.message_id}) удалено из чата с администратором.")
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
                        # logger.info(f"Сообщение с ID {msg_id} удалено из чата с администратором.")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении сообщения из чата с администратором: {e}")

            # Удаляем сообщение с кнопками
            await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=callback.message.message_id)
            # logger.info(f"Сообщение с кнопками (ID {callback.message.message_id}) удалено из чата с администратором.")
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения с кнопками: {e}")

        # Уведомляем администратора
        await callback.answer("Объявление отклонено.")

    await callback.answer()
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
            f"Подпишитесь на наш канал: {Config.CHANNEL_LINK}, а также на чат для обсуждения: {Config.CHAT_LINK}.\n\n"
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
    # keyboard = ReplyKeyboardMarkup(
    #     keyboard=[
    #         [KeyboardButton(text=f"Удалить объявление #{orders[i].id}"), 
    #         KeyboardButton(text=f"Удалить объявление #{orders[i+1].id}")] 
    #         for i in range(0, len(orders), 2)
    #     ],
    #     resize_keyboard=True
    # )

    await message.answer("Выберите объявление для удаления:", reply_markup=keyboard)
    await state.set_state(ReviewStates.delete_order)

async def process_delete_order(message: Message, state: FSMContext, bot: Bot):
    try:
        # Получаем ID заказа из текста сообщения
        order_id = int(message.text.split("#")[1])
        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id, Order.user_id == message.from_user.id).first()

        if order:
            # Удаляем все сообщения из канала, если они были опубликованы
            if order.channel_message_ids:
                message_ids = order.channel_message_ids.split(",")
                for msg_id in message_ids:
                    try:
                        await bot.delete_message(chat_id=Config.CHANNEL_ID, message_id=int(msg_id))
                        # logger.info(f"Сообщение с ID {msg_id} удалено из канала.")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении сообщения из канала: {e}")

            # Удаляем сообщения из чата с администратором, если они были отправлены
            if order.admin_message_ids:
                admin_message_ids = order.admin_message_ids.split(",")
                for msg_id in admin_message_ids:
                    try:
                        await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=int(msg_id))
                        # logger.info(f"Сообщение с ID {msg_id} удалено из чата с администратором.")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении сообщения из чата с администратором: {e}")

            # Удаляем сообщение с кнопками, если оно было отправлено
            if order.admin_buttons_message_id:
                try:
                    await bot.delete_message(chat_id=Config.ADMIN_IDS[0], message_id=order.admin_buttons_message_id)
                    # logger.info(f"Сообщение с кнопками (ID {order.admin_buttons_message_id}) удалено из чата с администратором.")
                except Exception as e:
                    logger.error(f"Ошибка при удалении сообщения с кнопками: {e}")

            # Помечаем объявление как неактивное
            order.is_active = False
            session.commit()

            await message.answer("Объявление удалено.", reply_markup=get_main_keyboard())
        else:
            await message.answer("Объявление не найдено.", reply_markup=get_main_keyboard())
    except Exception as e:
        # logger.error(f"Ошибка при удалении объявления: {e}")
        await message.answer("Произошла ошибка при удалении объявления.", reply_markup=get_main_keyboard())
    finally:
        await state.clear()







async def edit_product_command(message: Message, state: FSMContext):
    session = get_db_session()
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
async def process_edit_order(message: Message, state: FSMContext):
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
            [KeyboardButton(text="Религиозные изделия")]
        ],
        resize_keyboard=True
    )
        )
        await state.set_state(ReviewStates.edit_product_type)
    except Exception as e:
        logger.error(f"Ошибка при выборе объявления для редактирования: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_keyboard())
        await state.clear()
async def process_edit_product_type(message: Message, state: FSMContext):
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
        f"Текущее состояние изделия: {order.condition}\n"
        "Введите новое состояние товара или нажмите 'Оставить без изменений':",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
            [KeyboardButton(text="Оставить без изменений")],
            [KeyboardButton(text="новое")],
            [KeyboardButton(text="б/у")]],
            resize_keyboard=True
        )
    )
    await state.set_state(ReviewStates.edit_condition)
###################################################################
async def process_edit_condition(message: Message, state: FSMContext):
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
async def process_edit_price(message: Message, state: FSMContext):
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
async def process_edit_hallmark(message: Message, state: FSMContext):
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




async def process_edit_city(message: Message, state: FSMContext):
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




async def process_edit_additional_info(message: Message, state: FSMContext):
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

async def process_edit_contacts(message: Message, state: FSMContext):
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
async def process_edit_confirmation(message: Message, state: FSMContext, bot: Bot):
    if message.text == "Да, подтверждаю":
        # Получаем данные из состояния
        data = await state.get_data()
        order_id = data.get("order_id")

        session = get_db_session()
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await message.answer("Ошибка: заказ не найден. Начните заново.", reply_markup=get_main_keyboard())
            await state.clear()
            return

        # Обновляем данные в базе
        order.product_type = data.get("product_type", order.product_type)
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