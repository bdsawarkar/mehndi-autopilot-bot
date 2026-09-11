import os
import logging
import threading
import io
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Mehndi by Gayatri - SMART YouTube Bot LIVE! 🎬"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

ASK_TYPE, ASK_FORMAT = range(2)
user_data = {}
CHANNEL_NAME = "Mehndi by Gayatri"

def create_thumbnail_smart(img, mehndi_type, is_short):
    if is_short:
        W, H = 1080, 1920
    else:
        W, H = 1280, 720

    original = img.convert("RGB")
    bg_temp = original.copy().resize((W, H), Image.LANCZOS)
    bg_temp = bg_temp.filter(ImageFilter.GaussianBlur(radius=30))
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    bg = Image.blend(dark, bg_temp, 0.5)

    img_ratio = original.width / original.height
    max_w = W - 80
    max_h = H - 260

    if img_ratio > max_w / max_h:
        new_w = max_w
        new_h = int(new_w / img_ratio)
    else:
        new_h = max_h
        new_w = int(new_h * img_ratio)

    fitted = original.resize((new_w, new_h), Image.LANCZOS)
    x_offset = (W - new_w) // 2
    y_offset = (H - new_h) // 2 - 50
    if y_offset < 20:
        y_offset = 20

    bg.paste(fitted, (x_offset, y_offset))

    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    grad_start = H - 180
    for y in range(grad_start, H):
        alpha = int((y - grad_start) / 180 * 210)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))

    final = Image.alpha_composite(bg.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(final)

    try:
        font_big = ImageFont.truetype("arial.ttf", 70 if not is_short else 75)
        font_mid = ImageFont.truetype("arial.ttf", 38)
    except:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()

    draw.rectangle([x_offset-4, y_offset-4, x_offset+new_w+4, y_offset+new_h+4], outline=(255, 215, 0), width=4)

    text1 = mehndi_type.upper()
    draw.text((42, H-142), f"{text1} MEHNDI", fill=(0,0,0), font=font_big, stroke_width=6, stroke_fill=(0,0,0))
    draw.text((40, H-140), f"{text1} MEHNDI", fill=(255, 215, 0), font=font_big, stroke_width=5, stroke_fill=(0,0,0))
    
    draw.text((42, H-57), f"{CHANNEL_NAME} | Pune", fill=(0,0,0), font=font_mid, stroke_width=3, stroke_fill=(0,0,0))
    draw.text((40, H-55), f"{CHANNEL_NAME} | Pune", fill=(255, 255, 255), font=font_mid, stroke_width=2, stroke_fill=(0,0,0))

    return final

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎬 Namaste! {CHANNEL_NAME} - SMART YouTube Bot!\n\n"
        f"📸 Send any mehndi photo → I will ASK:\n"
        f"1. Which type of mehndi?\n"
        f"2. Short or Long video?\n\n"
        f"Then create perfect thumbnail with FULL mehndi (no cut!) + YouTube Pack!\n\n"
        f"Just send a photo now! 💅",
        reply_markup=ReplyKeyboardRemove()
    )

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    photo_bytes = await file.download_as_bytearray()
    user_id = update.effective_user.id
    user_data[user_id] = {"photo": photo_bytes}

    keyboard = [
        ["Bridal", "Arabic"],
        ["Simple", "Festival"],
        ["Shiv-Parvati", "Portrait"],
        ["Leg Mehndi", "Kids"],
        ["Dulha-Dulhan", "God Mehndi"]
    ]
    await update.message.reply_text(
        "📸 Photo received! Full mehndi safe ✅\n\n**Which type of mehndi is this?**",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_TYPE

async def type_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mehndi_type = update.message.text
    user_data[user_id]["type"] = mehndi_type

    keyboard = [["📱 Short Video (Shorts 9:16)", "🎥 Long Video (16:9)"]]
    await update.message.reply_text(
        f"Great! **{mehndi_type}** 👍\n\n**Short or Long video?**",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_FORMAT

async def format_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_short = "Short" in update.message.text
    mehndi_type = user_data[user_id].get("type", "Bridal")
    photo_bytes = user_data[user_id]["photo"]

    await update.message.reply_text(
        f"🎬 Creating {mehndi_type} thumbnail for {CHANNEL_NAME}...\n"
        f"{'📱 Shorts 9:16' if is_short else '🎥 Long 16:9'} | NO-CROP ✅",
        reply_markup=ReplyKeyboardRemove()
    )

    try:
        img = Image.open(io.BytesIO(photo_bytes))
        thumb = create_thumbnail_smart(img, mehndi_type, is_short)

        bio = io.BytesIO()
        bio.name = 'thumbnail.jpg'
        thumb.save(bio, 'JPEG', quality=95)
        bio.seek(0)

        await update.message.reply_photo(
            photo=bio, 
            caption=f"✅ {mehndi_type} - {'SHORTS' if is_short else 'LONG'} Ready!\nFull design visible ✅\nChannel: {CHANNEL_NAME}"
        )

        if is_short:
            title = f"{mehndi_type} Mehndi Design 2025 🔥 | #Shorts | {CHANNEL_NAME}"
        else:
            title = f"{mehndi_type} Mehndi Design 2025 😍 | Full Tutorial | {CHANNEL_NAME}"

        description = f"""{title}

🙏 Welcome to {CHANNEL_NAME}!

Design Type: {mehndi_type} Mehndi
Video: {'YouTube Shorts' if is_short else 'Full Video'}
Channel: {CHANNEL_NAME}

📌 Book Bridal Mehndi - Pune
👍 LIKE | SHARE | SUBSCRIBE

#{mehndi_type.replace(' ','')} #Mehndi #Henna #MehndiByGayatri #Pune #2025

{CHANNEL_NAME}
"""

        tags = f"{mehndi_type.lower()} mehndi, mehndi by gayatri, gayatri mehndi pune, bridal mehndi, {mehndi_type.lower()} design, henna 2025"

        await update.message.reply_text(
            f"🎬 **{CHANNEL_NAME} - {mehndi_type.upper()} PACK**\n\n"
            f"📐 {'📱 SHORTS' if is_short else '🎥 LONG'}\n\n"
            f"📌 TITLE:\n{title}\n\n"
            f"📝 DESCRIPTION:\n{description}\n\n"
            f"🏷️ TAGS:\n{tags}"
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"Error: {e}")

    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    if not BOT_TOKEN:
        logger.error("TOKEN not set!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, photo_received)],
        states={
            ASK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_received)],
            ASK_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, format_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    logger.info(f"{CHANNEL_NAME} Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
