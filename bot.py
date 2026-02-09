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

# --- Database Management ---
def save_user(user_id):
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(str(user_id) + "\n")

# --- Force Join System ---
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

# --- 1. Welcome Message ---
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
    else:
        welcome_text = (
            "👋 Welcome to YouTube, TikTok, Facebook and Instagram video downloader!\n\n"
            "📌 **How to use:**\n"
            "Just send me any video link and I will download the video for you."
        )
        bot.send_message(message.chat.id, welcome_text)

# --- 2. Admin Broadcast ---
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "📌 Usage: `/broadcast Your Message`")
        return
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            users = f.read().splitlines()
        bot.send_message(ADMIN_ID, f"⏳ Sending to {len(users)} users...")
        for user in users:
            try:
                bot.send_message(user, msg_text)
                time.sleep(0.3)
            except: pass
        bot.send_message(ADMIN_ID, "✅ Broadcast Done!")

# --- 3. Inline Search ---
@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    try:
        search_query = inline_query.query
        ydl_opts = {'quiet': True, 'noplaylist': True, 'format': 'best'}
        with YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch5:{search_query}", download=False)['entries']
        
        inline_results = []
        for entry in results:
            if not entry: continue
            r = types.InlineQueryResultArticle(
                id=entry['id'],
                title=entry['title'],
                description=f"📺 {entry.get('uploader', 'YouTube')}",
                thumb_url=entry.get('thumbnail'),
                input_message_content=types.InputTextMessageContent(entry['webpage_url'])
            )
            inline_results.append(r)
        bot.answer_inline_query(inline_query.id, inline_results)
    except Exception as e:
        print(f"Inline Search Error: {e}")

# --- 4. Main Video Handler ---
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
        return
    
    save_user(message.from_user.id)
    url = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ ቪዲዮውን በማዘጋጀት ላይ ነኝ... እባክዎ ይጠብቁ።")

    # ምርጡን ቪዲዮ ለማውረድ የሚያገለግል ቅንብር
    file_name = f"vid_{int(time.time())}.mp4"
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_name,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
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
            bot.edit_message_text("❌ ስህተት፡ ቪዲዮውን ማግኘት አልተቻለም።", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል! ሊንኩን ወይም የቪዲዮውን መጠን ያረጋግጡ።", message.chat.id, status_msg.message_id)
        if os.path.exists(file_name): os.remove(file_name)

# --- 5. Subscription Verification ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("✅ Verified! You can now send links.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

# --- 6. Polling ---
if __name__ == "__main__":
    print("🚀 Video Downloader is Active...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60, allowed_updates=['message', 'callback_query', 'inline_query'])
        except Exception as e:
            time.sleep(5)
