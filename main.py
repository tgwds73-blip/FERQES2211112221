import telebot
from telebot import types
import sqlite3
import os
import time
import random
import logging
import re
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# ========== НАСТРОЙКИ ЛОГИРОВАНИЯ ==========
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler('bot.log', maxBytes=5 * 1024 * 1024, backupCount=10, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ========== НАСТРОЙКИ БОТА ==========
BOT_TOKEN = '8781916300:AAGMQekaqp5ED5W1BoUnPIygQAA_m92mr1E'
bot = telebot.TeleBot(BOT_TOKEN)
GAMES_CHANNEL_ID = -1003421344618
BANNER_ID = 1749

# Константы
BAN_DURATIONS = {
    '1h': timedelta(hours=1), '6h': timedelta(hours=6), '12h': timedelta(hours=12),
    '1d': timedelta(days=1), '3d': timedelta(days=3), '7d': timedelta(days=7),
    '30d': timedelta(days=30), 'forever': None
}
MUTE_DURATIONS = {
    '1h': timedelta(hours=1), '6h': timedelta(hours=6), '12h': timedelta(hours=12),
    '1d': timedelta(days=1), '3d': timedelta(days=3), '7d': timedelta(days=7)
}
PRIORITY_COST = 50
ORDER_EXPIRE_DAYS = 70
AUTO_DELETE_REPORTS = 15
MAX_BANNED_WORD_ATTEMPTS = 3

BANNED_WORDS = [
    'продам', 'продаю', 'куплю', 'купить', 'цена', 'недорого',
    'реклама', 'пиар', 'накрутка', 'подписчики',
    'buy', 'price', 'cheap', 'spam',
    'http', 'https', 'www', '.com', '.ru',
    'telegram', 't.me', 'vk.com', 'discord', 'whatsapp',
    'пишите', 'звоните',
    'сука', 'бля', 'блять', 'блядь', 'хуй', 'пизда', 'ебать', 'нахуй', 'ахуел', 'ахуеть',
    'fuck', 'shit', 'bitch',
    'казино', 'ставки', 'заработок', 'схема', 'лохотрон',
    'casino', 'bet', 'scam',
    'нарко', 'трава', 'закладка', 'клад', 'weed', 'drugs',
]

# ========== БАЗА ДАННЫХ ==========
DATA_DIR = os.getenv('DATA_DIR', '.')
DB_FILE = os.path.join(DATA_DIR, 'bot_database.db')


def generate_unique_id():
    """Генерирует уникальный 6-значный ID"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    while True:
        uid = str(random.randint(100000, 999999))
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (uid,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return uid
    conn.close()


def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Пользователи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            unique_id TEXT UNIQUE,
            username TEXT,
            first_name TEXT,
            downloads INTEGER DEFAULT 0,
            created_orders INTEGER DEFAULT 0,
            stars_donated INTEGER DEFAULT 0,
            first_seen TIMESTAMP,
            last_active TIMESTAMP,
            is_banned BOOLEAN DEFAULT 0,
            ban_until TIMESTAMP,
            ban_reason TEXT,
            is_muted BOOLEAN DEFAULT 0,
            mute_until TIMESTAMP,
            mute_reason TEXT,
            banned_word_attempts INTEGER DEFAULT 0,
            last_banned_attempt TIMESTAMP,
            achievements TEXT DEFAULT ''
        )
    ''')

    # Досылаем недостающие колонки
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    for col, col_type in [
        ('unique_id', 'TEXT UNIQUE'),
        ('ban_until', 'TIMESTAMP'), ('ban_reason', 'TEXT'),
        ('is_muted', 'BOOLEAN DEFAULT 0'), ('mute_until', 'TIMESTAMP'), ('mute_reason', 'TEXT'),
        ('banned_word_attempts', 'INTEGER DEFAULT 0'), ('last_banned_attempt', 'TIMESTAMP'),
        ('achievements', "TEXT DEFAULT ''")
    ]:
        if col not in columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            except:
                pass

    # Заказы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_name TEXT,
            size TEXT,
            likes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            priority BOOLEAN DEFAULT 0,
            created_date TIMESTAMP,
            anonymous BOOLEAN DEFAULT 0,
            views INTEGER DEFAULT 0,
            admin_comment TEXT,
            subscribers TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    for col, col_type in [
        ('anonymous', 'BOOLEAN DEFAULT 0'), ('priority', 'BOOLEAN DEFAULT 0'),
        ('views', 'INTEGER DEFAULT 0'), ('admin_comment', 'TEXT'),
        ('subscribers', "TEXT DEFAULT ''")
    ]:
        if col not in columns:
            try:
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_type}")
            except:
                pass

    # Лайки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_likes (
            order_id INTEGER, user_id INTEGER, liked_date TIMESTAMP,
            PRIMARY KEY (order_id, user_id)
        )
    ''')

    # Жалобы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER, reporter_id INTEGER,
            reason TEXT, reported_date TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    ''')

    # История скачиваний
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, game_name TEXT,
            file_count INTEGER, download_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Достижения
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_key TEXT,
            achievement_name TEXT,
            earned_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Игры (основная база)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE,
            file_ids TEXT,
            downloads INTEGER DEFAULT 0,
            added_date TIMESTAMP
        )
    ''')

    # Игры LQ (альтернативная база)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games_lq (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE,
            file_ids TEXT,
            downloads INTEGER DEFAULT 0,
            added_date TIMESTAMP
        )
    ''')

    # Логи
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS action_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, timestamp TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS donations (donation_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, stars_amount INTEGER, status TEXT DEFAULT 'pending', created_date TIMESTAMP, completed_date TIMESTAMP)''')

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


init_database()


def init_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (7885915159,))
    conn.commit()
    conn.close()


init_admin()

# ========== ЗАГРУЗКА ИГР ИЗ БД ==========
GAMES_DATABASE = {}
GAMES_LQ_DATABASE = {}


def load_games_from_db():
    """Загружает все игры из базы данных"""
    global GAMES_DATABASE, GAMES_LQ_DATABASE
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT game_name, file_ids FROM games")
    for name, file_ids in cursor.fetchall():
        GAMES_DATABASE[name] = list(map(int, file_ids.split(',')))

    cursor.execute("SELECT game_name, file_ids FROM games_lq")
    for name, file_ids in cursor.fetchall():
        GAMES_LQ_DATABASE[name] = list(map(int, file_ids.split(',')))

    conn.close()
    logger.info(f"Загружено игр: {len(GAMES_DATABASE)} HQ, {len(GAMES_LQ_DATABASE)} LQ")


load_games_from_db()

user_states = {}

# ========== БАННЕР ==========
BANNER_TEXT = """<blockquote>🔥 <b>БЕЗ ВСТРОЕННЫХ ПРОГРАММ ИЛИ ВИРУСОВ</b>
🔥 <b><a href="https://t.me/FerwesGames">FERWES / GAMES</a></b>
🔥 <b><a href="https://t.me/addlist/AW1LBTA9xa45NDIy">FERWES / GRID</a></b></blockquote>"""

# ========== АЧИВКИ ==========
ACHIEVEMENTS = {
    'first_download': ('🥉', 'Первый контакт', 'Первое скачивание'),
    'first_order': ('🥉', 'Искатель', 'Первый созданный заказ'),
    'first_like': ('🥉', 'Доброе сердце', 'Первый лайк на заказе'),
    'first_donate': ('🥉', 'Меценат', 'Первый донат'),
    'downloads_10': ('🥈', 'Коллекционер', 'Скачать 10 игр'),
    'downloads_50': ('🥈', 'Геймер', 'Скачать 50 игр'),
    'downloads_100': ('🥇', 'Хардкорщик', 'Скачать 100 игр'),
    'downloads_500': ('🥇', 'Легенда', 'Скачать 500 игр'),
    'orders_5': ('🥈', 'Заказчик', 'Создать 5 заказов'),
    'orders_20': ('🥇', 'Звезда', 'Создать 20 заказов'),
    'likes_25': ('🥈', 'Популярный', 'Получить 25 лайков'),
    'likes_100': ('🥇', 'Любимчик', 'Получить 100 лайков'),
    'donate_500': ('🥇', 'Спонсор', 'Задонатить 500 Stars'),
    'priority_10': ('👑', 'Бог заказов', '10 приоритетных заказов'),
    'anonymous_5': ('💎', 'Шепчущий', '5 анонимных заказов подряд'),
    'days_365': ('💎', 'Верный друг', '365 дней в боте'),
    'night_download': ('👑', 'Ночной сталкер', 'Скачать игру ночью 3-5 утра'),
}


# ========== БЕЙДЖИ ==========
def get_user_badge(orders_count, likes_count, priority_count):
    badges = []
    if orders_count >= 50:
        badges.append('👑 Король заказов')
    elif orders_count >= 20:
        badges.append('💫 Мастер заказов')
    elif orders_count >= 10:
        badges.append('🌟⭐ Опытный')
    elif orders_count >= 5:
        badges.append('⭐ Заказчик')
    else:
        badges.append('🌟 Новичок')

    if likes_count >= 50: badges.append('🔥 Популярный')
    if priority_count >= 10: badges.append('💎 Элита')

    return ' | '.join(badges)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def escape_html(text):
    if text is None: return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def log_action(user_id, action, details=""):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO action_logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
                       (str(user_id), action, details, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except:
        pass


def get_or_create_user(user_id, username=None, first_name=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        unique_id = generate_unique_id()
        cursor.execute(
            "INSERT INTO users (user_id, unique_id, username, first_name, first_seen, last_active) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, unique_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
    else:
        cursor.execute("UPDATE users SET last_active = ?, username = ?, first_name = ? WHERE user_id = ?",
                       (datetime.now().isoformat(), username, first_name, user_id))
    conn.commit()
    conn.close()
    return True


def get_user_unique_id(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT unique_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_user_by_unique_id(unique_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE unique_id = ?", (unique_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def is_banned(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned, ban_until FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if not result or not result[0]: return False
    if result[1]:
        ban_until = datetime.fromisoformat(result[1])
        if datetime.now() > ban_until:
            unban_user(user_id)
            return False
    return True


def unban_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned = 0, ban_until = NULL, ban_reason = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def is_muted(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_muted, mute_until FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if not result or not result[0]: return False
    if result[1]:
        mute_until = datetime.fromisoformat(result[1])
        if datetime.now() > mute_until:
            unmute_user(user_id)
            return False
    return True


def unmute_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_muted = 0, mute_until = NULL, mute_reason = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def check_banned_words(text):
    """Проверяет текст на запрещённые слова. Возвращает (True, слово) если найдено"""
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True, word
    return False, None


def check_and_award_achievement(user_id, key):
    """Проверяет и выдаёт ачивку"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_achievements WHERE user_id = ? AND achievement_key = ?", (user_id, key))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False

    if key in ACHIEVEMENTS:
        emoji, name, desc = ACHIEVEMENTS[key]
        cursor.execute(
            "INSERT INTO user_achievements (user_id, achievement_key, achievement_name, earned_date) VALUES (?, ?, ?, ?)",
            (user_id, key, f"{emoji} {name}", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return name
    conn.close()
    return False


def send_game_files(chat_id, game_name, user_id=None, is_lq=False):
    """Отправка игры файлами из канала"""
    database = GAMES_LQ_DATABASE if is_lq else GAMES_DATABASE

    if game_name not in database:
        return False

    file_ids = database[game_name]

    try:
        for idx, file_id in enumerate(file_ids, 1):
            try:
                bot.copy_message(chat_id, GAMES_CHANNEL_ID, file_id)
                if idx % 10 == 0: time.sleep(0.3)
            except:
                pass

        bot.send_message(chat_id, BANNER_TEXT, parse_mode='HTML', disable_web_page_preview=True)

        if user_id:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))

            table = 'games_lq' if is_lq else 'games'
            cursor.execute(f"UPDATE {table} SET downloads = downloads + 1 WHERE game_name = ?", (game_name,))

            cursor.execute(
                "INSERT INTO download_history (user_id, game_name, file_count, download_date) VALUES (?, ?, ?, ?)",
                (user_id, game_name, len(file_ids), datetime.now().isoformat()))
            conn.commit()
            conn.close()

            # Проверка ачивок
            check_and_award_achievement(user_id, 'first_download')

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM download_history WHERE user_id = ?", (user_id,))
            total = cursor.fetchone()[0]
            conn.close()

            if total >= 10: check_and_award_achievement(user_id, 'downloads_10')
            if total >= 50: check_and_award_achievement(user_id, 'downloads_50')
            if total >= 100: check_and_award_achievement(user_id, 'downloads_100')
            if total >= 500: check_and_award_achievement(user_id, 'downloads_500')

            # Ночной сталкер
            hour = datetime.now().hour
            if 3 <= hour < 5:
                check_and_award_achievement(user_id, 'night_download')

        return True
    except Exception as e:
        logger.error(f"Ошибка отправки {game_name}: {e}")
        bot.send_message(chat_id, "❌ Ошибка при отправке игры.")
        return False


