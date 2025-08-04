import asyncio
import datetime
from aiogram import Bot, Dispatcher
from resources.config import BOT_TOKEN, COURIER_CHAT_IDS
from routers.handlers import main_router
from sheets import get_pending_orders
from keyboards import get_order_keyboard
from routers.statisticRouter import statisctic_router
import send_orders
import logging

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()
dp.include_router(statisctic_router)
dp.include_router(main_router)
DEBUG = True

sent_orders = send_orders.get_send_orders()


async def get_send_orders():
    return sent_orders


async def poll_google_sheet():
    while True:
        print("[INFO] Проверка новых заявок в таблице...")
        date = datetime.datetime.now().strftime("%d.%m.%Y")
        orders = await get_pending_orders(date=date)

        for order in orders:
            row = order["row_index"]
            if row in sent_orders:
                continue

            message_text = (
                f"📦 <b>Новая заявка</b>\n"
                f"📍 <b>Адрес:</b> {order['address']}\n"
                f"📞 <b>Телефон:</b> {order['phone']}\n"
                f"👤 <b>Имя:</b> {order['name']}\n"
                f"💰 <b>Цена:</b> {order['price']}\n"
            )

            keyboard = get_order_keyboard(
                phone=order['phone'],
                map_link=order['map_link'],
                row_index=str(row)
            )

            for chat_id in COURIER_CHAT_IDS:
                try:
                    message = await bot.send_message(chat_id, message_text, reply_markup=keyboard, parse_mode="HTML")
                    sent_orders.setdefault(row, []).append({"chat_id": chat_id, "message_id": message.message_id})
                    print(f"[SENT] Отправлена заявка в строке {row} → chat {chat_id}")
                except Exception as e:
                    print(f"[ERROR] Не удалось отправить заявку: {e}")

        await asyncio.sleep(30)  # ждём 60 секунд


async def main():
    asyncio.create_task(poll_google_sheet())
    await dp.start_polling(bot)


if __name__ == '__main__':
    if DEBUG:
        logging.basicConfig(level=logging.INFO)
        try:
            asyncio.run(main())
        except (KeyboardInterrupt, SystemExit):
            print('Bye!')
