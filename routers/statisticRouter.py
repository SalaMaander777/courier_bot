from aiogram import Router, F
from aiogram.types import Message, CallbackQuery;
from resources.config import ADMINS
from sheets import get_courier_stat, get_courier_stat_for_month, get_sheet_by_name, get_stats, get_stats_for_month, get_stats_region, get_stats_region_for_month
from aiogram.fsm.context import FSMContext
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.state import StatesGroup, State
import datetime
from keyboards import statistic_keyboard, type_statistic_keyboard, get_month_keyboard
statisctic_router  = Router()

class Statistic(StatesGroup):
    date = State()
    type = State()


class Statistic_date(StatesGroup):
    date = State()  
    type = State()

@statisctic_router.message(F.text == "/Statistic")
async def command_statistic(message: Message, state: FSMContext):
    print("[INFO] Статистика")
    if message.from_user.id in ADMINS :
        reply_markup = statistic_keyboard()
        await state.set_state(Statistic.date)
        await message.answer("Выберите дату", reply_markup=reply_markup)

@statisctic_router.callback_query(Statistic.date, F.data.startswith("statistic:"))
async def statistic_handler(callback: CallbackQuery, state: FSMContext):
    print(f"[INFO] {callback.data}")
    if callback.data == "statistic:month":
        await callback.message.edit_text("Выберите месяц", reply_markup=get_month_keyboard())
        await callback.answer()
        return
    if callback.data == "statistic:date":
        await state.set_state(Statistic_date.date)
        await callback.message.edit_text("Введите дату в формате ДД.ММ.ГГГГ", reply_markup=None)
        await callback.answer()
    else:

        await state.update_data(date=callback.data.split(":")[1])
        await callback.message.edit_text(
            f"Выберите тип статистики на дату: {callback.data.split(':')[1]}",
            reply_markup=type_statistic_keyboard()
        )
        await state.set_state(Statistic.type)
        await callback.answer()
@statisctic_router.message(Statistic_date.date)
async def statistic_date_handler(message: Message, state: FSMContext):
    await state.update_data(date=message.text)    
    await message.answer("Выберите тип статистики", reply_markup=type_statistic_keyboard())
    await state.set_state(Statistic_date.type)


