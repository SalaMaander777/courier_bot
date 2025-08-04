import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_order_keyboard(phone: str, map_link: str, row_index: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Позвонить", callback_data=f"call:{phone}")],
        [InlineKeyboardButton(text="📍 В путь", url=map_link)],
        [
            InlineKeyboardButton(text="✅ Доставлен", callback_data=f"status:delivered:{row_index}"),
            InlineKeyboardButton(text="❌ Отказ", callback_data=f"status:rejected:{row_index}")
        ],
        [
            InlineKeyboardButton(text="❌ Отказ (д.о.)", callback_data=f"status:rejected_do:{row_index}"),
            InlineKeyboardButton(text="❌ Отказ (д. не о.)", callback_data=f"status:rejected_dno:{row_index}")
        ]
    ])


def get_confirm_keyboard(status: str, row_index: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{status}:{row_index}"),
            InlineKeyboardButton(text="❎ Отмена", callback_data=f"cancel:{status}:{row_index}")
        ]
    ])


def statistic_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Cтатистика за сегодня", callback_data="statistic:today")],
        [InlineKeyboardButton(text="📊 Cтатистика вчера", callback_data="statistic:yesterday")],
        [InlineKeyboardButton(text="📊 Cтатистика по дате", callback_data="statistic:date")],
        [InlineKeyboardButton(text="📊 Cтатистика за месяц", callback_data="statistic:month")]
    ])


def type_statistic_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Cтатистика по городу", callback_data="city")],
        [InlineKeyboardButton(text="📊 Cтатистика по регионам", callback_data="region")]
    ])


def get_month_keyboard():
    current_month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    buttons = []
    for i in range(current_month, 0, -1):
        month_label = month_names[i - 1]
        callback = f"month:{i:02}.{year}"
        buttons.append([InlineKeyboardButton(text=f"📆 {month_label}", callback_data=callback)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
