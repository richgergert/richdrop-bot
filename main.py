from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os
import requests
import asyncio
import aioschedule
from datetime import datetime

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

EXCHANGE_RATE = 13.2
DELIVERY = 550
user_state = {}
last_result = {}

# Автообновление курса
def fetch_exchange_rate():
    global EXCHANGE_RATE
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url)
        data = response.json()
        EXCHANGE_RATE = round(data["Valute"]["CNY"]["Value"], 2)
        print(f"[{datetime.now()}] ✅ Курс обновлён: {EXCHANGE_RATE}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Ошибка обновления курса: {e}")

async def scheduler():
    aioschedule.every(12).hours.do(fetch_exchange_rate)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)

# Клавиатуры
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("💰 РАССЧИТАТЬ ЗАКАЗ"),
        KeyboardButton("💸 АКТУАЛЬНЫЙ КУРС"),
        KeyboardButton("📦 КАК ОФОРМИТЬ?")
    )
    return kb

def discount_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("🔁 НОВЫЙ РАСЧЕТ"),
        KeyboardButton("📉 СКИДКА 12.5%"),
        KeyboardButton("📉 СКИДКА 25%"),
        KeyboardButton("📉 СКИДКА 37.5%")
    )
    return kb

# Хендлеры
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "Добро пожаловать в калькулятор заказа с Poizon!\n\n"
        "Нажмите <b>РАССЧИТАТЬ ЗАКАЗ</b> и укажите цену товара в юанях (¥).\n"
        "Стоимость рассчитывается автоматически 💸",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

@dp.message_handler(lambda msg: msg.text == "💰 РАССЧИТАТЬ ЗАКАЗ")
async def ask_price(message: types.Message):
    user_state[message.from_user.id] = "awaiting_price"
    await message.answer("Укажи цену в ¥ (юанях):")

@dp.message_handler(lambda msg: msg.text == "💸 АКТУАЛЬНЫЙ КУРС")
async def show_rate(message: types.Message):
    fetch_exchange_rate()
    await message.answer(f"💱 Курс обновлён!\n<b>1 ¥ = {EXCHANGE_RATE}₽</b>", parse_mode="HTML")

@dp.message_handler(lambda msg: msg.text == "📦 КАК ОФОРМИТЬ?")
async def how_to_order(message: types.Message):
    await message.answer("Для оформления заказа пиши: @richgergert")

@dp.message_handler(lambda msg: msg.text == "🔁 НОВЫЙ РАСЧЕТ")
async def new_calc(message: types.Message):
    await ask_price(message)

@dp.message_handler(lambda msg: msg.text.startswith("📉 СКИДКА"))
async def handle_discount(message: types.Message):
    user_id = message.from_user.id
    if user_id not in last_result:
        await message.answer("Сначала сделай расчёт.", reply_markup=main_menu())
        return

    discount_percent = float(message.text.replace("📉 СКИДКА", "").replace("%", "").strip())
    original = last_result[user_id]
    discounted = round(original * (1 - discount_percent / 100), 2)

    await message.answer(f"💸 Итог со скидкой {discount_percent}%: <b>{discounted}₽</b>", parse_mode="HTML", reply_markup=discount_menu())

@dp.message_handler(lambda msg: user_state.get(msg.from_user.id) == "awaiting_price")
async def calculate_price(message: types.Message):
    try:
        price_yuan = float(message.text.replace(",", "."))
        result = round(price_yuan * EXCHANGE_RATE + DELIVERY, 2)
        user_id = message.from_user.id
        last_result[user_id] = result
        user_state.pop(user_id, None)

        await message.answer(
            f"💰 <b>Цена по курсу:</b> {EXCHANGE_RATE}₽/¥\n"
            f"📦 <b>Доставка:</b> {DELIVERY}₽\n"
            f"— — — — — — — — — —\n"
            f"💸 <b>ИТОГО:</b> <u>{result}₽</u>\n\n"
            f"Для оформления заказа — @richgergert\n\n"
            f"<i>Программа лояльности:</i>\n"
            f"от 2500¥ — 12.5%\nот 5000¥ — 25%\nот 7000¥ — 37.5%",
            parse_mode="HTML",
            reply_markup=discount_menu()
        )
    except ValueError:
        await message.answer("❗ Введите цену числом, например: 680 или 340.5")

# Запуск
if __name__ == "__main__":
    fetch_exchange_rate()
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp, skip_updates=True)
