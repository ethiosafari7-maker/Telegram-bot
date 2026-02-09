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
            "Just send me the link and I will send you both Video and Audio automatically."
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
                description=f"📺 {entry.get('uploader', 'Unknown')}",
                thumb_url=entry.get('thumbnail'),
                input_message_content=types.InputTextMessageContent(entry['webpage_url'])
            )
            inline_results.append(r)
        bot.answer_inline_query(inline_query.id, inline_results)
    except Exception as e:
        print(f"Inline error: {e}")

# --- 4. Handle Link (Automatic Download) ---
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        send_force_join(message)
        return
    
    save_user(message.from_user.id)
    url = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ Downloading Video and Audio... Please wait.")
    
    # መጀመሪያ ቪዲዮውን ያወርዳል
    vid_file = download_file(url, is_mp3=False)
    if vid_file:
        with open(vid_file, 'rb') as f:
            bot.send_video(message.chat.id, f, caption=f"🎬 Video - @{bot.get_me().username}")
        os.remove(vid_file)
    
    # በመቀጠል ኦዲዮውን ያወርዳል
    aud_file = download_file(url, is_mp3=True)
    if aud_file:
        with open(aud_file, 'rb') as f:
            bot.send_audio(message.chat.id, f, caption=f"🎵 Audio - @{bot.get_me().username}")
        os.remove(aud_file)

    bot.delete_message(message.chat.id, status_msg.message_id)

# --- 5. Download Helper ---
def download_file(url, is_mp3):
    ext = "mp3" if is_mp3 else "mp4"
    file_name = f"file_{int(time.time())}_{ext}.{ext}"
    ydl_opts = {
        'format': 'bestaudio/best' if is_mp3 else 'bestvideo+bestaudio/best',
        'outtmpl': file_name,
        'merge_output_format': 'mp4' if not is_mp3 else None,
        'quiet': True,
        'no_warnings': True
    }
    if is_mp3:
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return file_name if os.path.exists(file_name) else None
    except:
        return None

# --- 6. Verification Callback ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("✅ Verified! Send a link.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join the channel first!", show_alert=True)

if __name__ == "__main__":
    print("🚀 Automatic Downloader Active...")
    bot.infinity_polling()
