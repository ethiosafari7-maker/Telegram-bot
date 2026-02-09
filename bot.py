import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import time

API_TOKEN = '8537226856:AAGi84G9VXn3s_OIu6iZpWnKKSMz7oOimqQ'
CHANNEL_ID = '@MuleTechReact'
bot = telebot.TeleBot(API_TOKEN)

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return True 

@bot.message_handler(func=lambda message: "http" in message.text)
def handle_link(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "📢 መጀመሪያ ቻናላችንን ይቀላቀሉ: @MuleTechReact")
        return
    
    url = message.text
    status_msg = bot.send_message(message.chat.id, "⏳ ዩቲዩብን በመፈተሽ ላይ... እባክዎ ይጠብቁ።")
    file_name = f"video_{int(time.time())}.mp4"

    # ዩቲዩብ ብሎክ እንዳያደርገው የተጨመሩ ቅንብሮች
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': file_name,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
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
            bot.edit_message_text("❌ ዩቲዩብ ቪዲዮውን አልፈቀደም። እባክዎ ቆይተው ይሞክሩ።", message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት፡ ዩቲዩብ ግንኙነቱን አቋርጦታል። ይህ የሚሆነው ዩቲዩብ ሰርቨሩን ለጊዜው ብሎክ ሲያደርገው ነው።", message.chat.id, status_msg.message_id)
        if os.path.exists(file_name): os.remove(file_name)

if __name__ == "__main__":
    bot.infinity_polling()
