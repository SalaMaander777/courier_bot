import datetime
from aiogram import Dispatcher, F, Router,Bot
from aiogram.types import Message, CallbackQuery
from sheets import update_status_by_row_index, status_display, update_courier_id
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import get_confirm_keyboard, get_order_keyboard
import send_orders

main_router = Router()

@main_router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! Ожидаю заявки...")
@main_router.callback_query(F.data.startswith("call:")) 
async def call_handler(callback: CallbackQuery):
    await callback.message.answer(f"Номер телефона для звонка: +{callback.data.split(':')[1]}")


@main_router.callback_query(F.data.startswith("status:"))
async def handle_callback(callback: CallbackQuery):
        if callback.message:
            data: str = callback.data # type: ignore
            parts = data.split(":")
            if data.startswith("status:") and len(parts) == 3:
                _, status, row_index = parts
                row_index = int(row_index)
                confirm_keyboard = get_confirm_keyboard(status, row_index)
                # Показываем кнопки подтверждения
                await callback.message.edit_reply_markup(reply_markup=confirm_keyboard) # type: ignore
                #await callback.message.edit_reply_markup(confirm_keyboard)
                await callback.answer("Подтвердите действие")
         



@main_router.callback_query(F.data.startswith("confirm:"))
async def confirm_handler(callback: CallbackQuery, bot: Bot):
        data: str = callback.data # type: ignore
        parts = data.split(":")
        _, status, row_index = parts
        row_index = int(row_index)
       
        await update_status_by_row_index(row_index, status)
        await update_courier_id(row_index, str(callback.from_user.id), datetime.datetime.now().strftime("%d.%m.%Y"))
        sent_orders =  send_orders.get_send_orders()
        if row_index in sent_orders:
            for msg in sent_orders[row_index]:
                try:
                    if msg["chat_id"] != callback.from_user.id:
                        await bot.delete_message(chat_id=msg["chat_id"], message_id=msg["message_id"])
                except Exception as e:
                    print(f"[ERROR] Не удалось удалить сообщение: {e}")
        # Можно также полностью удалить из трекинга:
            del sent_orders[row_index]
        await callback.message.edit_reply_markup() # pyright: ignore[reportAttributeAccessIssue]
        await callback.answer(f"Статус обновлён: {status_display(status)}")

@main_router.callback_query(F.data.startswith("cancel:"))
async def cancel_handler(callback: CallbackQuery):
    data: str = callback.data # type: ignore
    parts = data.split(":")
    _, status, row_index = parts
    row_index = int(row_index)

    # Предполагаем, что ты можешь получить данные заказа по индексу
    from sheets import get_order_by_row_index
    order = await get_order_by_row_index(row_index)

    # Восстановим исходную клавиатуру заказа
    order_keyboard = get_order_keyboard(
        phone=order["phone"],
        map_link=order["map_link"],
        row_index=str(row_index)
    )

    await callback.message.edit_reply_markup(reply_markup=order_keyboard) # type: ignore
    await callback.answer("Выбор отменён")              