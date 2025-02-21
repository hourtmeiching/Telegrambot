import os
import logging
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

# Flask app for webhook
app = Flask(__name__)

# Telegram Bot Handlers
async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    keyboard = [
        [KeyboardButton("📋 Fill Form", web_app=WebAppInfo(url="https://hourtmeiching.github.io/Telegrambot/form.html"))],
        [KeyboardButton("ℹ️ Info"), KeyboardButton("🔔 Announcements")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)

async def info(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("ℹ️ This is a Telegram bot with a web form.")

# Telegram Application Setup
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Text("ℹ️ Info"), info))

# Webhook setup
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return "OK", 200

# Run Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
