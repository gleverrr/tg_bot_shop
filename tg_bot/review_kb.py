from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/добавить")],
            [KeyboardButton(text="/удалить")],
            [KeyboardButton(text="/редактировать")],
            [KeyboardButton(text="/помощь")]
        ],
        resize_keyboard=True
    )
def get_product_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
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

def get_condition_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Б/у")],
            [KeyboardButton(text="Новый")]
        ],
        resize_keyboard=True
    )

def get_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, подтверждаю")],
            [KeyboardButton(text="Нет, отменить объявление")]
        ],
        resize_keyboard=True
    )
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/help")]
        ],
        resize_keyboard=True
    )