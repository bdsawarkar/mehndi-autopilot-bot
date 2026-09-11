import os
import logging
import threading
import io
import random
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# --- Flask to keep Render alive ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Gayatri Mehndi - SMART YouTube Bot LIVE! 🎬 No-Crop Thumbnails"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# --- Conversation States ---
ASK_TYPE, ASK_FORMAT = range(2)
user_data = {}

# --- SMART THUMBNAIL - NO CROP, KEEP FULL MEHNDI ---
def create_thumbnail_smart(img, mehndi_type, is_short):
    # Canvas size
    if is_short:
        W, H = 1080, 1920  # YouTube Shorts 9:16
    else:
        W, H = 1280, 720   # YouTube Long 16:9

    original = img.convert("RGB")

    # 1. Create BLURRED background that fills full canvas (no black bars)
    bg_temp = original.copy().resize((W, H), Image.LANCZOS)
    bg_temp = bg_temp.filter(ImageFilter.GaussianBlur(radius=30))
    # Darken blurred bg for contrast
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    bg = Image.blend(dark, bg_temp, 0.5)

    # 2. FIT original inside canvas - NO CROP! (Contain logic)
    img_ratio = original.width / original.height
    canvas_ratio = W / H

    # Leave margins: 80px sides, 250px bottom for text
    max_w = W - 80
    max_h = H - 260

    if img_ratio > max_w / max_h:
        new_w = max_w
        new_h = int(new_w / img_ratio)
    else:
        new_h = max_h
        new_w = int(new_h * img_ratio)

    # Ensure minimum size
    if new_w < 200:
        new_w = 200
        new_h = int(new_w / img_ratio)
    if new_h < 200:
        new_h = 200
        new_w = int(new_h * img_ratio)

    fitted = original.resize((new_w, new_h), Image.LANCZOS)

    # 3. Paste fitted image CENTERED (slightly up to leave text space)
    x_offset = (W - new_w) // 2
    y_offset = (H - new_h) // 2 - 50
    if y_offset < 20:
        y_offset = 20

    bg.paste(fitted, (x_offset, y_offset))

    # 4. Add gradient only at bottom for text readability (not over mehndi)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    grad_start = H - 180
    for y in range(grad_start, H):
        alpha = int((y - grad_start) / 180 * 210)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))

    final = Image.alpha_composite(bg.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(final)

    # 5. Fonts
    try:
        font_big = ImageFont.truetype("arial.ttf", 70 if not is_short else 75)
        font_mid = ImageFont.truetype("arial.ttf", 38)
    except:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()

    # 6. Gold border around fitted mehndi to highlight (proves no crop)
    border_color = (255, 215, 0)  # Gold
    draw.rectangle([x_offset-4, y_offset-4, x_offset+new_w+4, y_offset+new_h+4], outline=border_color, width=4)

    # 7. Text at bottom - NEVER over center mehndi
    text1 = mehndi_type.upper()
    # Shadow + gold
    draw.text((42, H-142), f"{text1} MEHNDI", fill=(0,0,0), font=font_big, stroke_width=6, stroke_fill=(0,0,0))
    draw.text((40, H-140), f"{text1} MEHNDI", fill=(255, 215, 0), font=font_big, stroke_width=5, stroke_fill=(0,0,0))
    
    draw.text((42, H-57), "Gayatri Mehndi Arts | Pune", fill=(0,0,0), font=font_mid, stroke_width=3, stroke_fill=(0,0,0))
    draw.text((40, H-55), "Gayatri Mehndi Arts | Pune", fill=(255, 255, 255), font=font_mid, stroke_width=2, stroke_fill=(0,0,0))

    return final

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Namaste! Gayatri Mehndi - SMART YouTube Bot!\n\n"
        "📸 Send any mehndi photo → I will ASK:\n"
        "1. Which type of mehndi?\n"
        "2. Short or Long video?\n\n"
        "Then I create PERFECT thumbnail with FULL mehndi (no cut!) + YouTube Pack!\n\n"
        "Just send a photo now! 💅",
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
        "📸 Photo received! No crop will happen 👍\n\n**Which type of mehndi is this?**\nTap a button below:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_TYPE

async def type_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mehndi_type = update.message.text
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["type"] = mehndi_type

    keyboard = [["📱 Short Video (YouTube Shorts 9:16)", "🎥 Long Video (YouTube Video 16:9)"]]
    await update.message.reply_text(
        f"Great! **{mehndi_type} Mehndi** selected 👍\n\n"
        f"Now: Is this for **Short or Long video?**\n\n"
        f"📱 Short = Vertical thumbnail (1080x1920) for Shorts/Reels\n"
        f"🎥 Long = Horizontal thumbnail (1280x720) for YouTube Video\n"
        f"\nTap one:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ASK_FORMAT

async def format_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    is_short = "Short" in text
    
    if user_id not in user_data or "photo" not in user_data[user_id]:
        await update.message.reply_text("Please send photo again.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    mehndi_type = user_data[user_id].get("type", "Bridal")
    photo_bytes = user_data[user_id]["photo"]

    await update.message.reply_text(
        f"🎬 Creating {mehndi_type} thumbnail...\n"
        f"Format: {'Shorts 9:16' if is_short else 'Long 16:9'}\n"
        f"Mode: NO-CROP (full mehndi safe) ✅\n"
        f"Please wait 5 sec...",
        reply_markup=ReplyKeyboardRemove()
    )

    try:
        img = Image.open(io.BytesIO(photo_bytes))
        thumb = create_thumbnail_smart(img, mehndi_type, is_short)

        bio = io.BytesIO()
        bio.name = 'youtube_thumbnail.jpg'
        thumb.save(bio, 'JPEG', quality=95)
        bio.seek(0)

        await update.message.reply_photo(
            photo=bio, 
            caption=f"✅ {mehndi_type} - {'SHORTS (9:16)' if is_short else 'LONG VIDEO (16:9)'} Thumbnail Ready!\nFull mehndi visible - No cut! 👍"
        )

        # YouTube pack based on type
        if is_short:
            title = f"{mehndi_type} Mehndi Design 2025 🔥 | #{mehndi_type.replace(' ','')} #Shorts | Gayatri Mehndi Arts"
        else:
            title = f"{mehndi_type} Mehndi Design 2025 Full Tutorial 😍 | Bridal Mehndi | Gayatri Mehndi Arts Pune"

        description = f"""{title}

🙏 Welcome to Gayatri Mehndi Arts - Pune's Best Mehndi Artist!

In this video: {mehndi_type} Mehndi Design

✨ Type: {mehndi_type}
🎬 Video Type: {'YouTube Shorts (60 sec vertical)' if is_short else 'Full Length YouTube Video (Horizontal)'}
🎨 Thumbnail: Full design visible - No crop

📌 Book Your Bridal Mehndi:
📍 Pune, Maharashtra
📞 WhatsApp for Booking

👍 LIKE | SHARE | SUBSCRIBE for daily new designs!

#{mehndi_type.replace(' ', '')}Mehndi #MehndiDesign #BridalMehndi #HennaArt #GayatriMehndiArts #PuneMehndi #2025 #Shorts #Viral

Thanks for watching!
Gayatri Mehndi Arts
"""
        tags = f"{mehndi_type.lower()} mehndi design, {mehndi_type.lower()} mehndi, bridal mehndi, simple mehndi, mehndi design 2025, gayatri mehndi arts pune, henna, {mehndi_type.lower()} mehndi shorts, viral mehndi"

        pack_text = (
            f"🎬 **YOUTUBE PACK - {mehndi_type.upper()}** 🎬\n\n"
            f"📐