def search_games(query, is_lq=False):
    database = GAMES_LQ_DATABASE if is_lq else GAMES_DATABASE
    query = query.lower().strip()
    if query in database: return [query]
    results = [g for g in database if query in g or g in query]
    results.sort(key=lambda x: len(x))
    return results[:8]


# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private': return

    # Проверка deep link
    if message.text and 'start=order_' in message.text:
        try:
            order_id = int(message.text.split('order_')[1])
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT order_id, game_name, size, likes, created_date, priority, anonymous FROM orders WHERE order_id = ?",
                (order_id,))
            order = cursor.fetchone()
            conn.close()
            if order:
                priority_emoji = "🔴" if order[5] else "🔵"
                anon_text = "👻 Аноним" if order[6] else "👤 Открыто"
                try:
                    date_str = datetime.fromisoformat(order[4]).strftime("%d.%m.%Y")
                except:
                    date_str = "неизвестно"
                text = f"📋 <b>ЗАКАЗ #{order[0]}</b>\n\n🎮 {order[1]}\n💾 {order[2]}\n{priority_emoji} {'Приоритет' if order[5] else 'Обычный'}\n{anon_text}\n📅 {date_str} | ❤️ {order[3]}"
                bot.send_message(message.chat.id, text, parse_mode='HTML')
                return
        except:
            pass

    user = message.from_user
    get_or_create_user(user.id, user.username, user.first_name)

    if is_banned(user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    unique_id = get_user_unique_id(user.id)

    text = f"""Привет, {user.first_name or 'пользователь'}!

🔍 <b>Напиши название игры</b> — я найду и отправлю.

📋 /orders — стол заказов
📝 /neworder — создать заказ
👤 /me — мой профиль (#{unique_id})
📜 /history — история скачиваний
💰 /donate — поддержать бота

💡 Нет игры? → /neworder
━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | ❓ /help"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="show_me"),
        types.InlineKeyboardButton("📜 История", callback_data="show_history"),
        types.InlineKeyboardButton("💰 Поддержать", callback_data="show_donate"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== ПРОФИЛЬ /me ==========
@bot.message_handler(commands=['me'])
def me_cmd(message):
    if message.chat.type != 'private': return
    show_profile(message.chat.id, message.from_user.id)


def show_profile(chat_id, user_id):
    if is_banned(user_id):
        bot.send_message(chat_id, "🚫 Вы заблокированы")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unique_id, username, first_name, downloads, created_orders, stars_donated, first_seen FROM users WHERE user_id = ?",
        (user_id,))
    user = cursor.fetchone()

    if not user:
        bot.send_message(chat_id, "❌ Профиль не найден")
        conn.close()
        return

    unique_id, username, first_name, downloads, created_orders, stars, first_seen = user

    # Лайки
    cursor.execute("SELECT SUM(likes) FROM orders WHERE user_id = ?", (user_id,))
    total_likes = cursor.fetchone()[0] or 0

    # Приоритетные заказы
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND priority = 1", (user_id,))
    priority_count = cursor.fetchone()[0]

    # Ачивки
    cursor.execute("SELECT achievement_name FROM user_achievements WHERE user_id = ? ORDER BY earned_date DESC",
                   (user_id,))
    achievements = cursor.fetchall()
    conn.close()

    try:
        days_active = (datetime.now() - datetime.fromisoformat(first_seen)).days
    except:
        days_active = 0

    # Бейдж
    badge = get_user_badge(created_orders, total_likes, priority_count)

    text = f"""👤 <b>ПРОФИЛЬ</b>
━━━━━━━━━━━━━━━━━━
🆔 <code>#{unique_id}</code>
👤 {first_name or 'Пользователь'} {f'(@{username})' if username else ''}
🛡 {badge}

📊 <b>СТАТИСТИКА</b>
🎮 Скачано игр: {downloads}
📋 Создано заказов: {created_orders}
❤️ Получено лайков: {total_likes}
⭐ Stars: {stars}
📅 Дней в боте: {days_active}

🏆 <b>ДОСТИЖЕНИЯ</b> ({len(achievements)}/{len(ACHIEVEMENTS)})"""

    if achievements:
        text += "\n" + " ".join([a[0].split()[0] for a in achievements[:10]])

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📜 Все ачивки", callback_data="all_achievements"),
        types.InlineKeyboardButton("🏆 Топ заказов", callback_data="top_orders")
    )
    markup.add(
        types.InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📥 История", callback_data="show_history")
    )
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))

    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== АЧИВКИ ==========
@bot.callback_query_handler(func=lambda call: call.data == 'all_achievements')
def all_achievements_callback(call):
    user_id = call.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_key FROM user_achievements WHERE user_id = ?", (user_id,))
    earned = [r[0] for r in cursor.fetchall()]
    conn.close()

    text = "🏆 <b>ВСЕ ДОСТИЖЕНИЯ</b>\n\n"
    for key, (emoji, name, desc) in ACHIEVEMENTS.items():
        earned_mark = "✅" if key in earned else "🔒"
        text += f"{earned_mark} {emoji} <b>{name}</b>\n<i>{desc}</i>\n\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="show_me"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML',
                              reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)


# ========== ТОП ЗАКАЗОВ ==========
@bot.callback_query_handler(func=lambda call: call.data == 'top_orders')
def top_orders_callback(call):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.first_name, u.unique_id, 
               COUNT(o.order_id) as order_count, 
               COALESCE(SUM(o.likes), 0) as total_likes,
               COUNT(CASE WHEN o.priority = 1 THEN 1 END) as priority_count
        FROM users u LEFT JOIN orders o ON u.user_id = o.user_id 
        GROUP BY u.user_id ORDER BY order_count DESC LIMIT 10
    """)
    top_users = cursor.fetchall()
    conn.close()

    text = "🏆 <b>ТОП-10 ЗАКАЗЧИКОВ</b>\n\n"
    for i, user in enumerate(top_users, 1):
        username, first_name, unique_id, order_count, total_likes, priority_count = user
        name = f"@{username}" if username else first_name or f"#{unique_id}"
        badge = get_user_badge(order_count, total_likes, priority_count).split(' | ')[0]
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {badge} {name} — {order_count} заказов, {total_likes} ❤️\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="show_me"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML',
                              reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)


