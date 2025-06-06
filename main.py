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
user_state = {}
last_result = {}

# 🔁 Автообновление курса
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

# 📲 Клавиатуры
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("💰 РАССЧИТАТЬ ЗАКАЗ"),
        KeyboardButton("💸 АКТУАЛЬНЫЙ КУРС"),
        KeyboardButton("📦 КАК ОФОРМИТЬ?")
    )
    return kb

def category_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("👕 Одежда"),
        KeyboardButton("👟 Обувь"),
        KeyboardButton("📦 Другое")
    )
    return kb

def back_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Главная"))
    return kb

def manager_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📩 Связаться с менеджером"))
    kb.add(KeyboardButton("🔙 Главная"))
    return kb

# ▶️ Старт
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "Добро пожаловать в калькулятор заказа с Poizon!\n\n"
        "Нажмите <b>РАССЧИТАТЬ ЗАКАЗ</b> и укажите цену товара в юанях (¥).",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# 💰 Выбор категории
@dp.message_handler(lambda msg: msg.text == "💰 РАССЧИТАТЬ ЗАКАЗ")
async def ask_category(message: types.Message):
    user_state[message.from_user.id] = "awaiting_category"
    await message.answer("Выберите категорию товара:", reply_markup=category_menu())

# ✅ После выбора категории
@dp.message_handler(lambda msg: msg.text in ["👕 Одежда", "👟 Обувь", "📦 Другое"])
async def after_category_selected(message: types.Message):
    user_state[message.from_user.id] = "awaiting_price"
    await message.answer(
        'Отлично! Теперь напишите цену товара на из приложения "POIZON" в виде числа (например: 800)',
        reply_markup=back_menu()
    )

# 🔙 Вернуться на главную
@dp.message_handler(lambda msg: msg.text == "🔙 Главная")
async def back_home(message: types.Message):
    user_state.pop(message.from_user.id, None)
    await start_handler(message)

# 📩 Связаться с менеджером
@dp.message_handler(lambda msg: msg.text == "📩 Связаться с менеджером")
async def contact_manager(message: types.Message):
    await message.answer("Связь с менеджером: @richgergert")

# 💸 Показать курс
@dp.message_handler(lambda msg: msg.text == "💸 АКТУАЛЬНЫЙ КУРС")
async def show_rate(message: types.Message):
    fetch_exchange_rate()
    await message.answer(f"💱 Курс обновлён!\n<b>1 ¥ = {EXCHANGE_RATE}₽</b>", parse_mode="HTML")

# 📦 Как оформить
@dp.message_handler(lambda msg: msg.text == "📦 КАК ОФОРМИТЬ?")
async def how_to_order(message: types.Message):
    await message.answer("Для оформления заказа напишите нашему менеджеру — @richgergert")

# 📉 Скидки
@dp.message_handler(lambda msg: msg.text.startswith("📉 СКИДКА"))
async def handle_discount(message: types.Message):
    user_id = message.from_user.id
    if user_id not in last_result:
        await message.answer("Сначала сделай расчёт.", reply_markup=main_menu())
        return

    discount_percent = float(message.text.replace("📉 СКИДКА", "").replace("%", "").strip())
    original = last_result[user_id]
    discounted = round(original * (1 - discount_percent / 100), 2)

    await message.answer(f"💸 Итог со скидкой {discount_percent}%: <b>{discounted}₽</b>", parse_mode="HTML", reply_markup=main_menu())

# 💬 Расчёт стоимости (как у конкурента)
@dp.message_handler(lambda msg: user_state.get(msg.from_user.id) == "awaiting_price")
async def calculate_price(message: types.Message):
    try:
        price_yuan = float(message.text.replace(",", "."))
        exchange = EXCHANGE_RATE

        rub_price = round(price_yuan * exchange, 2)
        poizon_delivery = 316
        china_russia = 400
        insurance = round(rub_price * 0.03, 2)
        service_fee = 500
        total = round(rub_price + poizon_delivery + china_russia + insurance + service_fee, 2)

        last_result[message.from_user.id] = total
        user_state.pop(message.from_user.id, None)

        await message.answer(
            f"Сделал расчет вашего товара:\n\n"
            f"<b>Итого: стоимость заказа {total}₽</b>\n\n"
            f"<u>Детализация расчета:</u>\n"
            f"- Товар: {rub_price}₽\n"
            f"- Доставка от Poizon: {poizon_delivery}₽\n"
            f"- Доставка 🇨🇳 Китай – 🇷🇺 Россия: {china_russia}₽\n"
            f"- Страховка (3% от цены): {insurance}₽\n"
            f"- Комиссия сервиса: {service_fee}₽\n\n"
            f"Чтобы заказать данный товар, напишите нашему менеджеру – @richgergert",
            parse_mode="HTML",
            reply_markup=manager_menu()
        )
    except ValueError:
        await message.answer("❗ Введите цену числом, например: 800")

# ▶️ Запуск
if __name__ == "__main__":
    fetch_exchange_rate()
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp, skip_updates=True)
