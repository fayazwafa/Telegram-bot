import telebot
from telebot import types
import sqlite3

# Bot Token
TOKEN = '7947200381:AAF_oiplQIZ3m-fcWHaheC3eiq1Gm1M7s3w'
bot = telebot.TeleBot(TOKEN)

# Admin ID (replace with your actual Telegram numeric ID)
ADMIN_ID = 123456789

# Required channels
CHANNELS = [
    '@Allaboutairdrops001',
    '@KabulDallorRate',
    '@withoutInvestEarning09',
    '@FreeEarningBots002'
]

# Database setup
conn = sqlite3.connect('bot_users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, referrals INTEGER DEFAULT 0, wallet TEXT DEFAULT "")''')
conn.commit()

# Check subscription
def is_user_subscribed(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'creator', 'administrator']:
                return False
        except:
            return False
    return True

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    ref_id = message.text.split(' ')[1] if len(message.text.split()) > 1 else None

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    if ref_id and ref_id != str(user_id):
        cursor.execute("SELECT * FROM users WHERE user_id=?", (ref_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (ref_id,))
            conn.commit()

    if not is_user_subscribed(user_id):
        send_subscription_buttons(message.chat.id)
    else:
        send_main_menu(message.chat.id)

# Join buttons
def send_subscription_buttons(chat_id):
    markup = types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton(f"🎁 Join {ch}", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton("✅ Joined", callback_data="check_subs"))
    bot.send_message(chat_id, "🔐 **You have to join our channels.**\n\nAfter joining, press ✅ **Joined**", reply_markup=markup, parse_mode="Markdown")

# Subscription check
@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs(call):
    if is_user_subscribed(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ **Thank you! You’re verified.**", parse_mode="Markdown")
        send_main_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Please join all channels first!")

# Main menu
def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 My Balance", "👥 Referral")
    markup.row("🏧 Withdraw", "💳 Set Wallet")
    markup.add("📊 Statistic")
    bot.send_message(chat_id, "❤️ **Welcome to our bot!**", reply_markup=markup, parse_mode="Markdown")

# Button handler
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id

    if not is_user_subscribed(user_id):
        send_subscription_buttons(message.chat.id)
        return

    if message.text == "💰 My Balance":
        cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
        data = cursor.fetchone()
        balance = data[0] * 1 if data else 0
        bot.send_message(message.chat.id, f"💸 **Your Balance:** `{balance}` TRX", parse_mode="Markdown")

    elif message.text == "👥 Referral":
        referral_link = f"https://t.me/TerisTsakbot?start={user_id}"
        cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
        data = cursor.fetchone()
        bot.send_message(message.chat.id, f"👥 **Your Referral Link:**\n`{referral_link}`\n\n**Total Referrals:** `{data[0] if data else 0}`", parse_mode="Markdown")

    elif message.text == "🏧 Withdraw":
        cursor.execute("SELECT referrals, wallet FROM users WHERE user_id=?", (user_id,))
        data = cursor.fetchone()
        if not data or data[0] < 10:
            bot.send_message(message.chat.id, "❌ **You need at least 10 referrals to withdraw.**", parse_mode="Markdown")
        elif not data[1]:
            bot.send_message(message.chat.id, "❗ **Please set your TRX wallet first using** `💳 Set Wallet`", parse_mode="Markdown")
        else:
            # User message
            bot.send_message(message.chat.id, "✅ **Your withdrawal request has been received!**\n⏳ Please wait up to 24 hours.", parse_mode="Markdown")
            # Admin message (private)
            username = f"@{message.from_user.username}" if message.from_user.username else "No username"
            bot.send_message(ADMIN_ID, f"✅ Withdrawal Request:\n\nUser: {username}\nID: `{user_id}`\nReferrals: `{data[0]}`\nWallet: `{data[1]}`", parse_mode="Markdown")

    elif message.text == "💳 Set Wallet":
        bot.send_message(message.chat.id, "💳 **Please send your TRX wallet address:**", parse_mode="Markdown")
        bot.register_next_step_handler(message, save_wallet)

    elif message.text == "📊 Statistic":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"📊 **Total Users:** `{total_users}`", parse_mode="Markdown")

    else:
        bot.send_message(message.chat.id, "❌ **Invalid option. Please use the menu buttons.**", parse_mode="Markdown")

# Save wallet
def save_wallet(message):
    wallet = message.text.strip()
    user_id = message.from_user.id
    cursor.execute("UPDATE users SET wallet=? WHERE user_id=?", (wallet, user_id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ **Wallet address saved!**", parse_mode="Markdown")

# Start bot
print("🤖 Bot is running...")
bot.infinity_polling()