# ========== HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    text = """ℹ️ <b>ПОМОЩЬ</b>
🔍 Напиши название игры — бот найдёт и отправит
📋 /orders — стол заказов
📝 /neworder — создать заказ
👤 /me — профиль и ачивки
📜 /history — история скачиваний
⚠️ /report ID причина — жалоба на заказ
💰 /donate — поддержать бота
━━━━━━━━━━━━━━━━━━
📢 @FerwesGames"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== DONATE ==========
@bot.message_handler(commands=['donate'])
def donate_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    show_donate_menu(message.chat.id)


def show_donate_menu(chat_id):
    text = f"""💰 <b>ПОДДЕРЖАТЬ БОТА</b>
⭐ {PRIORITY_COST} Stars = 🔴 Приоритетный заказ
<b>Выберите сумму:</b>"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("⭐ 10", callback_data="donate_10"),
        types.InlineKeyboardButton("⭐ 20", callback_data="donate_20"),
        types.InlineKeyboardButton("⭐ 30", callback_data="donate_30"),
        types.InlineKeyboardButton("⭐ 40", callback_data="donate_40"),
        types.InlineKeyboardButton("⭐ 50", callback_data="donate_50"),
        types.InlineKeyboardButton("🌟 100", callback_data="donate_100")
    )
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="back_to_start"))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== ИСТОРИЯ ==========
@bot.message_handler(commands=['history'])
def history_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    show_history(message.chat.id, message.from_user.id)


def show_history(chat_id, user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT game_name, file_count, download_date FROM download_history WHERE user_id = ? ORDER BY download_date DESC LIMIT 20",
        (user_id,))
    history = cursor.fetchall()
    conn.close()

    if not history:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔍 Найти игру", callback_data="back_to_start"))
        bot.send_message(chat_id,
                         "📜 <b>ИСТОРИЯ СКАЧИВАНИЙ</b>\n\nУ вас пока нет скачиваний.\n\nНапишите название игры!",
                         parse_mode='HTML', reply_markup=markup)
        return

    text = f"📜 <b>ИСТОРИЯ СКАЧИВАНИЙ</b> ({len(history)})\n\n"
    for game_name, file_count, download_date in history:
        try:
            date_str = datetime.fromisoformat(download_date).strftime("%d.%m.%Y %H:%M")
        except:
            date_str = "неизвестно"
        text += f"🎮 {game_name}\n📦 {file_count} файлов | 📅 {date_str}\n━\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== ORDERS (ВЫПАДАЮЩЕЕ МЕНЮ) ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    show_orders_page(message.chat.id, 0, message.from_user.id)


def show_orders_page(chat_id, page=0, viewer_id=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.game_name, o.size, o.likes, o.status, o.created_date, 
               o.anonymous, o.priority, o.views, o.admin_comment, u.username,
               (SELECT COUNT(*) FROM order_reports WHERE order_id = o.order_id) as report_count
        FROM orders o LEFT JOIN users u ON o.user_id = u.user_id 
        WHERE o.status = 'active' ORDER BY o.priority DESC, o.created_date DESC
    """)
    all_orders = cursor.fetchall()
    conn.close()

    if not all_orders:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(chat_id, "📭 <b>Нет активных заказов</b>\n\nСтаньте первым!", parse_mode='HTML',
                         reply_markup=markup)
        return

    orders_per_page = 5
    total_pages = (len(all_orders) + orders_per_page - 1) // orders_per_page
    if page >= total_pages: page = total_pages - 1
    if page < 0: page = 0

    start_idx = page * orders_per_page
    end_idx = min(start_idx + orders_per_page, len(all_orders))
    page_orders = all_orders[start_idx:end_idx]

    priority_count = sum(1 for o in all_orders if o[8] == 1 or o[8] == True)
    new_count = sum(1 for o in all_orders if (datetime.now() - datetime.fromisoformat(o[6])).days < 2)

    text = f"📋 <b>СТОЛ ЗАКАЗОВ</b>\n━━━━━━━━━━━━━━━━━━\n📊 Всего: {len(all_orders)} | 🔴 {priority_count} | 🔵 {len(all_orders) - priority_count} | 🆕 {new_count}\n📄 Стр. {page + 1}/{total_pages}\n━━━━━━━━━━━━━━━━━━\n\n"

    for order in page_orders:
        order_id, user_id, game_name, size, likes, status, created_date, anonymous, priority, views, admin_comment, username, report_count = order

        try:
            date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y")
        except:
            date_str = "неизвестно"

        is_new = (datetime.now() - datetime.fromisoformat(created_date)).days < 2

        if priority == 1 or priority == True:
            priority_emoji = "🔴"
        else:
            priority_emoji = "🔵"

        new_badge = " 🆕" if is_new else ""
        report_badge = f" ⚠️{report_count}" if report_count > 0 else ""
        anon_badge = " 👻" if anonymous else ""

        text += f"{priority_emoji} <b>#{order_id}</b>{new_badge} | 🎮 {game_name}{anon_badge}\n❤️ {likes} | 📅 {date_str}{report_badge}\n"
        text += f"[▼ Подробнее #" + str(order_id) + "]\n"
        text += "━\n"

    markup = types.InlineKeyboardMarkup(row_width=5)

    # Навигация
    nav_buttons = []
    if page > 0: nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1: nav_buttons.append(
        types.InlineKeyboardButton("▶️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)

    # Кнопки "Подробнее" для каждого заказа
    for order in page_orders:
        markup.add(types.InlineKeyboardButton(f"▼ #{order[0]} {order[2][:15]}",
                                              callback_data=f"order_detail_{order[0]}_{page}"))

    markup.add(
        types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders")
    )
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))

    try:
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
    except:
        bot.send_message(chat_id, re.sub(r'<[^>]+>', '', text), reply_markup=markup)


