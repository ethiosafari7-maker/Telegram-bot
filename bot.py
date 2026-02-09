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

# --- Database ---
def save_user(user_id):
    if not os.path.exists(USER_FILE):
        open(USER_FILE, "w").close()
    with open(USER_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USER_FILE, "a") as f:
            f.write(str(user_id) + "\n")

# --- Subscription Guard ---
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

# --- 1. Start Command ---
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
    else:
        welcome_text = (
            "👋 Welcome to YouTube, TikTok, Facebook and Instagram video downloader!\n\n"
            "📌 **How to use:**\n"
            "1. Send me any video link directly.\n"
            "2. Or type `@YOUR_BOT_USERNAME` followed by a video name to search."
        )
        bot.send_message(message.chat.id, welcome_text)

# --- 2. Admin Broadcast ---
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

# --- 3. Inline Search (የፍለጋ ተግባር) ---
@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    try:
        search_query = inline_query.query
        ydl_opts = {'quiet': True, 'noplaylist': True, 'format': 'best'}
        with YoutubeDL(ydl_opts) as ydl:
            # 5 ፍለጋዎችን ብቻ እንዲያመጣ (ለፍጥነት)
            results = ydl.extract_info(f"ytsearch5:{search_query}", download=False)['entries']
            
        inline_results = []
        for entry in results:
            if not entry: continue
            # ቪዲዮውን ለማውረድ የሚያስችል ቁልፍ
            r = types.InlineQueryResultArticle(
                id=entry['id'],
                title=entry['title'],
                description=f"📺 Channel: {entry.get('uploader', 'Unknown')}",
                thumb_url=entry.get('thumbnail'),
                input_message_content=types.InputTextMessageContent(entry['webpage_url'])
            )
            inline_results.append(r)
        
        bot.answer_inline_query(inline_query.id, inline_results)
    except Exception as e:
        print(f"Inline error: {e}")

# --- 4. Direct Link Handling ---
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
        return
    
    save_user(message.from_user.id)
    url = message.text
    # ቪዲዮ ወይስ ኦዲዮ? የሚል ምርጫ
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎬 Video", callback_data=f"dl_vid_{url}"),
        types.InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"dl_aud_{url}")
    )
    bot.send_message(message.chat.id, "Select format:", reply_markup=markup)

# --- 5. Download Callbacks ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_") or call.data == "check_sub")
def handle_callbacks(call):
    if call.data == "check_sub":
        if is_subscribed(call.from_user.id):
            bot.edit_message_text("✅ Verified! Send a link.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Join the channel first!", show_alert=True)
        return

    # ማውረድ ሲጀመር
    is_mp3 = "dl_aud_" in call.data
    url = call.data.replace("dl_vid_", "").replace("dl_aud_", "")
    
    bot.edit_message_text("⏳ Processing... please wait.", call.message.chat.id, call.message.message_id)
    download_logic(call.message.chat.id, url, call.message.message_id, is_mp3)

# --- 6. Download Logic ---
def download_logic(chat_id, url, status_id, is_mp3):
    ext = "mp3" if is_mp3 else "mp4"
    file_name = f"file_{int(time.time())}.{ext}"
    
    ydl_opts = {
        'format': 'bestaudio/best' if is_mp3 else 'bestvideo+bestaudio/best',
        'outtmpl': file_name,
        'merge_output_format': 'mp4' if not is_mp3 else None,
        'quiet': True
    }
    
    if is_mp3:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        with open(file_name, 'rb') as f:
            if is_mp3: bot.send_audio(chat_id, f, caption=f"🎵 @{bot.get_me().username}")
            else: bot.send_video(chat_id, f, caption=f"✅ @{bot.get_me().username}")
            
        os.remove(file_name)
        bot.delete_message(chat_id, status_id)
    except Exception as e:
        bot.edit_message_text("❌ Error downloading video.", chat_id, status_id)
        if os.path.exists(file_name): os.remove(file_name)

# --- Polling ---
if __name__ == "__main__":
    print("🚀 Bot with Search is Active...")
    bot.infinity_polling()

