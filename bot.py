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
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(str(user_id) + "\n")

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return True 

def send_force_join(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("🔄 I have Joined", callback_data="check_sub"))
    bot.send_message(message.chat.id, "⚠️ **Please join our channel to use this bot!**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
    else:
        bot.send_message(message.chat.id, "👋 Welcome to YouTube, TikTok, Facebook and Instagram video downloader!\n\nSend a link, I'll send Video & Audio.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text: return
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            users = f.read().splitlines()
        bot.send_message(ADMIN_ID, f"⏳ Sending to {len(users)} users...")
        for user in users:
            try: bot.send_message(user, msg_text); time.sleep(0.3)
            except: pass
        bot.send_message(ADMIN_ID, "✅ Broadcast Done!")

@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
        return
    
    save_user(message.from_user.id)
    url = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ Downloading... please wait.")
    
    try:
        # ቪዲዮ ማውረጃ
        ydl_opts_vid = {'format': 'best[ext=mp4]/best', 'outtmpl': 'vid.mp4', 'quiet': True}
        with YoutubeDL(ydl_opts_vid) as ydl:
            ydl.download([url])
        with open('vid.mp4', 'rb') as f:
            bot.send_video(message.chat.id, f, caption="🎬 Video")
        os.remove('vid.mp4')

        # ኦዲዮ ማውረጃ
        ydl_opts_aud = {'format': 'bestaudio/best', 'outtmpl': 'aud.mp3', 'quiet': True}
        with YoutubeDL(ydl_opts_aud) as ydl:
            ydl.download([url])
        with open('aud.mp3', 'rb') as f:
            bot.send_audio(message.chat.id, f, caption="🎵 Audio")
        os.remove('aud.mp3')

        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:50]}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("✅ Verified!", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

if __name__ == "__main__":
    bot.infinity_polling()
