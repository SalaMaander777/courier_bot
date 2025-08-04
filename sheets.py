import asyncio
import datetime
from gspread_asyncio import AsyncioGspreadClientManager
from decimal import Decimal
from oauth2client.service_account import ServiceAccountCredentials
import resources.config as config
from models.couriers import Courier

SPREADSHEET_ID = config.SPREADSHEET_ID
SHEET_NAME = datetime.datetime.now().strftime("%d.%m.%Y")


# Создание асинхронного клиента
def get_creds():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    return ServiceAccountCredentials.from_json_keyfile_name("resources/credentials.json", scopes=scope)  # type: ignore


agcm = AsyncioGspreadClientManager(get_creds)


# Получение листа
async def get_sheet():
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(SPREADSHEET_ID)
    worksheet = await spreadsheet.worksheet(SHEET_NAME)
    return worksheet


async def get_sheet_by_name(name: str):
    agc = await agcm.authorize()
    spreadsheet = await agc.open_by_key(SPREADSHEET_ID)
    worksheet = await spreadsheet.worksheet(name)
    return worksheet


# Получение заявок
async def get_pending_orders(date):
    sheet = await get_sheet_by_name(date)
    records = await sheet.get_all_records()

    orders = []
    for i, row in enumerate(records, start=2):
        if row["ГЕО"] == "Город" and row["Статус"] == "Передан в доставку":
            orders.append({
                "row_index": i,
                "name": row["Имя"],
                "phone": row["Телефон"],
                "address": row["Адрес"],
                "price": row["Цена"],
                "map_link": row.get("ya map", "#")
            })
    return orders


# Обновление статуса
async def update_status_by_row_index(row_index: int, status: str):
    sheet = await get_sheet_by_name(SHEET_NAME)

    col_status = 13
    col_price = 6
    col_delivery = 8
    col_bonus = 9

    await sheet.update_cell(row_index, col_status, status_display(status))

    if status == "rejected_do":
        await sheet.update_cell(row_index, col_price, 0)
    elif status == "rejected_dno":
        await sheet.update_cell(row_index, col_price, 0)
        await sheet.update_cell(row_index, col_delivery, 0)
        await sheet.update_cell(row_index, col_bonus, 250)


# Преобразование кода статуса в текст
def status_display(code: str) -> str:
    return {
        "delivered": "Доставлен",
        "rejected": "Отказ",
        "rejected_do": "Отказ (д.о.)",
        "rejected_dno": "Отказ (д. не о.)"
    }.get(code, code)


# Получить заказ по индексу строки
async def get_order_by_row_index(row_index: int) -> dict:
    orders = await get_pending_orders(SHEET_NAME)
    for order in orders:
        if order["row_index"] == row_index:
            return order
    raise ValueError(f"Заявка с индексом {row_index} не найдена")


async def update_courier_id(row_index: int, courier_id: str, date):
    sheet = await get_sheet_by_name(date)
    await sheet.update_cell(row_index, 15, courier_id)


async def get_stats(date: str):
    print(date)
    sheet = await get_sheet_by_name(date)
    # records = await worksheet.get_all_records()
    # sheet = await get_sheet()
    records = await sheet.get_all_records()
    statistics = {

        "delivered_counts": 0,
        "selfdelivered_counts": 0,
        "selfdelivered_summ": Decimal("0"),
        "rejected_counts": 0,
        "rejected_do_counts": 0,
        "rejected_do_summ": Decimal("0"),
        "rejected_dno_counts": 0,
        "rejected_dno_summ": Decimal("0"),
        "dolg": Decimal("0"),
        "doplata_do": Decimal("0"),
        "doplata_dno": Decimal("0"),
        "couriers": [],

    }

    for row in records:
        city = row["ГЕО"]
        status = row["Статус"]
        if city == "Город":
            if status == "Доставлен":
                statistics["delivered_counts"] += 1

            if status == "Самовывоз":
                statistics["selfdelivered_counts"] += 1
                statistics["selfdelivered_summ"] += Decimal(row["Итого"])

            if status == "Отказ":
                statistics["rejected_counts"] += 1

            if status == "Отказ (д.о.)":
                statistics["rejected_do_counts"] += 1
                statistics["rejected_do_summ"] += Decimal(statistics["rejected_do_counts"]) * 90

            if status == "Отказ (д. не о.)":
                statistics["rejected_dno_counts"] += 1
                statistics["rejected_dno_summ"] += Decimal(statistics["rejected_dno_counts"]) * 250

            if city == "Город" and status == "Доставлен":
                statistics["dolg"] += Decimal(row["Итого"])

            if status == "Отказ (д.о.)":
                statistics["doplata_do"] += Decimal(row["Доплата"])

            if status == "Отказ (д. не о.)":
                statistics["doplata_dno"] += Decimal(row["Доплата"])
    print(statistics)
    return statistics


