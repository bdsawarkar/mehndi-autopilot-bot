import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token from Render Environment Variable
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "") # optional

# --- Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 Namaste! Welcome to Gayatri Mehndi Arts Autopilot Bot 💅\n\n"
        "Send me any mehndi photo and I will add your watermark + make it ready for YouTube Shorts/Instagram!\n\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/help - Help\n"
        "/about - About us"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Just send me a photo:\n"
        "1. I will add 'Gayatri Mehndi Arts' watermark\n"
        "2. Resize for Shorts (9:16)\n"
        "3. Send back ready to post!\n\n"
        "For video support, send video as file."
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gayatri Mehndi Arts | Professional Mehndi Artist | Pune\nManaged by Bhushan Sawarkar - Autopilot Bot on Render.com")

# --- Photo Handler (Main Feature) ---

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Processing your mehndi design... please wait 5 sec")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Open with Pillow
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        
        # Add watermark text
        draw = ImageDraw.Draw(img)
        w, h = img.size
        text = "Gayatri Mehndi Arts"
        # Try to use default font
        try:
            font = ImageFont.truetype("arial.ttf", size=int(w*0.05))
        except:
            font = ImageFont.load_default()
        
        # Position bottom center
        draw.text((w*0.05, h*0.92), text, fill=(255, 0, 100), font=font, stroke_width=2, stroke_fill=(255,255,255))
        
        # Save to bytes
        bio = io.BytesIO()
        bio.name = 'mehndi_ready.jpg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        
        await update.message.reply_photo(photo=bio, caption="✅ Ready! Watermark added.\nPost this on YouTube Shorts / Insta Reels 💅")
        
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set! Add in Render Environment Variables")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Optional: Handle PORT for Render Web Service (keeps alive)
    # Render expects a web server, but polling works fine for free tier
    logger.info("Bot is starting... @Gayatri Mehndi Arts")
    app.run_polling()

if __name__ == '__main__':
    main()
