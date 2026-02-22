import telebot
import os

TOKEN = os.getenv("8508131290:AAEldOb6MV6SR6kEbdVPdUTg27pCP22TC-A")
bot = telebot.TeleBot(8508131290:AAEldOb6MV6SR6kEbdVPdUTg27pCP22TC-A)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот работает 🚀")

    bot.infinity_polling() 