# ========== ДЕТАЛИ ЗАКАЗА (ВЫПАДАЮЩЕЕ МЕНЮ) ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('order_detail_'))
def order_detail_callback(call):
    parts = call.data.split('_')
    order_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.game_name, o.size, o.likes, o.status, o.created_date, 
               o.anonymous, o.priority, o.views, o.admin_comment, u.username, u.first_name,
               (SELECT COUNT(*) FROM order_reports WHERE order_id = o.order_id) as report_count,
               (SELECT COUNT(*) FROM orders o2 WHERE o2.user_id = o.user_id AND o2.priority = 1) as user_priority_count
        FROM orders o LEFT JOIN users u ON o.user_id = u.user_id 
        WHERE o.order_id = ?
    """, (order_id,))
    order = cursor.fetchone()
    conn.close()

    if not order:
        bot.answer_callback_query(call.id, "❌ Заказ не найден")
        return

    (order_id, user_id, game_name, size, likes, status, created_date, anonymous, priority,
     views, admin_comment, username, first_name, report_count, user_priority_count) = order

    # Увеличиваем счётчик просмотров
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET views = views + 1 WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()
    views += 1

    try:
        date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y %H:%M")
    except:
        date_str = "неизвестно"

    days_left = ORDER_EXPIRE_DAYS - (datetime.now() - datetime.fromisoformat(created_date)).days

    priority_emoji = "🔴" if priority else "🔵"
    priority_text = "ПРИОРИТЕТ" if priority else "Обычный"

    if anonymous:
        author = "👤 Аноним"
        author_name = "Аноним"
    elif username:
        author = f"👤 @{username}"
        author_name = first_name or username
    else:
        author = f"👤 ID:{user_id}"
        author_name = f"ID:{user_id}"

    # Бейдж автора
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    author_orders = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(likes) FROM orders WHERE user_id = ?", (user_id,))
    author_likes = cursor.fetchone()[0] or 0
    conn.close()

    author_badge = get_user_badge(author_orders, author_likes, user_priority_count).split(' | ')[0]

    text = f"""📋 <b>ЗАКАЗ #{order_id}</b>
━━━━━━━━━━━━━━━━━━
🎮 <b>{escape_html(game_name)}</b>
💾 Размер: {size}
{priority_emoji} {priority_text} | {author}{' 👻' if anonymous else ''}
━━━━━━━━━━━━━━━━━━
📊 <b>ИНФО</b>
👤 Автор: {author_name} ({author_badge})
📅 Создан: {date_str}
👁 Просмотров: {views}
❤️ Лайков: {likes}
⚠️ Жалоб: {report_count}
⏳ Осталось: {days_left} дней
{f'💬 Комментарий: {admin_comment}' if admin_comment else ''}
━━━━━━━━━━━━━━━━━━"""

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{order_id}"),
        types.InlineKeyboardButton("⚠️ Жалоба", callback_data=f"report_menu_{order_id}"),
        types.InlineKeyboardButton("📋 Заказать", callback_data=f"copy_order_{order_id}")
    )
    markup.add(
        types.InlineKeyboardButton("📢 Поделиться", callback_data=f"share_order_{order_id}"),
        types.InlineKeyboardButton("🔔 Уведомить", callback_data=f"subscribe_order_{order_id}")
    )
    markup.add(types.InlineKeyboardButton("▲ Свернуть", callback_data=f"orders_page_{page}"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML',
                              reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)

    bot.answer_callback_query(call.id)


# ========== ПОДЕЛИТЬСЯ ЗАКАЗОМ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('share_order_'))
def share_order_callback(call):
    order_id = int(call.data.split('_')[2])
    bot_name = bot.get_me().username
    link = f"https://t.me/{bot_name}?start=order_{order_id}"
    bot.answer_callback_query(call.id, f"Ссылка скопирована:\n{link}", show_alert=True)


# ========== ПОДПИСКА НА ЗАКАЗ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('subscribe_order_'))
def subscribe_order_callback(call):
    order_id = int(call.data.split('_')[2])
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT subscribers FROM orders WHERE order_id = ?", (order_id,))
    result = cursor.fetchone()

    if result:
        subscribers = result[0].split(',') if result[0] else []
        user_str = str(user_id)
        if user_str in subscribers:
            subscribers.remove(user_str)
            msg = "🔔 Вы отписались от уведомлений"
        else:
            subscribers.append(user_str)
            msg = "🔔 Вы подписались на уведомления!"

        cursor.execute("UPDATE orders SET subscribers = ? WHERE order_id = ?", (','.join(subscribers), order_id))
        conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, msg, show_alert=True)


# ========== КОПИРОВАТЬ ЗАКАЗ ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('copy_order_'))
def copy_order_callback(call):
    order_id = int(call.data.split('_')[2])

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT game_name FROM orders WHERE order_id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        user_states[call.message.chat.id] = {'state': 'waiting_size', 'game': result[0]}
        bot.send_message(call.message.chat.id,
                         f"📝 Копируем заказ: <b>{result[0]}</b>\n\nВведите размер в ГБ (только цифры):",
                         parse_mode='HTML')
        bot.answer_callback_query(call.id, "Введите размер игры")
    else:
        bot.answer_callback_query(call.id, "❌ Заказ не найден")


# ========== NEWORDER ==========
@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    if is_muted(message.from_user.id): bot.send_message(message.chat.id, "🔇 Вы не можете создавать заказы"); return

    user_states[message.chat.id] = {'state': 'waiting_game'}
    bot.send_message(message.chat.id, "📝 <b>НОВЫЙ ЗАКАЗ</b>\n\nВведите название игры:", parse_mode='HTML',
                     reply_markup=types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("Отмена", callback_data="cancel_order")))


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and user_states[m.chat.id].get('state') == 'waiting_game')
def get_game_name(message):
    if message.chat.type != 'private': return

    game_name = message.text.strip()

    # Проверка на запрещённые слова
    has_banned, banned_word = check_banned_words(game_name)
    if has_banned:
        user_id = message.from_user.id
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET banned_word_attempts = banned_word_attempts + 1, last_banned_attempt = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id))
        cursor.execute("SELECT banned_word_attempts FROM users WHERE user_id = ?", (user_id,))
        attempts = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        if attempts >= MAX_BANNED_WORD_ATTEMPTS:
            mute_until = (datetime.now() + timedelta(hours=24)).isoformat()
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_muted = 1, mute_until = ?, mute_reason = ?, banned_word_attempts = 0 WHERE user_id = ?",
                (mute_until, f"Запрещённое слово: {banned_word}", user_id))
            conn.commit()
            conn.close()
            del user_states[message.chat.id]
            bot.send_message(message.chat.id,
                             f"🔇 <b>Вы замучены на 24 часа!</b>\n\nПричина: {MAX_BANNED_WORD_ATTEMPTS} попытки использовать запрещённые слова.\nПоследнее: \"{banned_word}\"",
                             parse_mode='HTML')
            log_action(user_id, "auto_mute", f"3 banned word attempts: {banned_word}")
            return

        bot.send_message(message.chat.id,
                         f"❌ <b>Запрещённое слово:</b> \"{banned_word}\"\n⚠️ Попытка {attempts}/{MAX_BANNED_WORD_ATTEMPTS}\n\nПри {MAX_BANNED_WORD_ATTEMPTS} попытках — мут на 24 часа.",
                         parse_mode='HTML')
        return

    user_states[message.chat.id] = {'state': 'waiting_size', 'game': game_name}
    bot.send_message(message.chat.id, f"🎮 Игра: {game_name}\n\nВведите размер в ГБ (только цифры):", parse_mode='HTML')


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and isinstance(user_states[m.chat.id], dict) and user_states[
        m.chat.id].get('state') == 'waiting_size')
def get_game_size(message):
    if message.chat.type != 'private': return

    size_input = message.text.strip()

    if not re.match(r'^[\d.]+$', size_input):
        bot.send_message(message.chat.id, "❌ Только цифры!\nПример: 50 или 12.5\nПопробуйте ещё раз:",
                         parse_mode='HTML')
        return

    # Проверка размера на запрещённые слова
    has_banned, banned_word = check_banned_words(size_input)
    if has_banned:
        bot.send_message(message.chat.id, f"❌ <b>Запрещённое слово в размере:</b> \"{banned_word}\"", parse_mode='HTML')
        return

    data = user_states[message.chat.id]
    data['size'] = f"{size_input} ГБ"
    data['state'] = 'waiting_priority'

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔵 Обычный (бесплатно)", callback_data="priority_normal"),
        types.InlineKeyboardButton(f"🔴 Приоритет ({PRIORITY_COST} ⭐)", callback_data="priority_urgent")
    )
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel_order"))

    bot.send_message(message.chat.id,
                     f"🎮 {data['game']}\n💾 {data['size']}\n\n<b>Тип заказа:</b>\n🔵 Обычный — бесплатно\n🔴 Приоритет — {PRIORITY_COST} Stars (создаётся счёт)",
                     parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('priority_'))
def priority_choice(call):
    if call.message.chat.id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return

    data = user_states[call.message.chat.id]
    priority_type = call.data.split('_')[1]
    user_id = call.from_user.id

    if priority_type == 'urgent':
        prices = [types.LabeledPrice(f"Приоритет: {data['game'][:20]}", PRIORITY_COST)]
        try:
            bot.send_invoice(
                chat_id=call.message.chat.id,
                title="🔴 Приоритетный заказ",
                description=f"Игра: {data['game'][:50]}\nРазмер: {data['size']}",
                invoice_payload=f"priority_order_{user_id}",
                provider_token="",
                currency="XTR",
                prices=prices
            )
            bot.answer_callback_query(call.id, "✅ Счёт создан! Оплатите для продолжения.")
            data['state'] = 'waiting_payment'
            data['priority'] = True
            user_states[call.message.chat.id] = data
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
        except Exception as e:
            logger.error(f"Ошибка счёта: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка создания счёта")
    else:
        data['priority'] = False
        data['state'] = 'waiting_anonymous'
        user_states[call.message.chat.id] = data
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("👤 Открыто", callback_data="anon_no"),
                   types.InlineKeyboardButton("👻 Анонимно", callback_data="anon_yes"))
        bot.send_message(call.message.chat.id,
                         f"🎮 {data['game']}\n💾 {data['size']}\n🔵 Обычный\n\n<b>Опубликовать анонимно?</b>",
                         parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('anon_'))
def anonymous_choice(call):
    if call.message.chat.id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла");
        return

    data = user_states[call.message.chat.id]
    anonymous = call.data == 'anon_yes'
    priority = data.get('priority', False)
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, game_name, size, created_date, anonymous, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, data['game'], data['size'], datetime.now().isoformat(), 1 if anonymous else 0, 1 if priority else 0))
    order_id = cursor.lastrowid
    cursor.execute("UPDATE users SET created_orders = created_orders + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    del user_states[call.message.chat.id]
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    # Проверка ачивок
    check_and_award_achievement(user_id, 'first_order')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    if total >= 5: check_and_award_achievement(user_id, 'orders_5')
    if total >= 20: check_and_award_achievement(user_id, 'orders_20')

    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND priority = 1", (user_id,))
    if cursor.fetchone()[0] >= 10: check_and_award_achievement(user_id, 'priority_10')

    if anonymous:
        cursor.execute("SELECT anonymous FROM orders WHERE user_id = ? ORDER BY created_date DESC LIMIT 5", (user_id,))
        recent = [r[0] for r in cursor.fetchall()]
        if len(recent) >= 5 and all(r == 1 for r in recent):
            check_and_award_achievement(user_id, 'anonymous_5')
    conn.close()

    anon_text = "👻 Анонимно" if anonymous else "👤 Открыто"
    priority_text = "🔴 Приоритетный" if priority else "🔵 Обычный"

    text = f"""✅ <b>ЗАКАЗ #{order_id} СОЗДАН</b>
