import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
API_TOKEN = os.getenv("8744542602:AAEaqLkNAYLNtclYfKsXpcXytxYXt8GwYoo")
ADMIN_ID = int(os.getenv("5663190082", "0"))

# Проверка токена
if not API_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в .env файле!")

# Инициализация
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для FSM
class FeedbackStates(StatesGroup):
    waiting_for_message = State()
    confirming_send = State()

# Клавиатуры
feedback_button = InlineKeyboardButton("Связь", callback_data="feedback")
feedback_kb = InlineKeyboardMarkup().add(feedback_button)

send_button = InlineKeyboardButton("Отправь", callback_data="send")
send_kb = InlineKeyboardMarkup().add(send_button)

cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel")
cancel_kb = InlineKeyboardMarkup().add(cancel_button)

# Хранение сообщений пользователей
user_messages = {}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Команда /start"""
    await message.answer(
        "Привет! Это бот обратной связи. Нажми кнопку ниже, чтобы отправить сообщение.",
        reply_markup=feedback_kb
    )

@dp.callback_query_handler(lambda c: c.data == 'feedback')
async def feedback_callback(call: types.CallbackQuery):
    """Обработчик кнопки 'Связь'"""
    await call.message.answer(
        "Напишите ваше сообщение (предложения, баги, фризы и прочее). "
        "Сообщения не по теме будут проигнорированы.",
        reply_markup=cancel_kb
    )
    await FeedbackStates.waiting_for_message.set()
    await call.answer()

@dp.message_handler(state=FeedbackStates.waiting_for_message)
async def collect_message(message: types.Message, state: FSMContext):
    """Сбор сообщения от пользователя"""
    user_messages[message.from_user.id] = message.text
    await message.answer(
        "Отправить?",
        reply_markup=send_kb
    )
    await FeedbackStates.confirming_send.set()

@dp.callback_query_handler(lambda c: c.data == 'send', state=FeedbackStates.confirming_send)
async def send_callback(call: types.CallbackQuery, state: FSMContext):
    """Отправка сообщения админу"""
    msg = user_messages.get(call.from_user.id)
    if msg:
        try:
            # Отправка сообщения админу по ID
            await bot.send_message(
                ADMIN_ID,
                f"📨 <b>Новое сообщение обратной связи</b>\n\n"
                f"<b>От:</b> {call.from_user.full_name} (@{call.from_user.username or 'без юзернейма'})\n"
                f"<b>ID:</b> {call.from_user.id}\n\n"
                f"<b>Сообщение:</b>\n{msg}",
                parse_mode=types.ParseMode.HTML
            )
            await call.message.answer("✅ Сообщение отправлено! Спасибо за отзыв!")
            user_messages.pop(call.from_user.id, None)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            await call.message.answer("❌ Ошибка при отправке. Проверьте конфигурацию.")
    else:
        await call.message.answer("❌ Нет сообщения для отправки.")
    
    await state.finish()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'cancel', state=FeedbackStates.waiting_for_message)
async def cancel_callback(call: types.CallbackQuery, state: FSMContext):
    """Отмена"""
    await call.message.answer("Отменено.")
    user_messages.pop(call.from_user.id, None)
    await state.finish()
    await call.answer()

if __name__ == "__main__":
    logger.info("🤖 Бот запущен!")
    executor.start_polling(dp, skip_updates=True)
