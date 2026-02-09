import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import time

# --- Configuration ---
API_TOKEN = '8537226856:AAGi84G9VXn3s_OIu6iZpWnKKSMz7oOimqQ'
CHANNEL_ID = '@MuleTechReact'
ADMIN_ID = 7738656478 
bot = telebot.TeleBot(API_TOKEN)
USER_FILE = "users.txt"

def save_user(user_id):
    if not os.path.exists(USER_FILE): open(USER_FILE, "w").close()
    with open(USER_FILE, "r") as f: users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f: f.write(str(user_id) + "\n")

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return True 

@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
        markup.add(types.InlineKeyboardButton("🔄 I have Joined", callback_data="check_sub"))
        bot.send_message(message.chat.id, "⚠️ **Please join our channel to use this bot!**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "👋 Welcome! Send me any video link (YouTube, TikTok, FB, IG).")

@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        start(message)
        return
    
    url = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ ቪዲዮው በመውረድ ላይ ነው... እባክዎ ይጠብቁ።")
    file_name = f"video_{int(time.time())}.mp4"

    # --- Optimized yt-dlp Options ---
    ydl_opts = {
        'format': 'best[ext=mp4]/best', # ቀጥታ mp4 እንዲፈልግ (FFmpeg ችግር ካለ እንዲያልፈው)
        'outtmpl': file_name,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'max_filesize': 45000000, # 45MB በላይ ከሆነ እንዳያወርድ (ለቴሌግራም ገደብ)
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(file_name):
            with open(file_name, 'rb') as v:
                bot.send_video(message.chat.id, v, caption=f"🎬 @{bot.get_me().username}")
            os.remove(file_name)
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ ስህተት፡ ቪዲዮውን ማውረድ አልተቻለም።", message.chat.id, status_msg.message_id)
    except Exception as e:
        error_text = str(e)
        if "Too Large" in error_text:
            bot.edit_message_text("⚠️ ቪዲዮው ከ 50MB በላይ ስለሆነ በቦት መላክ አይቻልም።", message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ ስህተት፡ ሊንኩ አልሰራም። (ቪዲዮው Private ወይም የተዘጋ ሊሆን ይችላል)", message.chat.id, status_msg.message_id)
        if os.path.exists(file_name): os.remove(file_name)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("✅ ተረጋግጧል! አሁን ሊንክ መላክ ይችላሉ።", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ አልተቀላቀሉም!", show_alert=True)

if __name__ == "__main__":
    bot.infinity_polling(allowed_updates=['message', 'callback_query'])
