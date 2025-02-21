from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import os
import json
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN = os.getenv("BOT_TOKEN", "7680394855:AAFVjKErGVwWg9bZ49BnChVgCLnv1xA3MRw")
PERSONAL_CHAT_ID = "1799744741"  # Your Telegram user ID
WEB_APP_URL = "https://katie2090.github.io/TelegramBot/form.html"  # Hosted Web Form

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and displays menu options."""
    menu_buttons = [
        ["✈ 落地接机", "🔖 证照办理"],
        ["🏤 房产凭租", "🏩 酒店预订"],
        ["📋 填写信息", "🔔 后勤生活信息频道"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text("欢迎使用亚太·亚通机器人！请选择一个选项：", reply_markup=reply_markup)

# Handle Menu Selection
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles menu selection and displays an inline 'Fill Out' button."""
    user_input = update.message.text

    response_data = {
        "✈ 落地接机": {
            "photo": "images/接机.jpg",
            "caption": "🌟 欢迎加入【后勤接机】群 🌟\n\n✅ 请核对信息，如有更改，请联系客服！",
            "buttons": [["🧑🏻‍💻 在线客服", "https://t.me/HQBGSKF"], ["✈ 接机频道", "https://t.me/+pqM959ERihBkYTc9"]]
        },
        "🔖 证照办理": {
            "photo": "images/passport.jpg",
            "caption": "📋 证照办理服务：\n\n✔️ 提供快速办理签证、护照及其他相关证件的服务。\n📞 点击客服咨询更多详情。",
            "buttons": [["🧑🏻‍💻 在线客服", "https://t.me/HQBGSKF"], ["🔖 证件办理频道", "https://t.me/+sINSVji28vM4ZDJl"]]
        },
        "🏤 房产凭租": {
            "photo": "images/resized-image.jpg",
            "caption": "🏤 房产租赁信息：\n\n✔️ 提供房产出租和购房服务，涵盖各类房型。\n🔍 点击下方按钮了解更多。",
            "buttons": [["🧑🏻‍💻 在线客服", "https://t.me/HQBGSKF"], ["🏤 房产信息频道", "https://t.me/+8i7xQLV_UiY2NTY1"]]
        },
        "🏩 酒店预订": {
            "photo": "images/sofietel.jpg",
            "caption": "🏨高端酒店预订代办服务| 索菲特 & 瑰丽酒店 |🏨\n\n✨ 奢华体验，优惠价格，预订更省心！ ✨\n\n📞 联系我们，轻松享受高端住宿！",
            "buttons": [["🧑🏻‍💻 在线客服", "https://t.me/HQBGSKF"], ["🏩 酒店详情频道", "https://t.me/+M5Q_hf4xyG00YzRl"]]
        },
        "📋 填写信息": {
            "buttons": [["填写表单", WebAppInfo(url=https://t.me/MyAppLogisticBot/tg_Logistic)]]
        },
        "🔔 后勤生活信息频道": {
            "photo": "images/logistic.png",
            "caption": "📌 主要提供各种后勤管理和生活服务，确保用户能够方便、高效地获取信息和帮助。",
            "buttons": [["🔔 详细了解", "https://t.me/+QQ56RVTKshQxMDU1"]]
        }
    }

    if user_input in response_data:
        data = response_data[user_input]
        inline_keyboard = [[InlineKeyboardButton(text, web_app=url) if isinstance(url, WebAppInfo) else InlineKeyboardButton(text, url=url)] for text, url in data.get("buttons", [])]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        
        if "photo" in data:
            await update.message.reply_photo(photo=open(data["photo"], "rb"), caption=data["caption"], reply_markup=reply_markup)
        else:
            await update.message.reply_text("请点击下面的按钮打开表单并提交您的信息:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("请从菜单中选择一个选项。")

# Handle Web App Data Submission
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles data submission from Web App form."""
    if update.effective_message.web_app_data:
        try:
            # Extract data from Web App submission
            data = json.loads(update.effective_message.web_app_data.data)

            # Ensure data contains necessary fields
            date = data.get('date', '未提供')
            name = data.get('name', '未提供')
            rooms = data.get('rooms', '未提供')
            telephone = data.get('telephone', '未提供')

            # Construct the message
            message = (
                f"📋 **新提交信息**\n"
                f"📅 日期: {date}\n"
                f"👤 姓名: {name}\n"
                f"🛏️ 房间数: {rooms}\n"
                f"📞 电话: {telephone}\n"
            )

            # ✅ Send the message to your personal Telegram ID
            await context.bot.send_message(chat_id=PERSONAL_CHAT_ID, text=message, parse_mode="Markdown")

            # ✅ Notify the user that submission was successful
            await update.effective_message.reply_text("✅ 您的信息已成功提交！")

        except Exception as e:
            logging.error(f"Error processing Web App data: {e}")
            await update.effective_message.reply_text("❌ 数据提交失败，请稍后重试。")


# Main function
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    application.run_polling()

if __name__ == "__main__":
    main()
