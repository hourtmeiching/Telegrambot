import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Firebase credentials from environment variable
firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")
if firebase_credentials:
    cred_dict = json.loads(firebase_credentials)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    logger.error("❌ FIREBASE_CREDENTIALS environment variable not set.")

# Collection name in Firestore
USER_COLLECTION = "telegram_users"
MESSAGE_COLLECTION = "sent_messages"


# Store user chat IDs in Firestore
def save_user_chat_id(chat_id):
    doc_ref = db.collection(USER_COLLECTION).document(str(chat_id))
    doc_ref.set({"chat_id": chat_id})


# Load all user chat IDs from Firestore
def load_user_chat_ids():
    users = db.collection(USER_COLLECTION).stream()
    return [user.id for user in users]


# Store message ID in Firestore (for editing messages later)
def save_message_id(chat_id, message_id):
    db.collection(MESSAGE_COLLECTION).document(str(chat_id)).set({"message_id": message_id})


# Get stored message ID (for editing)
def get_message_id(chat_id):
    doc = db.collection(MESSAGE_COLLECTION).document(str(chat_id)).get()
    return doc.to_dict().get("message_id") if doc.exists else None


# /start command - Registers users and displays menu buttons
async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    save_user_chat_id(chat_id)

    keyboard = [
        [KeyboardButton("✈ 落地接机"), KeyboardButton("🔖 证照办理")],
        [KeyboardButton("🏤 房产租赁"), KeyboardButton("🏩 酒店预订")],
        [KeyboardButton("🍽️ 食堂信息"), KeyboardButton("📦 生活物资")],
        [KeyboardButton("🔔 后勤生活信息频道")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text("✅ 你已成功注册，可接收最新公告！\n请选择一个服务：", reply_markup=reply_markup)


# /broadcast command - Sends messages, images, and buttons to all users
async def broadcast(update: Update, context: CallbackContext) -> None:
    user_chat_ids = load_user_chat_ids()
    if not user_chat_ids:
        await update.message.reply_text("❌ 没有注册用户，无法发送公告。")
        return

    message_text = update.message.text.split("\n")
    if message_text[0].startswith("/broadcast"):
        message_text.pop(0)  # Remove the first line

    if len(message_text) < 2:
        await update.message.reply_text("⚠️ 请输入公告内容格式:\n\n"
                                        "<b>标题 (加粗)</b>\n"
                                        "主要内容\n"
                                        "(可选) 图片URL 或 图片文件名\n"
                                        "(可选) 按钮格式: `按钮文本|链接`",
                                        parse_mode="HTML")
        return

    # Extract title, body text, images, and buttons
    title = f"{message_text[0]}\n\n" if message_text[0] else ""
    body_text = []
    images = []
    buttons = []

    for line in message_text[1:]:
        line = line.strip()
        if line.startswith("http") and (".jpg" in line or ".png" in line):
            images.append(line)
        elif "|" in line:
            button_row = [InlineKeyboardButton(*btn.strip().split("|", 1)) for btn in line.split(",")]
            buttons.append(button_row)
        else:
            body_text.append(line)

    message_content = title + "\n".join(body_text)
    inline_markup = InlineKeyboardMarkup(buttons) if buttons else None

    success_count, failure_count = 0, 0
    for chat_id in user_chat_ids:
        try:
            if images:
                sent_media = await context.bot.send_photo(chat_id=chat_id, photo=images[0], caption=message_content, reply_markup=inline_markup, parse_mode="HTML")
                save_message_id(chat_id, sent_media.message_id)
            else:
                sent_message = await context.bot.send_message(chat_id=chat_id, text=message_content, reply_markup=inline_markup, parse_mode="HTML")
                save_message_id(chat_id, sent_message.message_id)

            success_count += 1
        except Exception as e:
            logger.error(f"❌ 发送失败给 {chat_id}: {e}")
            failure_count += 1

    await update.message.reply_text(f"✅ 公告已发送！成功: {success_count}，失败: {failure_count}")


# /edit command - Updates a previously sent message
async def edit_message(update: Update, context: CallbackContext) -> None:
    user_chat_ids = load_user_chat_ids()
    if not user_chat_ids:
        await update.message.reply_text("❌ 没有注册用户，无法编辑公告。")
        return

    message_text = update.message.text.split("\n")
    if message_text[0].startswith("/edit"):
        message_text.pop(0)

    if len(message_text) < 2:
        await update.message.reply_text("⚠️ 请输入公告内容格式:\n\n"
                                        "<b>标题 (加粗)</b>\n"
                                        "修改后的内容\n"
                                        "(可选) 新的图片URL 或 图片文件名\n"
                                        "(可选) 按钮格式: `按钮文本|链接`",
                                        parse_mode="HTML")
        return

    title = f"{message_text[0]}\n\n" if message_text[0] else ""
    body_text = "\n".join(message_text[1:])
    new_message = title + body_text

    success_count, failure_count = 0, 0
    for chat_id in user_chat_ids:
        try:
            message_id = get_message_id(chat_id)
            if message_id:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=new_message, parse_mode="HTML")
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            logger.error(f"❌ 更新失败给 {chat_id}: {e}")
            failure_count += 1

    await update.message.reply_text(f"✅ 公告已更新！成功: {success_count}，失败: {failure_count}")


# Main function
def main():
    token = os.getenv("7100869336:AAH1khQ33dYv4YElbdm8EmYfARMNkewHlKs")  # Use environment variable for security

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("edit", edit_message))

    logger.info("🚀 机器人已启动...")
    application.run_polling()


if __name__ == "__main__":
    main()
