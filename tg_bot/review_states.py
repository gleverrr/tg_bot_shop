# tg_bot/review_states.py
from aiogram.fsm.state import State, StatesGroup

class ReviewStates(StatesGroup):
    product_type = State()
    condition = State()
    price = State()
    hallmark = State()
    city = State()
    additional_info = State()
    contacts = State()
    media = State()
    confirmation = State()  # Для подтверждения нового объявления
    delete_order = State()
    edit_order = State()  # Для выбора объявления для редактирования
    edit_product_type = State()  # Для редактирования типа изделия
    edit_condition = State()  # Для редактирования состояния
    edit_price = State()  # Для редактирования цены
    edit_hallmark = State()  # Для редактирования пробы
    edit_city = State()
    edit_additional_info = State()  # Для редактирования дополнительной информации
    edit_contacts = State()  # Для редактирования контактов
    edit_confirmation = State()  # Для подтверждения редактирования