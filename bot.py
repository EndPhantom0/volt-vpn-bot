import asyncio
import os
import sqlite3
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")

# НАСТРОЙКИ
DB_PATH = "/data/volt.db"
ADMIN_ID = 8843062369

os.makedirs("/data", exist_ok=True)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# БАЗА ДАННЫХ
def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                tariff TEXT DEFAULT 'FREE',
                traffic_used_bytes INTEGER DEFAULT 0,
                registered_at TEXT,
                subscription_until TEXT
            )
        """)


def register_user(user):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with get_db() as db:
        db.execute("""
            INSERT INTO users (
                telegram_id, username, first_name,
                tariff, traffic_used_bytes, registered_at
            )
            VALUES (?, ?, ?, 'FREE', 0, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (
            user.id,
            user.username,
            user.first_name,
            now
        ))


def get_user(user_id):
    with get_db() as db:
        return db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (user_id,)
        ).fetchone()


# ГЛАВНОЕ МЕНЮ
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⚡ FREE"), KeyboardButton(text="👑 PREMIUM")],
        [KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="🔌 Подключение"), KeyboardButton(text="🆘 Поддержка")]
    ],
    resize_keyboard=True
)


# СТАРТ
@dp.message(CommandStart())
async def start(message: Message):
    register_user(message.from_user)

    await message.answer(
        "⚡ VOLT VPN\n\n"
        "Твоя скорость. Твоя приватность. Твой контроль.\n\n"
        "Добро пожаловать в VOLT.\n"
        "Выбери свой режим:",
        reply_markup=main_menu
    )


# FREE
@dp.message(F.text == "⚡ FREE")
async def free(message: Message):
    await message.answer(
        "⚡ VOLT FREE\n\n"
        "Трафик: 3 ГБ в месяц\n"
        "Скорость: ограниченная\n\n"
        "Подключение появится здесь."
    )


# PREMIUM
@dp.message(F.text == "👑 PREMIUM")
async def premium(message: Message):
    await message.answer(
        "👑 VOLT PREMIUM\n\n"
        "Цена: 219 ₽ / месяц\n"
        "Высокая скорость\n"
        "Расширенные возможности\n\n"
        "Оплата появится здесь."
    )


# ПРОФИЛЬ
@dp.message(Command("profile"))
@dp.message(F.text == "👤 Мой профиль")
async def profile(message: Message):
    register_user(message.from_user)
    user = get_user(message.from_user.id)

    if user:
        traffic = user[4] / (1024 ** 3)
        registered = user[5][:10] if user[5] else "Неизвестно"

        await message.answer(
            "👤 VOLT IDENTITY\n\n"
            f"ID: {user[0]}\n"
            f"Тариф: {user[3]}\n"
            f"Использовано трафика: {traffic:.2f} ГБ\n"
            f"Дата регистрации: {registered}"
        )


# АДМИН-ПАНЕЛЬ
@dp.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    try:
        with get_db() as db:
            total = db.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            free_count = db.execute(
                "SELECT COUNT(*) FROM users WHERE tariff = 'FREE'"
            ).fetchone()[0]

            premium_count = db.execute(
                "SELECT COUNT(*) FROM users WHERE tariff = 'PREMIUM'"
            ).fetchone()[0]

            traffic = db.execute(
                "SELECT COALESCE(SUM(traffic_used_bytes), 0) FROM users"
            ).fetchone()[0]

        traffic_gb = traffic / (1024 ** 3)

        await message.answer(
            "⚡ VOLT CONTROL\n\n"
            "👑 Панель администратора\n\n"
            f"👥 Всего пользователей: {total}\n"
            f"⚡ FREE: {free_count}\n"
            f"👑 PREMIUM: {premium_count}\n\n"
            f"📊 Учтённый трафик: {traffic_gb:.2f} ГБ\n"
            "🗄 База данных: доступна"
        )

    except sqlite3.Error:
        await message.answer(
            "❌ Ошибка при обращении к базе данных."
        )
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ

