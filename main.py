import os
import logging
import threading
import random
import io
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Flask to keep Render alive
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Gayatri Mehndi Bot - YouTube Autopilot is LIVE! 🎬"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# YouTube Titles
TITLES = [
    "Bridal Mehndi Design 2025 🔥 | Gayatri Mehndi Arts",
    "Beautiful Mehndi Design for Hands 💅 | Easy & Simple",
    "Latest Bridal Mehndi Design 😍 | Full Hand Tutorial",
    "New Mehndi Design 2025 ✨ | Gayatri Mehndi Arts Pune",
    "Stylish Mehndi Design for Festival 🎉 | Step by Step"
]

def create_youtube_thumbnail(input_img):
    # Create 1280x720 thumbnail
    thumb_w, thumb_h = 1280, 720
    # Resize and crop image
    img = input_img.convert("RGB")
    img_ratio = img.width / img.height
    thumb_ratio = thumb_w / thumb_h
    if img_ratio > thumb_ratio:
        # crop width
        new_h = thumb_h
        new_w = int(new_h * img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - thumb_w) // 2
        img = img.crop((left, 0, left+thumb_w, thumb_h))
    else:
        new_w = thumb_w
        new_h = int(new_w / img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - thumb_h) // 2
        img = img.crop((0, top, thumb_w, top+thumb_h))

    # Dark gradient overlay at bottom for text
    overlay = Image.new('RGBA', (thumb_w, thumb_h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    for y in range(thumb_h//2, thumb_h):
        alpha = int((y - thumb_h//2) / (thumb_h//2) * 180)
        draw.line([(0,y),(thumb_w,y)], fill=(0,0,0,alpha))
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    # Add text
    draw = ImageDraw.Draw(img)
    try:
        # Try to use bold font if available
        font_big = ImageFont.truetype("arial.ttf", 70)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Text with stroke
    draw.text((50, 500), "BRIDAL MEHNDI", fill=(255,215,0), font=font_big, stroke_width=4, stroke_fill=(0,0,0))
    draw.text((50, 580), "Design 2025 ✨", fill=(255,255,255), font=font_big, stroke_width=3, stroke_fill=(0,0,0))
    draw.text((50, 660), "Gayatri Mehndi Arts | Pune", fill=(255,255,255), font=font_small, stroke_width=2, stroke_fill=(0,0,0))
    
    return img

def get_youtube_pack():
    title = random.choice(TITLES)
    description = f"""{title}

🙏 Welcome to Gayatri Mehndi Arts - Pune's Best Mehndi Artist!

In this video, I am showing {title.lower()}.

📌 Book Your Bridal Mehndi:
📞 Call/WhatsApp: +91 9XXXXXXXXX
📍 Pune, Maharashtra

👍 LIKE | SHARE | SUBSCRIBE for more designs!

#mehndi #mehndidesign #bridalmehndi #henna #GayatriMehndiArts #Pune #mehndidesign2025 #newmehndi #simplemehndi #festivalmehndi

Thanks for watching!
Gayatri Mehndi Arts
"""
    tags = "mehndi design, bridal mehndi, mehndi design 2025, simple mehndi, gayatri mehndi arts, pune mehndi, henna design, new mehndi design, festival mehndi, easy mehndi"
    return title, description, tags

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Namaste! Welcome to Gayatri Mehndi Arts - YouTube Autopilot Bot!\n\n"
        "📸 Send me any mehndi photo and I will create:\n"
        "1. YouTube Thumbnail (1280x720)\n"
        "2. Viral Title\n"
        "3. Description + Hashtags\n"
        "4. Tags\n\n"
        "Just send a photo now! 💅\n\n"
        "/start - Start\n/help - Help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Send 1 mehndi photo → Get full YouTube pack ready to upload!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Creating YouTube pack... Please wait 5 sec...")
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        img = Image.open(io.BytesIO(photo_bytes))

        # 1. Create thumbnail
        thumb = create_youtube_thumbnail(img)
        bio = io.BytesIO()
        bio.name = 'youtube_thumbnail.jpg'
        thumb.save(bio, 'JPEG', quality=95)
        bio.seek(0)

        # 2. Get titles/desc/tags
        title, desc, tags = get_youtube_pack()

        # Send thumbnail
        await update.message.reply_photo(photo=bio, caption=f"✅ YouTube Thumbnail Ready! (1280x720)")

        # Send YouTube pack
        pack_text = f"🎬 **YOUTUBE PACK READY** 🎬\n\n**📌 TITLE (copy one):**\n{title}\n\n**📝 DESCRIPTION:**\n{desc}\n\n**🏷️ TAGS (copy-paste in YouTube tags box):**\n{tags}\n\n✅ Just upload thumbnail + copy title/description! Ready to go viral!"
        
        await update.message.reply_text(pack_text)

    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"Error: {e}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    if not BOT_TOKEN:
        logger.error("TOKEN not set!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("YouTube Autopilot Bot starting... @Gayatri Mehndi Arts")
    app.run_polling()

if __name__ == '__main__':
    main()