async def get_stats_region(date: str):
    sheet = await get_sheet_by_name(date)
    records = await sheet.get_all_records()
    statistics = {
        "delivered_counts": 0,
        "delivered_quantity": 0,
        "returns_counts": 0,
        "returns_summ": Decimal("0"),
        "dolg": Decimal("0"),
        "doplata_summ": Decimal("0"),
        "viruchka": Decimal("0"),
        "doplata": Decimal("0")
    }
    for row in records:
        region = row["ГЕО"]
        status = row["Статус"]
        if region == "Регион":
            if status == "Доставлен":
                statistics["delivered_counts"] += 1
                statistics["delivered_quantity"] += row["Количество"]
                statistics["dolg"] += Decimal(row["Итого"])

            if status == "Отказ":
                statistics["returns_counts"] += 1
                statistics["returns_summ"] += (Decimal(row["Доставка"]) + Decimal(row["Доплата"]) + Decimal("200"))

        if status == "Доставлен":
            statistics["viruchka"] += Decimal(row["Итого"])
            statistics["doplata"] += Decimal(row["Доплата"])

    return statistics


async def get_courier_stat(date: str):
    array_of_couriers = []
    sheet = await get_sheet_by_name(date)
    records = await sheet.get_all_records()
    for row in records:
        if row['courier_id'] != "":
            if row["Статус"] == "Доставлен" or row["Статус"] == "Отказ (д.о.)" or row["Статус"] == "Отказ (д. не о.)":
                courier_id = row['courier_id']
                flaG = await __check_courier__(array_of_couriers, courier_id)
                dostavka = row['Доставка']
                doplata = row["Доплата"]
                if not flaG:
                    courier = Courier(courier_id, config.courier[str(courier_id)])
                    courier.add(Decimal(dostavka), Decimal(doplata))
                    array_of_couriers.append(courier)
                if flaG:
                    for courier in array_of_couriers:
                        if courier.get_id() == courier_id:
                            courier.add(Decimal(dostavka), Decimal(doplata))

    print(array_of_couriers)
    return array_of_couriers


async def __check_courier__(array_of_couriers, courier_id):
    for courier in array_of_couriers:
        if courier.get_id() == courier_id:
            return True
    return False


async def get_courier_stat_for_month(month: str):
    array_of_couriers = []
    year = int(month.split(".")[1])
    month_num = int(month.split(".")[0])

    for day in range(1, 32):
        try:
            date_obj = datetime.date(year, month_num, day)
            date_str = date_obj.strftime("%d.%m.%Y")
            day_couriers = await get_courier_stat(date_str)

            for day_courier in day_couriers:
                match = next((c for c in array_of_couriers if c.get_id() == day_courier.get_id()), None)
                if match:
                    match.add(day_courier.get_dostavka(), day_courier.get_doplata())
                else:
                    array_of_couriers.append(day_courier)
        except Exception:
            continue

    return array_of_couriers


async def get_stats_for_month(month: str):
    """month format: '08.2025'"""
    stats_total = {
        "delivered_counts": 0,
        "selfdelivered_counts": 0,
        "selfdelivered_summ": Decimal("0"),
        "rejected_counts": 0,
        "rejected_do_counts": 0,
        "rejected_do_summ": Decimal("0"),
        "rejected_dno_counts": 0,
        "rejected_dno_summ": Decimal("0"),
        "dolg": Decimal("0"),
        "doplata_do": Decimal("0"),
        "doplata_dno": Decimal("0"),
    }

    year = int(month.split(".")[1])
    month_num = int(month.split(".")[0])

    for day in range(1, 32):
        try:
            date_obj = datetime.date(year, month_num, day)
            sheet_name = date_obj.strftime("%d.%m.%Y")
            day_stat = await get_stats(sheet_name)
            for key in stats_total:
                stats_total[key] += day_stat[key]
        except Exception:
            continue  # Пропускаем несуществующие даты или отсутствующие листы

    return stats_total


async def get_stats_region_for_month(month: str):
    """month format: '08.2025'"""
    stats_total = {
        "delivered_counts": 0,
        "delivered_quantity": 0,
        "returns_counts": 0,
        "returns_summ": Decimal("0"),
        "dolg": Decimal("0"),
        "doplata_summ": Decimal("0"),
        "viruchka": Decimal("0"),
        "doplata": Decimal("0")
    }

    year = int(month.split(".")[1])
    month_num = int(month.split(".")[0])

    for day in range(1, 32):
        try:
            date_obj = datetime.date(year, month_num, day)
            date_str = date_obj.strftime("%d.%m.%Y")
            day_stats = await get_stats_region(date_str)

            for key in stats_total:
                stats_total[key] += day_stats[key]
        except Exception:
            continue  # Пропускаем ошибки и несуществующие листы

    return stats_total



if __name__ == "__main__":
    asyncio.run(get_pending_orders("01.08.2025"))