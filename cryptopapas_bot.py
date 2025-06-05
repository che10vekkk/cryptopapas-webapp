
import sqlite3
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import LabeledPrice, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging

# --- Конфигурация ---
BOT_TOKEN = "8025168995:AAGZICDPEg9MdLTcqRAujgkcIJt813WiyqQ"
VIP_CHAT_USERNAME = "CryptoPapasAppBot"
WEBAPP_URL = "https://cryptopapasito-bot.onrender.com"
PRICE = LabeledPrice(label="VIP-доступ", amount=75000)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- База данных ---
conn = sqlite3.connect("database.sqlite")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER,
    stars_earned INTEGER DEFAULT 0
)
""")
conn.commit()

# --- Клавиатура с WebApp ---
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL)))

# --- Команда старт ---
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    referrer_id = None
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except ValueError:
            pass

    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, referrer_id))
    conn.commit()

    await message.answer("Добро пожаловать в CryptoPapa’s App!\n\nНажмите кнопку ниже, чтобы открыть приложение👇", reply_markup=keyboard)

# --- Команда купить VIP ---
@dp.message_handler(commands=['buy'])
async def buy(message: types.Message):
    await bot.send_invoice(
        message.chat.id,
        title="Покупка VIP-доступа",
        description="Доступ в VIP-чат CryptoPapa’s за 750 Stars",
        provider_token="STARS_PROVIDER_TOKEN",
        currency="XTR",
        prices=[PRICE],
        start_parameter="buy-vip",
        payload="vip-access"
    )

@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    user_id = message.from_user.id
    invite_link = f"https://t.me/{VIP_CHAT_USERNAME}"
    await message.answer(f"✅ Оплата прошла успешно! Вот ваша ссылка для входа в VIP-чат:\n{invite_link}")

    cursor.execute("SELECT referrer_id FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        referrer_id = result[0]
        reward = 750 * 5 // 100
        cursor.execute("UPDATE users SET stars_earned = stars_earned + ? WHERE user_id=?", (reward, referrer_id))
        conn.commit()
        try:
            await bot.send_message(referrer_id, f"🎉 По вашей ссылке оформлена покупка! Вы заработали {reward} Stars.")
        except:
            pass

# --- Команда Баланс ---
@dp.message_handler(commands=['balance'])
async def balance(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT stars_earned FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    earned = result[0] if result else 0
    await message.answer(f"💰 Вы заработали {earned} Stars по партнёрской программе.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
