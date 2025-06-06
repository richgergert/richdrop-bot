from aiogram import Bot, Dispatcher, types, executor

# ТВОЙ ТОКЕН — вставлен напрямую (для быстрого старта)
bot = Bot(token="7555461880:AAGKTBCl-KH12mmpwg91ILnpCS9478SrxnY")
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        types.KeyboardButton("📦 Рассчитать заказ с POIZON"),
        types.KeyboardButton("🌍 Заказы с Европы // США"),
        types.KeyboardButton("📦 Оптовые Заказы"),
        types.KeyboardButton("⚡ Экспресс-доставка для срочных заказов")
    )
    await message.answer(
        "Привет!\nЭтот бот поможет тебе рассчитать свой заказ с POIZON.\n\n"
        "<i>Минимальная сумма заказа: 3000₽.</i>",
        parse_mode="HTML",
        reply_markup=kb
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