🎮 {data['game']}
💾 {data['size']}
{priority_text}
{anon_text}
Спасибо за заказ!"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Все заказы", callback_data="show_orders"))
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))

    bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)


# ========== MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, game_name, size, likes, status, created_date, anonymous, priority FROM orders WHERE user_id = ? ORDER BY created_date DESC LIMIT 10",
        (message.from_user.id,))
    user_orders = cursor.fetchall()
    conn.close()

    if not user_orders:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, "👤 <b>МОИ ЗАКАЗЫ</b>\n\n📭 У вас пока нет заказов.", parse_mode='HTML',
                         reply_markup=markup)
        return

    text = f"👤 <b>МОИ ЗАКАЗЫ</b> ({len(user_orders)})\n\n"
    for o in user_orders:
        order_id, game_name, size, likes, status, created_date, anonymous, priority = o
        text += f"{'🔴' if priority else '🔵'} <b>#{order_id}</b> | {game_name}\n💾 {size} | ❤️ {likes} | {'Активен' if status == 'active' else 'Завершён'}{' 👻' if anonymous else ''}\n━\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== РЕПОРТЫ ==========
@bot.message_handler(commands=['report'])
def report_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return

    try:
        parts = message.text.split(maxsplit=2)
        order_id, reason = int(parts[1]), parts[2] if len(parts) > 2 else "Без причины"
    except:
        bot.send_message(message.chat.id, "❌ /report ID причина\nПример: /report 5 Неверное описание");
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone(): bot.send_message(message.chat.id, f"❌ Заказ #{order_id} не найден"); conn.close(); return

    cursor.execute("SELECT report_id FROM order_reports WHERE order_id = ? AND reporter_id = ?",
                   (order_id, message.from_user.id))
    if cursor.fetchone(): bot.send_message(message.chat.id,
                                           f"❌ Вы уже жаловались на заказ #{order_id}"); conn.close(); return

    cursor.execute("INSERT INTO order_reports (order_id, reporter_id, reason, reported_date) VALUES (?, ?, ?, ?)",
                   (order_id, message.from_user.id, reason, datetime.now().isoformat()))

    # Проверка на автоудаление
    cursor.execute("SELECT COUNT(*) FROM order_reports WHERE order_id = ?", (order_id,))
    report_count = cursor.fetchone()[0]

    if report_count >= AUTO_DELETE_REPORTS:
        cursor.execute("SELECT user_id, game_name FROM orders WHERE order_id = ?", (order_id,))
        order_info = cursor.fetchone()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_likes WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_reports WHERE order_id = ?", (order_id,))

        if order_info:
            try:
                bot.send_message(order_info[0],
                                 f"📋 Ваш заказ <b>#{order_id}</b> ({order_info[1]}) был удалён из-за {AUTO_DELETE_REPORTS}+ жалоб.",
                                 parse_mode='HTML')
            except:
                pass

    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"⚠️ Жалоба на заказ #{order_id} отправлена\n📝 Причина: {reason}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('report_menu_'))
def report_menu_callback(call):
    order_id = int(call.data.split('_')[2])
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("❌ Неверное описание", callback_data=f"report_{order_id}_wrong_desc"),
        types.InlineKeyboardButton("🔞 Запрещённый контент", callback_data=f"report_{order_id}_illegal"),
        types.InlineKeyboardButton("🤖 Спам/Бот", callback_data=f"report_{order_id}_spam"),
        types.InlineKeyboardButton("📋 Другое", callback_data=f"report_{order_id}_other"),
        types.InlineKeyboardButton("« Назад", callback_data=f"orders_page_0")
    )
    bot.send_message(call.message.chat.id, f"⚠️ <b>ЖАЛОБА НА ЗАКАЗ #{order_id}</b>\n\nВыберите причину:",
                     parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('report_') and len(call.data.split('_')) == 3)
def report_reason_callback(call):
    parts = call.data.split('_')
    order_id, reason_type = int(parts[1]), parts[2]
    reasons = {'wrong_desc': 'Неверное описание', 'illegal': 'Запрещённый контент', 'spam': 'Спам/Бот',
               'other': 'Другое'}
    reason = reasons.get(reason_type, 'Другое')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT report_id FROM order_reports WHERE order_id = ? AND reporter_id = ?",
                   (order_id, call.from_user.id))
    if cursor.fetchone():
        bot.answer_callback_query(call.id, "❌ Вы уже жаловались", show_alert=True)
        conn.close()
        return

    cursor.execute("INSERT INTO order_reports (order_id, reporter_id, reason, reported_date) VALUES (?, ?, ?, ?)",
                   (order_id, call.from_user.id, reason, datetime.now().isoformat()))

    cursor.execute("SELECT COUNT(*) FROM order_reports WHERE order_id = ?", (order_id,))
    report_count = cursor.fetchone()[0]

    if report_count >= AUTO_DELETE_REPORTS:
        cursor.execute("SELECT user_id, game_name FROM orders WHERE order_id = ?", (order_id,))
        order_info = cursor.fetchone()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_likes WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_reports WHERE order_id = ?", (order_id,))
        if order_info:
            try:
                bot.send_message(order_info[0],
                                 f"📋 Ваш заказ #{order_id} ({order_info[1]}) удалён из-за {AUTO_DELETE_REPORTS}+ жалоб.",
                                 parse_mode='HTML')
            except:
                pass

    conn.commit()
    conn.close()

    try:
        bot.edit_message_text(f"✅ Жалоба на заказ #{order_id} отправлена\n📝 Причина: {reason}", call.message.chat.id,
                              call.message.message_id)
    except:
        pass

    bot.answer_callback_query(call.id, "✅ Жалоба отправлена!")


