import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from config import Config
from tg_bot.db_connection import get_db_session
from tg_bot.models import Base, Raffle, Order
from sqlalchemy.orm import Session
import asyncio

# Настройка логирования
# logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=Config.SECOND_BOT_TOKEN)
dp = Dispatcher()

# Состояния для FSM
class RaffleStates(StatesGroup):
    waiting_for_raffle_type = State()
    waiting_for_raffle_message = State()
    waiting_for_confirmation = State()
    raffle_active = State()
    waiting_for_end_confirmation = State()  # Новое состояние для подтверждения завершения

# Клавиатура для админа
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить розыгрыш")]  # Кнопка "Добавить розыгрыш"
    ],
    resize_keyboard=True  # Автоматическое изменение размера клавиатуры
)

# Клавиатура для управления розыгрышем
raffle_management_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Количество участников")],  # Кнопка "Количество участников"
        [KeyboardButton(text="Завершить розыгрыш")]  # Кнопка "Завершить розыгрыш"
    ],
    resize_keyboard=True
)

# Клавиатура для подтверждения завершения
confirmation_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Да")],  # Кнопка "Да"
        [KeyboardButton(text="Нет")]  # Кнопка "Нет"
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        await message.answer("Выберите действие:", reply_markup=admin_keyboard)

# Обработка кнопки "Добавить розыгрыш"
@dp.message(lambda message: message.text == "Добавить розыгрыш")
async def add_raffle(message: types.Message, state: FSMContext):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        await message.answer("Выберите тип розыгрыша:", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Для продавцов")],  # Кнопка "Для продавцов"
                [KeyboardButton(text="Для всех")]  # Кнопка "Для всех"
            ],
            resize_keyboard=True
        ))
        await state.set_state(RaffleStates.waiting_for_raffle_type)  # Установка состояния

# Обработка выбора типа розыгрыша
@dp.message(RaffleStates.waiting_for_raffle_type)
async def process_raffle_type(message: types.Message, state: FSMContext):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        await state.update_data(raffle_type=message.text)
        await message.answer("Пришлите сообщение для розыгрыша:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(RaffleStates.waiting_for_raffle_message)  # Установка состояния

# Обработка сообщения для розыгрыша
@dp.message(RaffleStates.waiting_for_raffle_message)
async def process_raffle_message(message: types.Message, state: FSMContext):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        await state.update_data(raffle_message=message.text)
        await message.answer("Вы уверены, что хотите разместить данный розыгрыш?", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Разместить")],  # Кнопка "Разместить"
                [KeyboardButton(text="Отменить")]  # Кнопка "Отменить"
            ],
            resize_keyboard=True
        ))
        await state.set_state(RaffleStates.waiting_for_confirmation)  # Установка состояния

# Обработка подтверждения розыгрыша
@dp.message(RaffleStates.waiting_for_confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        if message.text == "Разместить":
            data = await state.get_data()
            raffle_type = data['raffle_type']
            raffle_message = data['raffle_message']

            # Создаем кнопку "Принять участие"
            participation_button = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Принять участие", callback_data="participate")]
                ]
            )

            session = None
            try:
                # Отправка сообщения в канал с кнопкой
                channel_message = await bot.send_message(
                    Config.CHANNEL_ID,
                    raffle_message,
                    reply_markup=participation_button
                )

                # Создаем таблицу raffle (если она еще не создана)
                session = get_db_session()
                Base.metadata.create_all(session.bind)

                # Отправляем сообщение администратору
                await message.answer(
                    "Розыгрыш размещен!",
                    reply_markup=raffle_management_keyboard
                )

                # Сохраняем данные о розыгрыше в базе данных
                new_raffle = Raffle(
                    channel_message_id=channel_message.message_id,
                    raffle_type=raffle_type,
                    raffle_message=raffle_message
                )
                session.add(new_raffle)
                session.commit()

                await state.set_state(RaffleStates.raffle_active)  # Устанавливаем состояние "розыгрыш активен"
            except Exception as e:
                await message.answer(f"Ошибка при отправке сообщения в канал: {e}")
            finally:
                if session:
                    session.close()
        else:
            await message.answer("Розыгрыш отменен.", reply_markup=admin_keyboard)
            await state.clear()  # Очистка состояния