@statisctic_router.callback_query(Statistic_date.type, F.data == "city")
async def statistic_date_handler_city(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    print(f"[INFO] {callback.data}")
    data = await state.get_data()
    print(data)
    print(data['date'])
    stat = await get_stats(str(data["date"]))  # используем дату из состояния
    courier_info = await get_courier_stat(data['date'])
    courier_string = ""
    for courier in courier_info:
        name  = courier.get_name()
        zarobotok = courier.get_zarobotok()
        courier_string += f"🚴 <b>{name}</b>:  {zarobotok} ₽\n"
    
    text = f"""
<b>📊 Статистика за {data['date']} по городу</b>

Доставленные: {stat["delivered_counts"]}
Самовывоз: {stat['selfdelivered_counts']}, на сумму: {stat["selfdelivered_summ"]}"
Отказы: {stat["rejected_counts"]}
Отказы (д.о.): {stat["rejected_do_counts"]} и сумма: {stat['rejected_do_summ']}
Отказы (д. не о.):{stat["rejected_dno_counts"]} и сумма: {stat["rejected_dno_summ"]}
Долг: {stat["dolg"]}
Cумма "Доплата" по всем заявкам со статусом "отказ (д.о.) - {stat["doplata_do"]}"
Cумма "Доплата" по всем заявкам со статусом "отказ (д. не о.) - {stat['doplata_dno']}"

Заработок курьера:

{courier_string}
"""
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.clear()
    await callback.answer()



@statisctic_router.callback_query(Statistic.type, F.data == "city")
async def statistic_type_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    print(f"[INFO] {callback.data}")
    data = await state.get_data()
    print(data)
    neded_period = data["date"].split("_")[0]
    # используем дату из состояния
    if data["date"].endswith("_month"):
        stat = await get_stats_for_month(neded_period)
        courier_info = await get_courier_stat_for_month(neded_period)
    elif data["date"] == "today":
        neded_period = get_date_by_state(data)
        stat = await get_stats(str(neded_period))
        courier_info = await get_courier_stat(str(neded_period))    
    elif data["date"] == "yesterday":
        neded_period = get_date_by_state(data)
        stat = await get_stats(str(neded_period))
        courier_info = await get_courier_stat(str(neded_period))
    else:
        stat = await get_stats(str(neded_period))  
        courier_info = await get_courier_stat(str(neded_period))

    courier_string = ""
    for courier in courier_info:
        name  = courier.get_name()
        zarobotok = courier.get_zarobotok()
        courier_string += f"🚴 <b>{name}</b>:  {zarobotok} ₽\n"
    text = f"""
            <b>📊 Статистика за {neded_period} по городу</b>

            Доставленные: {stat["delivered_counts"]}
            Самовывоз: {stat['selfdelivered_counts']}, на сумму: {stat["selfdelivered_summ"]}"
            Отказы: {stat["rejected_counts"]}
            Отказы (д.о.): {stat["rejected_do_counts"]} и сумма: {stat['rejected_do_summ']}
            Отказы (д. не о.):{stat["rejected_dno_counts"]} и сумма: {stat["rejected_dno_summ"]}
            Долг: {stat["dolg"]}
            Cумма "Доплата" по всем заявкам со статусом "отказ (д.о.) - {stat["doplata_do"]}"
            Cумма "Доплата" по всем заявкам со статусом "отказ (д. не о.) - {stat['doplata_dno']}"

            Заработок курьера:
            {courier_string}
            """
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.clear()
    await callback.answer()
@statisctic_router.callback_query(Statistic_date.type, F.data== "region")
async def statistic_type_date_handler_region(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    print(f"[INFO] {callback.data}")
    
    data = await state.get_data()
    neded_period = data["date"]
    stat = await get_stats_region(str(neded_period))   # используем дату из состояния
    
    text = f"""
             <b>📊 Статистика за {neded_period} по регионам</b>

Доставленные: {stat["delivered_counts"]}
Единицы: {stat['delivered_quantity']}

Возвраты: кол-во: {stat["returns_counts"]}
          сумма:  {stat["returns_summ"]}                        

Долг: {stat["dolg"]}
Доплата (по сумме): {stat["doplata_summ"]}

Выручка: {stat["viruchka"]}
Доплата: {stat["doplata"]}

""" 
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.clear()
    await callback.answer()

@statisctic_router.callback_query(Statistic.type, F.data== "region")
async def statistic_type_handler_region(callback: CallbackQuery, state: FSMContext):
    await state.update_data(type=callback.data)
    print(f"[INFO] {callback.data}")
    
    data = await state.get_data()
    neded_period = data["date"].split("_")[0]
    if data["date"].endswith("_month"):
        stat = await get_stats_region_for_month(str(neded_period))
    else:
        neded_period = get_date_by_state(data)
        stat = await get_stats_region(str(neded_period))  

    text = f"""
<b>📊 Статистика за {neded_period} по регионам</b>

Доставленные: {stat["delivered_counts"]}
Единицы: {stat['delivered_quantity']}

Возвраты: кол-во: {stat["returns_counts"]}
          сумма:  {stat["returns_summ"]}                        

Долг: {stat["dolg"]}
Доплата (по сумме): {stat["doplata_summ"]}

Выручка: {stat["viruchka"]}
Доплата: {stat["doplata"]}

""" 
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.clear()
    await callback.answer()

def get_date_by_state(data: dict):
    if data["date"] == "today":
        return datetime.datetime.now().strftime("%d.%m.%Y")
    elif data["date"] == "yesterday":
        return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
    elif data["date"] == "date":
        return data["date"]
    elif data["date"] == "month":
        return None
@statisctic_router.callback_query(F.data.startswith("month:"))
async def handle_month_selection(callback: CallbackQuery, state: FSMContext):
    month_value = callback.data.split(":")[1]  
    print(callback.data)# пример: "08.2025"
    await state.update_data(date=month_value + "_month" )
    await callback.message.edit_text(
        f"Вы выбрали: {month_value}\nВыберите тип статистики:",
        reply_markup=type_statistic_keyboard()
    )
    await state.set_state(Statistic.type)
    await callback.answer()