# ========== ПОИСК ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def search_handler(message):
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return

    query = message.text.strip()

    # Ищем в HQ
    results_hq = search_games(query, is_lq=False)

    # Ищем в LQ
    results_lq = search_games(query, is_lq=True)

    # Если точное совпадение в HQ
    if len(results_hq) == 1 and query.lower() == results_hq[0].lower():
        bot.send_message(message.chat.id,
                         f"🎮 {results_hq[0]}\n📦 Файлов: {len(GAMES_DATABASE[results_hq[0]])}\n⏳ Отправляю...",
                         parse_mode='HTML')
        send_game_files(message.chat.id, results_hq[0], message.from_user.id)
        return

    # Если точное совпадение в LQ
    if len(results_lq) == 1 and query.lower() == results_lq[0].lower():
        bot.send_message(message.chat.id,
                         f"🎮 {results_lq[0]} (LQ)\n📦 Файлов: {len(GAMES_LQ_DATABASE[results_lq[0]])}\n⏳ Отправляю...",
                         parse_mode='HTML')
        send_game_files(message.chat.id, results_lq[0], message.from_user.id, is_lq=True)
        return

    # Формируем результаты
    text = f"🔍 Результаты для \"{query}\":\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)

    if results_hq:
        text += "<b>🎮 HQ версии:</b>\n"
        for game in results_hq:
            markup.add(types.InlineKeyboardButton(f"📥 {game}", callback_data=f"play_{game}"))
            text += f"• {game}\n"

    if results_lq:
        text += "\n<b>💿 LQ версии:</b>\n"
        for game in results_lq:
            markup.add(types.InlineKeyboardButton(f"💿 {game} (LQ)", callback_data=f"playlq_{game}"))
            text += f"• {game}\n"

    if results_hq or results_lq:
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, f"❌ \"{query}\" не найдено\n📝 Создайте заказ через /neworder",
                         parse_mode='HTML', reply_markup=markup)


