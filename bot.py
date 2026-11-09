import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ FREE"), KeyboardButton(text="👑 PREMIUM")],
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="🔌 Подключение"), KeyboardButton(text="🆘 Поддержка")]
    ],
    resize_keyboard=True
)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "⚡ Добро пожаловать в VOLT VPN!\n\n"
        "Твой персональный кабинет управления подключением.\n\n"
        "Выбери нужный раздел:",
        reply_markup=main_menu
    )


@dp.message(F.text == "⚡ FREE")
async def free(message: Message):
    await message.answer(
        "⚡ VOLT FREE\n\n"
        "Трафик: 3 ГБ в месяц\n"
        "Скорость: ограниченная\n\n"
        "Скоро здесь появится подключение."
    )


@dp.message(F.text == "👑 PREMIUM")
async def premium(message: Message):
    await message.answer(
        "👑 VOLT PREMIUM\n\n"
        "Цена: 219 ₽ / месяц\n"
        "Высокая скорость\n"
        "Расширенные возможности\n\n"
        "Подключение оплаты добавим позже."
    )


@dp.message(Command("profile"))
@dp.message(F.text == "👤 Мой профиль")
async def profile(message: Message):
    await message.answer(
        f"👤 Твой профиль\n\n"
        f"Telegram ID: {message.from_user.id}\n"
        f"Тариф: FREE"
    )


@dp.message(Command("subscription"))
async def subscription(message: Message):
    await premium(message)


@dp.message(Command("connect"))
@dp.message(F.text == "🔌 Подключение")
async def connect(message: Message):
    await message.answer(
        "🔌 Настройка VPN-подключения появится здесь."
    )


@dp.message(Command("support"))
@dp.message(F.text == "🆘 Поддержка")
async def support(message: Message):
    await message.answer(
        "🆘 По вопросам работы VOLT VPN напиши в поддержку."
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
