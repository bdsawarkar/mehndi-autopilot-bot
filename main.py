import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# --- Mini website to keep Render alive ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Gayatri Mehndi Bot is LIVE! 💅 Bot is running 24/7 on Render"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# --- Telegram Bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Namaste! Welcome to Gayatri Mehndi Arts Autopilot Bot 💅\n\nSend me any mehndi photo and I will add your watermark!\n\n/start - Start\n/help - Help\n/about - About")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send me a photo: I will add 'Gayatri Mehndi Arts' watermark and send back ready to post!")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gayatri Mehndi Arts | Pune | Bot on Render.com")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Processing...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size
        text = "Gayatri Mehndi Arts"
        try:
            font = ImageFont.truetype("arial.ttf", size=int(w*0.05))
        except:
            font = ImageFont.load_default()
        draw.text((w*0.05, h*0.92), text, fill=(255, 0, 100), font=font, stroke_width=2, stroke_fill=(255,255,255))
        bio = io.BytesIO()
        bio.name = 'mehndi_ready.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        await update.message.reply_photo(photo=bio, caption="✅ Ready! Watermark added 💅")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"Error: {e}")

def main():
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("Bot is starting... @Gayatri Mehndi Arts")
    app.run_polling()

if __name__ == '__main__':
    main()