# ========== МОДЕРАЦИЯ ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if not is_admin(message.from_user.id): return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'active'")
    active_orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE priority = 1 AND status = 'active'")
    priority_orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM order_reports")
    total_reports = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM order_reports WHERE reported_date > ?",
                   ((datetime.now() - timedelta(days=1)).isoformat(),))
    new_reports = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM download_history WHERE download_date > ?",
                   (datetime.now().strftime("%Y-%m-%d"),))
    today_downloads = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(stars_donated) FROM users")
    total_stars = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_muted = 1")
    muted = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM admins")
    admin_count = cursor.fetchone()[0]
    conn.close()

    text = f"""🛡 <b>ПАНЕЛЬ МОДЕРАТОРА v9.0</b>

━━━━━━━━━━━━━━━━━━
📊 <b>СТАТИСТИКА</b>
━━━━━━━━━━━━━━━━━━
👥 Пользователей: {total_users}
👑 Админов: {admin_count}
📋 Активных заказов: {active_orders} (🔴{priority_orders} | 🔵{active_orders - priority_orders})
⚠️ Жалоб: {total_reports} (новых: {new_reports})
📥 Скачиваний сегодня: {today_downloads}
💰 Stars собрано: {total_stars}
🔨 Забанено: {banned} | 🔇 Замучено: {muted}

━━━━━━━━━━━━━━━━━━
⚡ <b>ДЕЙСТВИЯ</b>
━━━━━━━━━━━━━━━━━━
[⚠️ Жалобы] [📋 Заказы] [👥 Пользователи]
[🎮 Игры HQ] [💿 Игры LQ] [📊 Статистика]

━━━━━━━━━━━━━━━━━━
🔧 <b>КОМАНДЫ</b>
━━━━━━━━━━━━━━━━━━
/ban #ID время причина
/unban #ID
/mute #ID время причина
/unmute #ID
/addadmin #ID
/removeadmin #ID
/adminlist
/deleteorder ID причина
/addgame Название IDначала IDконца
/addgamelq Название IDначала IDконца
/addword слово
/removeword слово
/listwords
/broadcast текст
/stats — подробная статистика"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚠️ Жалобы", callback_data="admin_reports"),
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        types.InlineKeyboardButton("🎮 Игры HQ", callback_data="admin_games"),
        types.InlineKeyboardButton("💿 Игры LQ", callback_data="admin_games_lq"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    )

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== АДМИН: ДОБАВЛЕНИЕ ИГР ==========
@bot.message_handler(commands=['addgame'])
def add_game_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ /addgame Название IDначала IDконца\nПример: /addgame Cyberpunk 2005 2047")
            return

        end_id = int(parts[-1])
        start_id = int(parts[-2])
        name = ' '.join(parts[1:-2]).lower()

        file_ids = list(range(start_id, end_id + 1))

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO games (game_name, file_ids, downloads, added_date) VALUES (?, ?, ?, ?)",
                       (name, ','.join(map(str, file_ids)), 0, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        load_games_from_db()
        bot.reply_to(message,
                     f"✅ Игра <b>{name}</b> добавлена в HQ!\n📦 {len(file_ids)} файлов (ID {start_id}-{end_id})",
                     parse_mode='HTML')
        log_action(message.from_user.id, "add_game", f"{name}: {start_id}-{end_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=['addgamelq'])
def add_game_lq_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        parts = message.text.split()
        if len(parts) < 4:
            bot.reply_to(message, "❌ /addgamelq Название IDначала IDконца\nПример: /addgamelq Cyberpunk 2005 2047")
            return

        end_id = int(parts[-1])
        start_id = int(parts[-2])
        name = ' '.join(parts[1:-2]).lower()

        file_ids = list(range(start_id, end_id + 1))

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO games_lq (game_name, file_ids, downloads, added_date) VALUES (?, ?, ?, ?)",
            (name, ','.join(map(str, file_ids)), 0, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        load_games_from_db()
        bot.reply_to(message,
                     f"✅ Игра <b>{name}</b> добавлена в LQ!\n📦 {len(file_ids)} файлов (ID {start_id}-{end_id})",
                     parse_mode='HTML')
        log_action(message.from_user.id, "add_game_lq", f"{name}: {start_id}-{end_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# ========== АДМИН: УПРАВЛЕНИЕ АДМИНАМИ ==========
@bot.message_handler(commands=['addadmin'])
def addadmin_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        unique_id = message.text.split()[1].replace('#', '')
        target_user_id = get_user_by_unique_id(unique_id)

        if not target_user_id:
            bot.reply_to(message, f"❌ Пользователь #{unique_id} не найден")
            return

        if is_admin(target_user_id):
            bot.reply_to(message, f"❌ Пользователь #{unique_id} уже админ")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (target_user_id,))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ Пользователь #{unique_id} теперь админ!")
        log_action(message.from_user.id, "addadmin", unique_id)

        try:
            bot.send_message(target_user_id, "🎉 Вас назначили администратором бота!")
        except:
            pass
    except:
        bot.reply_to(message, "❌ /addadmin #ID")


@bot.message_handler(commands=['removeadmin'])
def removeadmin_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        unique_id = message.text.split()[1].replace('#', '')
        target_user_id = get_user_by_unique_id(unique_id)

        if not target_user_id:
            bot.reply_to(message, f"❌ Пользователь #{unique_id} не найден")
            return

        if target_user_id == 7885915159:
            bot.reply_to(message, "❌ Нельзя удалить создателя бота")
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admins WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ Пользователь #{unique_id} больше не админ")
        log_action(message.from_user.id, "removeadmin", unique_id)
    except:
        bot.reply_to(message, "❌ /removeadmin #ID")


@bot.message_handler(commands=['adminlist'])
def adminlist_cmd(message):
    if not is_admin(message.from_user.id): return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT a.user_id, u.username, u.first_name, u.unique_id FROM admins a LEFT JOIN users u ON a.user_id = u.user_id")
    admins = cursor.fetchall()
    conn.close()

    text = "👑 <b>СПИСОК АДМИНОВ</b>\n\n"
    for admin in admins:
        user_id, username, first_name, unique_id = admin
        name = f"@{username}" if username else first_name or f"#{unique_id}"
        text += f"• {name} — <code>#{unique_id}</code>\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== АДМИН: БАН/МУТ ПО ID ==========
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        parts = message.text.split(maxsplit=3)
        unique_id = parts[1].replace('#', '')
        duration = parts[2].lower()
        reason = parts[3] if len(parts) > 3 else "Без причины"

        target_user_id = get_user_by_unique_id(unique_id)
        if not target_user_id:
            bot.reply_to(message, f"❌ Пользователь #{unique_id} не найден")
            return

        if duration not in BAN_DURATIONS:
            bot.reply_to(message, f"❌ Неверное время! {', '.join(BAN_DURATIONS.keys())}")
            return

        ban_until = (datetime.now() + BAN_DURATIONS[duration]).isoformat() if BAN_DURATIONS[duration] else None

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 1, ban_until = ?, ban_reason = ? WHERE user_id = ?",
                       (ban_until, reason, target_user_id))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ #{unique_id} забанен на {duration}")
        try:
            bot.send_message(target_user_id, f"🚫 Вы заблокированы\n⏰ {duration}\n📝 {reason}", parse_mode='HTML')
        except:
            pass
        log_action(message.from_user.id, "ban", f"#{unique_id}, {duration}")
    except Exception as e:
        bot.reply_to(message, f"❌ /ban #ID время причина\nПример: /ban #862618 7d Спам")


@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        unique_id = message.text.split()[1].replace('#', '')
        target_user_id = get_user_by_unique_id(unique_id)
        if not target_user_id:
            bot.reply_to(message, f"❌ Пользователь #{unique_id} не найден")
            return

        unban_user(target_user_id)
        bot.reply_to(message, f"✅ #{unique_id} разбанен")
        try:
            bot.send_message(target_user_id, "✅ Вы разблокированы")
        except:
            pass
    except:
        bot.reply_to(message, "❌ /unban #ID")


@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        parts = message.text.split(maxsplit=3)
        unique_id = parts[1].replace('#', '')
        duration = parts[2].lower()
        reason = parts[3] if len(parts) > 3 else "Без причины"

        target_user_id = get_user_by_unique_id(unique_id)
        if not target_user_id:
            bot.reply_to(message, f"❌ Пользователь #{unique_id} не найден")
            return

        if duration not in MUTE_DURATIONS:
            bot.reply_to(message, f"❌ Неверное время! {', '.join(MUTE_DURATIONS.keys())}")
            return

        mute_until = (datetime.now() + MUTE_DURATIONS[duration]).isoformat()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_muted = 1, mute_until = ?, mute_reason = ? WHERE user_id = ?",
                       (mute_until, reason, target_user_id))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ #{unique_id} замучен на {duration}")
        try:
            bot.send_message(target_user_id, f"🔇 Вы замучены\n⏰ {duration}\n📝 {reason}", parse_mode='HTML')
        except:
            pass
        log_action(message.from_user.id, "mute", f"#{unique_id}, {duration}")
    except:
        bot.reply_to(message, "❌ /mute #ID время причина")


@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if not is_admin(message.from_user.id): return

    try:
        unique_id = message.text.split()[1].replace('#', '')
        target_user_id = get_user_by_unique_id(unique_id)
        if not target_user_id:
            bot.reply_to(message, f"❌ Пользователь #{unique_id} не найден")
            return

        unmute_user(target_user_id)
        bot.reply_to(message, f"✅ Мут снят с #{unique_id}")
        try:
            bot.send_message(target_user_id, "✅ Вы размучены")
        except:
            pass
    except:
        bot.reply_to(message, "❌ /unmute #ID")


# ========== АДМИН: УПРАВЛЕНИЕ СЛОВАМИ ==========
@bot.message_handler(commands=['addword'])
def addword_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        word = message.text.split(' ', 1)[1].lower()
        if word not in BANNED_WORDS:
            BANNED_WORDS.append(word)
            bot.reply_to(message, f"✅ Слово \"{word}\" добавлено в чёрный список")
        else:
            bot.reply_to(message, f"❌ Слово \"{word}\" уже в списке")
    except:
        bot.reply_to(message, "❌ /addword слово")


@bot.message_handler(commands=['removeword'])
def removeword_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        word = message.text.split(' ', 1)[1].lower()
        if word in BANNED_WORDS:
            BANNED_WORDS.remove(word)
            bot.reply_to(message, f"✅ Слово \"{word}\" удалено из списка")
        else:
            bot.reply_to(message, f"❌ Слово \"{word}\" не найдено")
    except:
        bot.reply_to(message, "❌ /removeword слово")


@bot.message_handler(commands=['listwords'])
def listwords_cmd(message):
    if not is_admin(message.from_user.id): return
    text = "📋 <b>ЗАПРЕЩЁННЫЕ СЛОВА</b>\n\n" + ", ".join(BANNED_WORDS)
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== АДМИН: РАССЫЛКА ==========
@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        text = message.text.split(' ', 1)[1]
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
        users = cursor.fetchall()
        conn.close()

        sent = 0
        for (uid,) in users:
            try:
                bot.send_message(uid, f"📢 {text}", parse_mode='HTML')
                sent += 1
                time.sleep(0.1)
            except:
                pass

        bot.reply_to(message, f"✅ Отправлено: {sent}/{len(users)}")
    except:
        bot.reply_to(message, "❌ /broadcast текст")


# ========== АДМИН: СТАТИСТИКА ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if not is_admin(message.from_user.id): return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # За 7 дней
    stats_text = "📊 <b>СТАТИСТИКА ЗА 7 ДНЕЙ</b>\n\n"
    for days_ago in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        cursor.execute("SELECT COUNT(*) FROM download_history WHERE download_date LIKE ?", (f"{date}%",))
        count = cursor.fetchone()[0]
        day_name = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'][(datetime.now() - timedelta(days=days_ago)).weekday()]
        bar = '█' * min(count, 20)
        stats_text += f"{day_name}: {bar} {count}\n"

    cursor.execute("SELECT COUNT(*) FROM orders WHERE created_date > ?",
                   ((datetime.now() - timedelta(days=7)).isoformat(),))
    new_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(stars_donated) FROM users")
    total_stars = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM games")
    hq_games = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM games_lq")
    lq_games = cursor.fetchone()[0]

    conn.close()

    stats_text += f"\n📋 Новых заказов: {new_orders}"
    stats_text += f"\n💰 Всего Stars: {total_stars}"
    stats_text += f"\n🎮 Игр HQ: {hq_games} | LQ: {lq_games}"

    bot.send_message(message.chat.id, stats_text, parse_mode='HTML')


# ========== АДМИН: CALLBACK-МЕНЮ ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_reports')
def admin_reports_callback(call):
    if not is_admin(call.from_user.id): return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT r.report_id, r.order_id, r.reporter_id, r.reason, r.reported_date, o.game_name FROM order_reports r JOIN orders o ON r.order_id = o.order_id ORDER BY r.reported_date DESC LIMIT 20")
    reports = cursor.fetchall()
    conn.close()

    if not reports:
        bot.send_message(call.message.chat.id, "📭 Нет жалоб")
        bot.answer_callback_query(call.id)
        return

    text = "⚠️ <b>ЖАЛОБЫ НА ЗАКАЗЫ</b>\n\n"
    for r in reports:
        report_id, order_id, reporter_id, reason, reported_date, game_name = r
        try:
            date_str = datetime.fromisoformat(reported_date).strftime("%d.%m %H:%M")
        except:
            date_str = "???"
        text += f"📋 #{order_id} | {game_name}\n👤 {reporter_id} | {reason}\n📅 {date_str}\n"
        text += f"[Удалить: /deleteorder {order_id}]\n━\n"

    bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'admin_users')
def admin_users_callback(call):
    if not is_admin(call.from_user.id): return
    users_cmd(call.message)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'admin_games')
def admin_games_callback(call):
    if not is_admin(call.from_user.id): return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, downloads, added_date FROM games ORDER BY downloads DESC LIMIT 20")
    games = cursor.fetchall()
    conn.close()

    text = "🎮 <b>ИГРЫ HQ</b> | /addgame Название IDначала IDконца\n\n"
    for game in games:
        name, dl, date = game
        try:
            date_str = datetime.fromisoformat(date).strftime("%d.%m.%Y")
        except:
            date_str = "неизв."
        text += f"• {name} — 📥 {dl} | 📅 {date_str}\n"

    bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'admin_games_lq')
def admin_games_lq_callback(call):
    if not is_admin(call.from_user.id): return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, downloads, added_date FROM games_lq ORDER BY downloads DESC LIMIT 20")
    games = cursor.fetchall()
    conn.close()

    text = "💿 <b>ИГРЫ LQ</b> | /addgamelq Название IDначала IDконца\n\n"
    for game in games:
        name, dl, date = game
        try:
            date_str = datetime.fromisoformat(date).strftime("%d.%m.%Y")
        except:
            date_str = "неизв."
        text += f"• {name} — 📥 {dl} | 📅 {date_str}\n"

    bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def admin_stats_callback(call):
    if not is_admin(call.from_user.id): return
    stats_cmd(call.message)
    bot.answer_callback_query(call.id)


# ========== ОСТАЛЬНЫЕ АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['deleteorder'])
def delete_order_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=2)
        order_id, reason = int(parts[1]), parts[2] if len(parts) > 2 else "Без причины"
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()
        if not order: bot.reply_to(message, f"❌ Заказ #{order_id} не найден"); conn.close(); return
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_likes WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_reports WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Заказ #{order_id} удалён")
        try:
            bot.send_message(order[0], f"📋 Ваш заказ #{order_id} удалён\nПричина: {reason}", parse_mode='HTML')
        except:
            pass
    except:
        bot.reply_to(message, "❌ /deleteorder ID причина")


@bot.message_handler(commands=['users'])
def users_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, username, first_name, unique_id, downloads, is_banned, is_muted FROM users ORDER BY downloads DESC LIMIT 20")
    users = cursor.fetchall()
    conn.close()
    text = "👥 <b>ТОП-20 ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
    for u in users:
        uid, username, fn, unique_id, dl, banned, muted = u
        name = f"@{username}" if username else fn or f"#{unique_id}"
        badge = "🚫" if banned else "🔇" if muted else ""
        text += f"{badge} {name} — {dl} скачиваний | <code>#{unique_id}</code>\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['userinfo'])
def userinfo_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        unique_id = message.text.split()[1].replace('#', '')
        target_user_id = get_user_by_unique_id(unique_id)
        if not target_user_id: bot.reply_to(message, f"❌ #{unique_id} не найден"); return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (target_user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user: bot.reply_to(message, "❌ Пользователь не найден"); return

        (uid, uq_id, username, fn, dl, orders, stars, first_seen, last_active, banned, ban_until, ban_reason, muted,
         mute_until, mute_reason, banned_word_attempts, last_banned_attempt, achievements) = user

        text = f"""👤 <b>ИНФО О ПОЛЬЗОВАТЕЛЕ #{uq_id}</b>