@dp.message(Command("user"))
async def admin_user(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    parts = (message.text or "").split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /user TELEGRAM_ID")
        return

    user_id = int(parts[1])
    user = get_user(user_id)

    if not user:
        await message.answer("❌ Пользователь не найден.")
        return

    traffic = user[4] / (1024 ** 3)

    await message.answer(
        "👤 VOLT USER\n\n"
        f"ID: {user[0]}\n"
        f"Имя: {user[2] or 'Не указано'}\n"
        f"Username: @{user[1] or 'нет'}\n"
        f"Тариф: {user[3]}\n"
        f"Трафик: {traffic:.2f} ГБ\n"
        f"Регистрация: {user[5] or 'Неизвестно'}"
    )


@dp.message(Command("setpremium"))
async def set_premium(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    parts = (message.text or "").split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /setpremium TELEGRAM_ID")
        return

    user_id = int(parts[1])

    with get_db() as db:
        cursor = db.execute(
            """
            UPDATE users
            SET tariff = 'PREMIUM',
                subscription_until = NULL
            WHERE telegram_id = ?
            """,
            (user_id,)
        )

    if cursor.rowcount == 0:
        await message.answer("❌ Пользователь не найден.")
        return

    await message.answer(
        f"👑 Пользователь {user_id} переведён на PREMIUM.\n"
        "Срок подписки пока не установлен."
    )


@dp.message(Command("setfree"))
async def set_free(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    parts = (message.text or "").split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /setfree TELEGRAM_ID")
        return

    user_id = int(parts[1])

    with get_db() as db:
        cursor = db.execute(
            """
            UPDATE users
            SET tariff = 'FREE',
                subscription_until = NULL
            WHERE telegram_id = ?
            """,
            (user_id,)
        )

    if cursor.rowcount == 0:
        await message.answer("❌ Пользователь не найден.")
        return

    await message.answer(
        f"⚡ Пользователь {user_id} переведён на FREE."
    )
# ВЫДАЧА PREMIUM НА ОПРЕДЕЛЁННЫЙ СРОК

@dp.message(Command("grantpremium"))
async def grant_premium(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    parts = (message.text or "").split()

    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer(
            "Использование:\n"
            "/grantpremium TELEGRAM_ID ДНИ\n\n"
            "Пример:\n"
            "/grantpremium 8843062369 30"
        )
        return

    user_id = int(parts[1])
    days = int(parts[2])

    if days < 1 or days > 365:
        await message.answer("❌ Срок должен быть от 1 до 365 дней.")
        return

    user = get_user(user_id)

    if not user:
        await message.answer("❌ Пользователь не найден.")
        return

    now = datetime.now(timezone.utc)
    current_until = user[6]

    if user[3] == "PREMIUM" and current_until:
        try:
            old_until = datetime.fromisoformat(current_until)

            if old_until.tzinfo is None:
                old_until = old_until.replace(tzinfo=timezone.utc)

            if old_until > now:
                now = old_until
        except ValueError:
            pass

    expires = now + timedelta(days=days)
    expires_text = expires.isoformat(timespec="seconds")

    with get_db() as db:
        db.execute(
            """
            UPDATE users
            SET tariff = 'PREMIUM',
                subscription_until = ?
            WHERE telegram_id = ?
            """,
            (expires_text, user_id)
        )

    await message.answer(
        "👑 PREMIUM АКТИВИРОВАН\n\n"
        f"Пользователь: {user_id}\n"
        f"Добавлено дней: {days}\n"
        f"Действует до: {expires.strftime('%d.%m.%Y %H:%M UTC')}"
    )
# АВТОМАТИЧЕСКОЕ ИСТЕЧЕНИЕ PREMIUM

async def subscription_expiry_checker():
    while True:
        try:
            now = datetime.now(timezone.utc)

            with get_db() as db:
                users = db.execute(
                    """
                    SELECT telegram_id, subscription_until
                    FROM users
                    WHERE tariff = 'PREMIUM'
                    AND subscription_until IS NOT NULL
                    """
                ).fetchall()

            for user_id, subscription_until in users:
                try:
                    expires = datetime.fromisoformat(subscription_until)

                    if expires.tzinfo is None:
                        expires = expires.replace(tzinfo=timezone.utc)

                    if expires <= now:
                        with get_db() as db:
                            db.execute(
                                """
                                UPDATE users
                                SET tariff = 'FREE',
                                    subscription_until = NULL
                                WHERE telegram_id = ?
                                AND tariff = 'PREMIUM'
                                AND subscription_until = ?
                                """,
                                (user_id, subscription_until)
                            )

                        await bot.send_message(
                            user_id,
                            "⌛ Срок твоей PREMIUM-подписки VOLT VPN закончился.\n\n"
                            "Тариф изменён на FREE.\n"
                            "Чтобы вернуть PREMIUM, продли подписку."
                        )

                except Exception as error:
                    print(f"Ошибка обработки подписки {user_id}: {error}")

        except Exception as error:
            print(f"Ошибка проверки подписок: {error}")

        await asyncio.sleep(60)

# ПОДПИСКА
@dp.message(Command("subscription"))
async def subscription(message: Message):
    await premium(message)


# ПОДКЛЮЧЕНИЕ
@dp.message(Command("connect"))
@dp.message(F.text == "🔌 Подключение")
async def connect(message: Message):
    await message.answer(
        "🔌 VOLT CONNECTION\n\n"
        "Настройка VPN-подключения появится здесь."
    )


# ПОДДЕРЖКА
@dp.message(Command("support"))
@dp.message(F.text == "🆘 Поддержка")
async def support(message: Message):
    await message.answer(
        "🆘 VOLT SUPPORT\n\n"
        "Раздел технической поддержки скоро появится."
    )


# ЗАПУСК
async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