# Обработка нажатия кнопки "Принять участие"
@dp.callback_query(lambda query: query.data == "participate")
async def handle_participation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username

    if not username:
        # Если у пользователя нет username
        await callback_query.answer("Задайте username в профиле для участия в розыгрыше.", show_alert=True)
        return

    session = None
    try:
        session = get_db_session()

        # Получаем последний активный розыгрыш
        active_raffle = session.query(Raffle).order_by(Raffle.id.desc()).first()

        if not active_raffle:
            await callback_query.answer("Активных розыгрышей нет.", show_alert=True)
            return

        # Проверяем, участвовал ли пользователь ранее
        existing_participant = session.query(Raffle).filter(Raffle.user_id == user_id).first()
        if existing_participant:
            await callback_query.answer("Вы уже участвуете в розыгрыше!", show_alert=True)
            return

        # Добавляем участника в таблицу
        new_participant = Raffle(
            user_id=user_id,
            telegram_tag=username,
            channel_message_id=active_raffle.channel_message_id,
            raffle_type=active_raffle.raffle_type,
            raffle_message=active_raffle.raffle_message
        )
        session.add(new_participant)
        session.commit()

        await callback_query.answer("Вы успешно зарегистрированы в розыгрыше!", show_alert=True)
    finally:
        if session:
            session.close()

# Обработка команды "Количество участников"
@dp.message(lambda message: message.text == "Количество участников")
async def get_participants_count(message: types.Message):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        session = None
        try:
            session = get_db_session()
            participants_count = session.query(Raffle).filter(Raffle.user_id != None).count()
            await message.answer(f"Количество участников: {participants_count}")
        finally:
            if session:
                session.close()

# Обработка команды "Завершить розыгрыш"
@dp.message(lambda message: message.text == "Завершить розыгрыш")
async def end_raffle(message: types.Message, state: FSMContext):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        await message.answer("Вы уверены, что хотите завершить розыгрыш?", reply_markup=confirmation_keyboard)
        await state.set_state(RaffleStates.waiting_for_end_confirmation)  # Установка состояния

# Обработка подтверждения завершения розыгрыша
@dp.message(RaffleStates.waiting_for_end_confirmation)
async def process_end_confirmation(message: types.Message, state: FSMContext):
    if message.from_user.id in Config.ADMIN_IDS:  # Проверка, что пользователь — администратор
        if message.text == "Да":
            session = None
            try:
                session = get_db_session()

                # Получаем последний активный розыгрыш
                active_raffle = session.query(Raffle).order_by(Raffle.id.desc()).first()

                if not active_raffle:
                    await message.answer("Активных розыгрышей нет.", reply_markup=raffle_management_keyboard)
                    return

                # Получаем участников розыгрыша
                participants = session.query(Raffle).filter(Raffle.user_id != None).all()

                if not participants:
                    await message.answer("Нет участников для розыгрыша.", reply_markup=raffle_management_keyboard)
                    return

                # Выбираем победителей
                if active_raffle.raffle_type == "Для продавцов":
                    # Получаем активные объявления участников
                    active_orders = session.query(Order).filter(
                        Order.user_id.in_([p.user_id for p in participants]),
                        Order.is_active == True
                    ).all()

                    # Считаем количество активных объявлений для каждого участника
                    user_order_counts = {}
                    for order in active_orders:
                        if order.user_id in user_order_counts:
                            user_order_counts[order.user_id] += 1
                        else:
                            user_order_counts[order.user_id] = 1

                    # Формируем список участников с учетом количества активных объявлений
                    weighted_participants = []
                    for participant in participants:
                        if participant.user_id in user_order_counts:
                            weighted_participants.extend([participant] * user_order_counts[participant.user_id])

                    # Выбираем уникальных победителей
                    unique_winners = []
                    while len(unique_winners) < 10 and weighted_participants:
                        winner = random.choice(weighted_participants)
                        if winner.user_id not in [w.user_id for w in unique_winners]:
                            unique_winners.append(winner)
                        weighted_participants = [p for p in weighted_participants if p.user_id != winner.user_id]

                    winners = unique_winners
                else:
                    # Выбираем случайных участников
                    winners = random.sample(participants, min(len(participants), 10))

                # Формируем список победителей
                if winners:
                    winners_list = "\n".join([f"@{winner.telegram_tag} (ID: {winner.user_id})" for winner in winners])
                    await message.answer(f"Победители:\n{winners_list}", reply_markup=admin_keyboard)
                else:
                    await message.answer("Нет победителей.", reply_markup=admin_keyboard)

                # Удаляем сообщение с розыгрышем из канала
                try:
                    await bot.delete_message(Config.CHANNEL_ID, active_raffle.channel_message_id)
                except Exception as e:
                    logging.error(f"Ошибка при удалении сообщения: {e}")

                # Очищаем таблицу raffle
                session.query(Raffle).delete()
                session.commit()

                # Очищаем состояние
                await state.clear()
            finally:
                if session:
                    session.close()
        else:
            await message.answer("Розыгрыш не завершен.", reply_markup=raffle_management_keyboard)
            await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())