━━━━━━━━━━━━━━━━━━
👤 {fn or 'Н/Д'} (@{username or 'Н/Д'})
📊 Скачиваний: {dl} | Заказов: {orders} | Stars: {stars}
📅 Первый вход: {first_seen or 'Н/Д'}
🕐 Активность: {last_active or 'Н/Д'}
⚠️ Попыток banned слов: {banned_word_attempts}
━━━━━━━━━━━━━━━━━━
{'🚫 ЗАБАНЕН до ' + ban_until if banned else '✅ Не забанен'}
{f"📝 Причина: {ban_reason}" if ban_reason else ''}
{'🔇 ЗАМУЧЕН до ' + mute_until if muted else '✅ Не замучен'}
{f"📝 Причина: {mute_reason}" if mute_reason else ''}
━━━━━━━━━━━━━━━━━━
Бан: /ban #{uq_id} время причина
Мут: /mute #{uq_id} время причина"""

        bot.send_message(message.chat.id, text, parse_mode='HTML')
    except:
        bot.reply_to(message, "❌ /userinfo #ID")


# ========== CALLBACK ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data.startswith('like_'):
        if is_banned(user_id): bot.answer_callback_query(call.id, "❌ Вы заблокированы"); return
        order_id = int(call.data.split('_')[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM order_likes WHERE order_id = ? AND user_id = ?", (order_id, user_id))
        if cursor.fetchone(): bot.answer_callback_query(call.id, "❌ Вы уже лайкали"); conn.close(); return
        cursor.execute("INSERT INTO order_likes (order_id, user_id, liked_date) VALUES (?, ?, ?)",
                       (order_id, user_id, datetime.now().isoformat()))
        cursor.execute("UPDATE orders SET likes = likes + 1 WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()

        check_and_award_achievement(user_id, 'first_like')

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(likes) FROM orders WHERE user_id = ?", (user_id,))
        total_likes = cursor.fetchone()[0] or 0
        if total_likes >= 25: check_and_award_achievement(user_id, 'likes_25')
        if total_likes >= 100: check_and_award_achievement(user_id, 'likes_100')
        conn.close()

        bot.answer_callback_query(call.id, "❤️ Лайк поставлен!")

    elif call.data.startswith('play_'):
        game_name = call.data[5:]
        bot.answer_callback_query(call.id, f"⏳ Загружаю...")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_game_files(call.message.chat.id, game_name, user_id)

    elif call.data.startswith('playlq_'):
        game_name = call.data[7:]
        bot.answer_callback_query(call.id, f"⏳ Загружаю LQ...")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        send_game_files(call.message.chat.id, game_name, user_id, is_lq=True)

    elif call.data.startswith('orders_page_'):
        page = int(call.data.split('_')[2])
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_orders_page(call.message.chat.id, page, user_id)

    elif call.data.startswith('donate_'):
        amount = int(call.data.split('_')[1])
        prices = {10: [types.LabeledPrice("Поддержка", 10)], 20: [types.LabeledPrice("Поддержка", 20)],
                  30: [types.LabeledPrice("Поддержка", 30)], 40: [types.LabeledPrice("Поддержка", 40)],
                  50: [types.LabeledPrice("Поддержка", 50)], 100: [types.LabeledPrice("Поддержка", 100)]}
        try:
            bot.send_invoice(call.message.chat.id, "Поддержка Ferwes Games", f"Пожертвование {amount} Stars",
                             f"donate_{user_id}_{amount}", "", "XTR", prices[amount])
            bot.answer_callback_query(call.id, "✅ Счёт создан")
        except:
            bot.answer_callback_query(call.id, "❌ Ошибка")

    elif call.data == "show_donate":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_donate_menu(call.message.chat.id)

    elif call.data == "show_history":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_history(call.message.chat.id, user_id)

    elif call.data == "show_me":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_profile(call.message.chat.id, user_id)

    elif call.data in ["show_orders", "new_order", "my_orders", "show_help", "back_to_start"]:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        {"show_orders": orders_cmd, "new_order": neworder_cmd, "my_orders": myorders_cmd, "show_help": help_cmd,
         "back_to_start": start_cmd}[call.data](call.message)

    elif call.data == "cancel_order":
        if call.message.chat.id in user_states: del user_states[call.message.chat.id]
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(call.message.chat.id, "❌ Создание заказа отменено")
        start_cmd(call.message)

    elif call.data == "current_page":
        bot.answer_callback_query(call.id)


# ========== ОПЛАТА ==========
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout_handler(q): bot.answer_pre_checkout_query(q.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def payment_handler(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload

    if payload.startswith('priority_order_'):
        if user_id in user_states and user_states[user_id].get('state') == 'waiting_payment':
            data = user_states[user_id]
            data['state'] = 'waiting_anonymous'
            data['priority'] = True
            user_states[user_id] = data

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("👤 Открыто", callback_data="anon_no"),
                       types.InlineKeyboardButton("👻 Анонимно", callback_data="anon_yes"))
            bot.send_message(message.chat.id,
                             f"✅ Оплата получена!\n\n🎮 {data['game']}\n💾 {data['size']}\n🔴 Приоритетный\n\n<b>Опубликовать анонимно?</b>",
                             parse_mode='HTML', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "✅ Оплата получена, но сессия истекла. Создайте заказ заново.")

    elif payload.startswith('donate_'):
        try:
            amount = int(payload.split('_')[2])
        except:
            amount = 0
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET stars_donated = stars_donated + ? WHERE user_id = ?", (amount, user_id))

        # Проверка ачивок
        cursor.execute("SELECT stars_donated FROM users WHERE user_id = ?", (user_id,))
        total_stars = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        check_and_award_achievement(user_id, 'first_donate')
        if total_stars >= 500: check_and_award_achievement(user_id, 'donate_500')

        bot.send_message(message.chat.id,
                         f"✅ <b>СПАСИБО!</b>\n💰 Оплачено: {amount} Stars\n\nТеперь можно создать 🔴 приоритетный заказ!",
                         parse_mode='HTML')


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 FERWES GAMES BOT v9.0 'LEGENDARY'")
    print("=" * 60)
    print(f"🎮 Игр HQ: {len(GAMES_DATABASE)} | LQ: {len(GAMES_LQ_DATABASE)}")
    print("🔍 Fuzzy-поиск: ВКЛ")
    print("🏆 Ачивки: ВКЛ")
    print("🔴🔵 Приоритеты: через счёт Stars")
    print("⚠️ Репорты: ВКЛ (автоудаление при 15)")
    print("📜 История скачиваний: ВКЛ")
    print("🔢 Уникальные ID: ВКЛ")
    print("🛡 Модерация: бан/мут по #ID")
    print("👑 Управление админами: ВКЛ")
    print("🚫 Фильтр слов: ВКЛ (3 попытки = мут 24ч)")
    print("📋 Выпадающее меню заказов: ВКЛ")
    print("🔔 Подписка на заказы: ВКЛ")
    print("📢 Поделиться заказом: ВКЛ")
    print("💿 Базы HQ + LQ: ВКЛ")
    print("=" * 60)
    print("⚡ Бот запущен!")
    print("=" * 60)

    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        logger.critical(f"Ошибка: {e}")
        time.sleep(10)