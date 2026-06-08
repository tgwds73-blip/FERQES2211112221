import telebot
from telebot import types
import sqlite3
import os
import time
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

# ========== БАЗА ДАННЫХ ==========
DATA_DIR = os.getenv('DATA_DIR', '.')
DB_FILE = os.path.join(DATA_DIR, 'bot_database.db')


def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            downloads INTEGER DEFAULT 0, created_orders INTEGER DEFAULT 0,
            stars_donated INTEGER DEFAULT 0, first_seen TIMESTAMP, last_active TIMESTAMP,
            is_banned BOOLEAN DEFAULT 0, ban_until TIMESTAMP, ban_reason TEXT,
            is_muted BOOLEAN DEFAULT 0, mute_until TIMESTAMP, mute_reason TEXT
        )
    ''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    for col in ['ban_until', 'ban_reason', 'is_muted', 'mute_until', 'mute_reason']:
        if col not in columns:
            cursor.execute(
                f"ALTER TABLE users ADD COLUMN {col} {'TIMESTAMP' if 'until' in col else 'TEXT' if 'reason' in col else 'BOOLEAN DEFAULT 0'}")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            game_name TEXT, size TEXT, likes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active', priority BOOLEAN DEFAULT 0,
            created_date TIMESTAMP, anonymous BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'anonymous' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN anonymous BOOLEAN DEFAULT 0")
    if 'priority' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN priority BOOLEAN DEFAULT 0")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_likes (
            order_id INTEGER, user_id INTEGER, liked_date TIMESTAMP,
            PRIMARY KEY (order_id, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER, reporter_id INTEGER,
            reason TEXT, reported_date TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, game_name TEXT,
            file_count INTEGER, download_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS action_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, timestamp TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT, game_name TEXT UNIQUE,
            file_ids TEXT, downloads INTEGER DEFAULT 0, added_date TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            donation_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            stars_amount INTEGER, status TEXT DEFAULT 'pending',
            created_date TIMESTAMP, completed_date TIMESTAMP
        )
    ''')

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

# ========== БАЗА ИГР ==========
GAMES_DATABASE = {
    'antonblast': [913, 914],
    'assassins creed': list(range(1028, 1033)),
    'artmoney': [1770, 1771],
    'bad cheese': list(range(1651, 1654)),
    'batman legacy of the dark knight': list(range(1984, 2004)),
    'battlefield 3': list(range(1773, 1784)),
    'BeamNG drive': list(range(861, 873)),
    'beholder': list(range(823, 825)),
    'bendy and the ink machine': list(range(652, 654)),
    'bioshock remaster': list(range(1070, 1080)),
    'blender': list(range(1306, 1310)),
    'borderlands 2': list(range(776, 782)),
    'bully': list(range(1639, 1642)),
    'call of duty modern warfare 2': list(range(1212, 1221)),
    'call of duty ww2': list(range(521, 541)),
    'caves of qud': list(range(655, 657)),
    'chesscraft': list(range(1655, 1657)),
    'clair obscur: expedition 33': list(range(1552, 1575)),
    'construction simulator 4': list(range(1373, 1375)),
    'counter strike 1.6': list(range(1453, 1455)),
    'cry of fear': list(range(1481, 1486)),
    'cuphead': list(range(817, 821)),
    'cyberpunk 2077': list(range(658, 705)),
    'cybernetic fault': list(range(1938, 1941)),
    'dark souls remastered': list(range(1976, 1983)),
    'dark souls 3': list(range(880, 894)),
    'dead space': list(range(1576, 1580)),
    'dead space remake': list(range(1581, 1599)),
    'detroit become human': list(range(1407, 1436)),
    'devil may cry 4': list(range(1244, 1258)),
    'dispatch': list(range(1311, 1320)),
    'distant worlds 2': list(range(1644, 1650)),
    'doom the dark ages': list(range(1706, 1748)),
    'dying light: the beast': list(range(1502, 1525)),
    'elden ring': list(range(552, 587)),
    'endoparasitic': [1942, 1943],
    'fallout 3': list(range(1231, 1236)),
    'fallout 4': list(range(1277, 1296)),
    'far cry': list(range(1658, 1661)),
    'far cry 2': list(range(1662, 1665)),
    'far cry 3': list(range(783, 787)),
    'far cry 4': list(range(1354, 1369)),
    'far cry 5': list(range(242, 254)),
    'farm frenzy': list(range(1456, 1458)),
    'fifa 17': list(range(916, 931)),
    'finding frankie': list(range(622, 626)),
    'five nights at freddys': list(range(948, 950)),
    'five nights at freddys secret of the mimic': list(range(1462, 1473)),
    'fl studio 25': list(range(1153, 1156)),
    'forza horizon 5': list(range(1806, 1890)),
    'friday night funkin': list(range(748, 750)),
    'frostpunk': list(range(1222, 1228)),
    'frostpunk 2': list(range(1619, 1627)),
    'garrys mod': list(range(858, 860)),
    'ghost of tsushima': list(range(1527, 1551)),
    'ghostrunner': list(range(1692, 1701)),
    'goat simulator': list(range(618, 621)),
    'god of war': list(range(1787, 1805)),
    'Grand Theft Auto III': list(range(1088, 1090)),
    'Grand Theft Auto IV': list(range(799, 810)),
    'Grand Theft Auto V': list(range(705, 742)),
    'Grand Theft Auto: San Andreas': list(range(1259, 1270)),
    'Grand Theft Auto: Vice City': list(range(1450, 1452)),
    'half life 2': list(range(1207, 1211)),
    'hard time 3': list(range(1006, 1009)),
    'hatred': list(range(1667, 1669)),
    'hearts of iron 4': list(range(743, 747)),
    'hearts of iron 4: ultimate bundle': list(range(1497, 1501)),
    'hello neighbor 2': list(range(1891, 1896)),
    'hitman': list(range(962, 985)),
    'hitman blood money': list(range(951, 960)),
    'hollow knight': list(range(1060, 1062)),
    'hollow knight silksong': list(range(1600, 1602)),
    'hotline miami': list(range(1085, 1087)),
    'hotline miami 2': [1159, 1160],
    'humanit z': list(range(1096, 1110)),
    'hytale': list(range(1398, 1402)),
    'inscription': [1897],
    'jewel match': list(range(234, 236)),
    'korsary 3': list(range(1370, 1372)),
    'left 4 dead 2': list(range(1207, 1211)),
    'little nightmares 3': list(range(174, 182)),
    'lonarpg': list(range(1447, 1449)),
    'mafia 1': list(range(1241, 1243)),
    'mafia 2': list(range(942, 947)),
    'mafia: the old country': list(range(1954, 1975)),
    'metro 2033': list(range(1051, 1056)),
    'metro last light redux': list(range(1606, 1611)),
    'minecraft': list(range(932, 935)),
    'my gaming club': list(range(811, 813)),
    'my summer car': list(range(1441, 1443)),
    'my winter car': list(range(1347, 1349)),
    'miside': list(range(1057, 1059)),
    'nier automata': list(range(164, 173)),
    'nier replicant': list(range(1670, 1682)),
    'no im not a human': list(range(517, 520)),
    'no mans sky': list(range(1751, 1765)),
    'one shot': list(range(1065, 1069)),
    'orion sandbox': list(range(814, 816)),
    'palworld': list(range(202, 216)),
    'payday the heist': list(range(876, 879)),
    'people playground': list(range(1603, 1605)),
    'plants vs zombies': list(range(549, 551)),
    'portal 2': list(range(1207, 1211)),
    'portal knights': list(range(1237, 1239)),
    'postal 2': list(range(1615, 1617)),
    'postal 2 complete': list(range(2011, 2014)),
    'pragmata': list(range(1901, 1920)),
    'project zomboid': list(range(1093, 1095)),
    'prototype 1': list(range(895, 901)),
    'prototype 2': list(range(1044, 1050)),
    'quasimorph': list(range(589, 591)),
    'rauniot': list(range(1926, 1937)),
    'red dead redemption': list(range(542, 548)),
    'red dead redemption 2': list(range(428, 485)),
    'resident evil revelations 2': list(range(788, 798)),
    'resident evil village': list(range(826, 845)),
    'rimworld': list(range(1298, 1301)),
    'risk of rain 2': list(range(1612, 1614)),
    'rock star life simulator': list(range(184, 186)),
    'stalker call of pripyat': list(range(1922, 1925)),
    'stalker anomaly': list(range(1628, 1634)),
    'stalker shadow of chernobyl': list(range(1326, 1329)),
    'sally face': list(range(628, 632)),
    'scorn': list(range(217, 227)),
    'slim rancher': list(range(853, 857)),
    'slime rancher 2': list(range(1323, 1325)),
    'spider man remastered': list(range(486, 516)),
    'stray': list(range(936, 941)),
    'streets of rogue 2': list(range(1041, 1043)),
    'subnautica 2': list(range(1945, 1953)),
    'system shock 2 remaster': list(range(187, 192)),
    'swat 4': list(range(1766, 1769)),
    'teardown': list(range(906, 912)),
    'terraria': list(range(1459, 1461)),
    'the forest': list(range(633, 635)),
    'the last of us': list(range(1119, 1152)),
    'the long drive': list(range(1444, 1446)),
    'the spike': list(range(846, 852)),
    'the witcher 3': list(range(986, 1005)),
    'third crisis': list(range(1302, 1305)),
    'tomb raider 2013': list(range(1487, 1496)),
    'uber soldier': list(range(197, 201)),
    'undertale': list(range(1376, 1378)),
    'warhammer 40000 gladius relics of war': list(range(1702, 1705)),
    'watch dogs 2': list(range(1010, 1027)),
    'worldbox': list(range(1036, 1040)),
    'корсары 3': list(range(1370, 1372)),
    'arda launcher': list(range(1784, 1787)),
}

user_states = {}

# ========== БАННЕР С ЦИТИРОВАНИЕМ ==========
BANNER_TEXT = """<blockquote>🔥 <b>БЕЗ ВСТРОЕННЫХ ПРОГРАММ ИЛИ ВИРУСОВ</b>
🔥 <b><a href="https://t.me/FerwesGames">FERWES / GAMES</a></b>
🔥 <b><a href="https://t.me/addlist/AW1LBTA9xa45NDIy">FERWES / GRID</a></b></blockquote>"""


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
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
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, first_seen, last_active) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
    else:
        cursor.execute("UPDATE users SET last_active = ?, username = ?, first_name = ? WHERE user_id = ?",
                       (datetime.now().isoformat(), username, first_name, user_id))
    conn.commit()
    conn.close()
    return True


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


def send_game_files(chat_id, game_name, user_id=None):
    if game_name not in GAMES_DATABASE:
        return False
    file_ids = GAMES_DATABASE[game_name]
    try:
        for idx, file_id in enumerate(file_ids, 1):
            try:
                bot.copy_message(chat_id, GAMES_CHANNEL_ID, file_id)
                if idx % 10 == 0: time.sleep(0.3)
            except:
                pass
        bot.send_message(chat_id, BANNER_TEXT, parse_mode='HTML', disable_web_page_preview=True)
        if user_id:
            conn = sqlite3.connect(DB_FILE);
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))
            cursor.execute("UPDATE games SET downloads = downloads + 1 WHERE game_name = ?", (game_name,))
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO games (game_name, file_ids, downloads, added_date) VALUES (?, ?, ?, ?)",
                               (game_name, ','.join(map(str, file_ids)), 1, datetime.now().isoformat()))
            cursor.execute(
                "INSERT INTO download_history (user_id, game_name, file_count, download_date) VALUES (?, ?, ?, ?)",
                (user_id, game_name, len(file_ids), datetime.now().isoformat()))
            conn.commit();
            conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки {game_name}: {e}")
        bot.send_message(chat_id, "❌ Ошибка при отправке игры.")
        return False


def search_games(query):
    query = query.lower().strip()
    if query in GAMES_DATABASE: return [query]
    results = [g for g in GAMES_DATABASE if query in g or g in query]
    results.sort(key=lambda x: len(x))
    return results[:8]


# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private': return
    user = message.from_user
    get_or_create_user(user.id, user.username, user.first_name)
    if is_banned(user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    text = f"""Привет, {user.first_name or 'пользователь'}!

🔍 <b>Напиши название игры</b> — я найду и отправлю.

📋 /orders — заказы (🔴 приоритет, 🔵 обычный)
📝 /neworder — создать заказ
👤 /myorders — мои заказы
📜 /history — история скачиваний
💰 /donate — поддержать

💡 Нет игры? → /neworder
━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | ❓ /help"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📜 История", callback_data="show_history"),
        types.InlineKeyboardButton("💰 Поддержать", callback_data="show_donate"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    text = """ℹ️ <b>ПОМОЩЬ</b>
🔍 Напиши название игры — бот найдёт и отправит
📋 /orders — все заказы
📝 /neworder — создать заказ
👤 /myorders — мои заказы
📜 /history — история скачиваний
⚠️ /report ID причина — пожаловаться на заказ
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


# ========== ИСТОРИЯ СКАЧИВАНИЙ ==========
@bot.message_handler(commands=['history'])
def history_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute(
        "SELECT game_name, file_count, download_date FROM download_history WHERE user_id = ? ORDER BY download_date DESC LIMIT 20",
        (message.from_user.id,))
    history = cursor.fetchall();
    conn.close()
    if not history:
        markup = types.InlineKeyboardMarkup();
        markup.add(types.InlineKeyboardButton("🔍 Найти игру", callback_data="back_to_start"))
        bot.send_message(message.chat.id,
                         "📜 <b>ИСТОРИЯ СКАЧИВАНИЙ</b>\n\nУ вас пока нет скачиваний.\n\nНапишите название игры, чтобы начать!",
                         parse_mode='HTML', reply_markup=markup)
        return
    text = f"📜 <b>ИСТОРИЯ СКАЧИВАНИЙ</b> ({len(history)})\n\n"
    for game_name, file_count, download_date in history:
        try:
            date_str = datetime.fromisoformat(download_date).strftime("%d.%m.%Y %H:%M")
        except:
            date_str = "неизвестно"
        text += f"🎮 {game_name}\n📦 {file_count} файлов | 📅 {date_str}\n━\n"
    markup = types.InlineKeyboardMarkup();
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== ORDERS ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    show_orders_page(message.chat.id, 0, message.from_user.id)


def show_orders_page(chat_id, page=0, viewer_id=None):
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.game_name, o.size, o.likes, o.status, o.created_date, 
               o.anonymous, o.priority, u.username,
               (SELECT COUNT(*) FROM order_reports WHERE order_id = o.order_id) as report_count
        FROM orders o LEFT JOIN users u ON o.user_id = u.user_id 
        WHERE o.status = 'active' ORDER BY o.priority DESC, o.created_date DESC
    """)
    all_orders = cursor.fetchall();
    conn.close()
    if not all_orders:
        markup = types.InlineKeyboardMarkup();
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(chat_id, "📭 <b>Нет активных заказов</b>\n\nСтаньте первым, кто создаст заказ!",
                         parse_mode='HTML', reply_markup=markup)
        return
    orders_per_page = 5
    total_pages = (len(all_orders) + orders_per_page - 1) // orders_per_page
    if page >= total_pages: page = total_pages - 1
    if page < 0: page = 0
    start_idx = page * orders_per_page
    end_idx = min(start_idx + orders_per_page, len(all_orders))
    page_orders = all_orders[start_idx:end_idx]
    priority_count = sum(1 for o in all_orders if o[8] == 1 or o[8] == True)
    text = f"📋 <b>СТОЛ ЗАКАЗОВ</b>\n━━━━━━━━━━━━━━━━━━\n📊 Всего: {len(all_orders)} | 🔴 Приоритет: {priority_count} | 🔵 Обычных: {len(all_orders) - priority_count}\n📄 Страница {page + 1}/{total_pages}\n━━━━━━━━━━━━━━━━━━\n\n"
    for order in page_orders:
        order_id, user_id, game_name, size, likes, status, created_date, anonymous, priority, username, report_count = order
        try:
            date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y")
        except:
            date_str = "неизвестно"
        if priority == 1 or priority == True:
            priority_emoji, priority_text = "🔴", "ПРИОРИТЕТ"
        else:
            priority_emoji, priority_text = "🔵", "Обычный"
        author = "👤 Аноним" if anonymous else f"👤 @{username}" if username else f"👤 ID:{user_id}"
        report_badge = f" ⚠️{report_count}" if report_count > 0 else ""
        text += f"{priority_emoji} <b>#{order_id}</b> | 🎮 {game_name}\n{author} | 💾 {size}\n📅 {date_str} | ❤️ {likes} | {priority_text}{report_badge}\n━━━━━━━━━━━━━━━━━━\n"
    markup = types.InlineKeyboardMarkup(row_width=5)
    nav_buttons = []
    if page > 0: nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1: nav_buttons.append(
        types.InlineKeyboardButton("➡️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)
    for order in page_orders[:3]:
        markup.add(types.InlineKeyboardButton(f"❤️ #{order[0]}", callback_data=f"like_{order[0]}"))
    for order in page_orders[:2]:
        markup.add(types.InlineKeyboardButton(f"⚠️ РЕПОРТ #{order[0]}", callback_data=f"report_menu_{order[0]}"))
    markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"),
               types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"))
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))
    try:
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
    except:
        bot.send_message(chat_id, re.sub(r'<[^>]+>', '', text), reply_markup=markup)


# ========== РЕПОРТЫ ==========
@bot.message_handler(commands=['report'])
def report_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    try:
        parts = message.text.split(maxsplit=2)
        order_id, reason = int(parts[1]), parts[2] if len(parts) > 2 else "Без причины"
    except:
        bot.send_message(message.chat.id,
                         "❌ Использование: /report ID причина\nПример: /report 5 Неверное описание"); return
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone(): bot.send_message(message.chat.id, f"❌ Заказ #{order_id} не найден"); conn.close(); return
    cursor.execute("SELECT report_id FROM order_reports WHERE order_id = ? AND reporter_id = ?",
                   (order_id, message.from_user.id))
    if cursor.fetchone(): bot.send_message(message.chat.id,
                                           f"❌ Вы уже жаловались на заказ #{order_id}"); conn.close(); return
    cursor.execute("INSERT INTO order_reports (order_id, reporter_id, reason, reported_date) VALUES (?, ?, ?, ?)",
                   (order_id, message.from_user.id, reason, datetime.now().isoformat()))
    conn.commit();
    conn.close()
    bot.send_message(message.chat.id,
                     f"⚠️ Жалоба на заказ #{order_id} отправлена\n📝 Причина: {reason}\n\nАдминистрация рассмотрит её.")


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
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute("SELECT report_id FROM order_reports WHERE order_id = ? AND reporter_id = ?",
                   (order_id, call.from_user.id))
    if cursor.fetchone(): bot.answer_callback_query(call.id, "❌ Вы уже жаловались на этот заказ",
                                                    show_alert=True); conn.close(); return
    cursor.execute("INSERT INTO order_reports (order_id, reporter_id, reason, reported_date) VALUES (?, ?, ?, ?)",
                   (order_id, call.from_user.id, reason, datetime.now().isoformat()))
    conn.commit();
    conn.close()
    try:
        bot.edit_message_text(
            f"✅ Жалоба на заказ #{order_id} отправлена\n📝 Причина: {reason}\n\nАдминистрация рассмотрит её.",
            call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id, "✅ Жалоба отправлена!")


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
    user_states[message.chat.id] = {'state': 'waiting_size', 'game': message.text.strip()}
    bot.send_message(message.chat.id, f"🎮 Игра: {message.text.strip()}\n\nВведите размер в ГБ (только цифры):",
                     parse_mode='HTML')


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and isinstance(user_states[m.chat.id], dict) and user_states[
        m.chat.id].get('state') == 'waiting_size')
def get_game_size(message):
    if message.chat.type != 'private': return
    if not re.match(r'^[\d.]+$', message.text.strip()):
        bot.send_message(message.chat.id, "❌ Только цифры!\nПример: 50 или 12.5\nПопробуйте ещё раз:",
                         parse_mode='HTML')
        return
    data = user_states[message.chat.id]
    data['size'] = f"{message.text.strip()} ГБ"
    data['state'] = 'waiting_priority'
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🔵 Обычный (бесплатно)", callback_data="priority_normal"),
               types.InlineKeyboardButton(f"🔴 Приоритет ({PRIORITY_COST} ⭐)", callback_data="priority_urgent"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel_order"))
    bot.send_message(message.chat.id,
                     f"🎮 {data['game']}\n💾 {data['size']}\n\n<b>Тип заказа:</b>\n🔵 Обычный — бесплатно\n🔴 Приоритет — {PRIORITY_COST} Stars (создаётся счёт на оплату)",
                     parse_mode='HTML', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('priority_'))
def priority_choice(call):
    if call.message.chat.id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла");
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return

    data = user_states[call.message.chat.id]
    priority_type = call.data.split('_')[1]
    user_id = call.from_user.id

    if priority_type == 'urgent':
        # Создаём счёт на оплату приоритетного заказа
        prices = [types.LabeledPrice(f"Приоритетный заказ: {data['game'][:20]}", PRIORITY_COST)]
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
            logger.error(f"Ошибка создания счёта: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка создания счёта. Попробуйте позже.")
    else:
        # Обычный заказ
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
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, game_name, size, created_date, anonymous, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (call.from_user.id, data['game'], data['size'], datetime.now().isoformat(), 1 if anonymous else 0,
         1 if priority else 0))
    order_id = cursor.lastrowid
    cursor.execute("UPDATE users SET created_orders = created_orders + 1 WHERE user_id = ?", (call.from_user.id,))
    conn.commit();
    conn.close()
    del user_states[call.message.chat.id]
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    text = f"""✅ <b>ЗАКАЗ #{order_id} СОЗДАН</b>
🎮 {data['game']}
💾 {data['size']}
{'🔴 Приоритетный' if priority else '🔵 Обычный'}
{'👻 Анонимно' if anonymous else '👤 Открыто'}
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
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, game_name, size, likes, status, created_date, anonymous, priority FROM orders WHERE user_id = ? ORDER BY created_date DESC LIMIT 10",
        (message.from_user.id,))
    user_orders = cursor.fetchall();
    conn.close()
    if not user_orders:
        markup = types.InlineKeyboardMarkup();
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, "👤 <b>МОИ ЗАКАЗЫ</b>\n\n📭 У вас пока нет заказов.", parse_mode='HTML',
                         reply_markup=markup);
        return
    text = f"👤 <b>МОИ ЗАКАЗЫ</b> ({len(user_orders)})\n\n"
    for o in user_orders:
        order_id, game_name, size, likes, status, created_date, anonymous, priority = o
        text += f"{'🔴' if priority else '🔵'} <b>#{order_id}</b> | {game_name}\n💾 {size} | ❤️ {likes} | {'Активен' if status == 'active' else 'Завершён'}{' 👻' if anonymous else ''}\n━\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== ПОИСК ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def search_handler(message):
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    query = message.text.strip()
    results = search_games(query)
    if len(results) == 1 and query.lower() == results[0].lower():
        bot.send_message(message.chat.id,
                         f"🎮 {results[0]}\n📦 Файлов: {len(GAMES_DATABASE[results[0]])}\n⏳ Отправляю...",
                         parse_mode='HTML')
        send_game_files(message.chat.id, results[0], message.from_user.id)
    elif results:
        text = f"🔍 Результаты для \"{query}\":\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for game in results: markup.add(types.InlineKeyboardButton(f"📥 {game}", callback_data=f"play_{game}"))
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, text + '\n'.join(f"{i + 1}. {g}" for i, g in enumerate(results)),
                         parse_mode='HTML', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup();
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, f"❌ \"{query}\" не найдено\n📝 Создайте заказ через /neworder",
                         parse_mode='HTML', reply_markup=markup)


# ========== МОДЕРАЦИЯ ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if not is_admin(message.from_user.id): return
    text = f"""🛡 <b>ПАНЕЛЬ МОДЕРАТОРА</b>
/ban ID время причина — Забанить ({', '.join(BAN_DURATIONS.keys())})
/unban ID — Разбанить
/mute ID время причина — Замутить ({', '.join(MUTE_DURATIONS.keys())})
/unmute ID — Размутить
/deleteorder ID причина — Удалить заказ
/reports — Список жалоб
/users — Список пользователей
/userinfo ID — Инфо о пользователе"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['reports'])
def reports_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute(
        "SELECT r.report_id, r.order_id, r.reporter_id, r.reason, r.reported_date, o.game_name FROM order_reports r JOIN orders o ON r.order_id = o.order_id ORDER BY r.reported_date DESC LIMIT 20")
    reports = cursor.fetchall();
    conn.close()
    if not reports: bot.send_message(message.chat.id, "📭 Нет жалоб"); return
    text = "⚠️ <b>ЖАЛОБЫ НА ЗАКАЗЫ</b>\n\n"
    for r in reports:
        report_id, order_id, reporter_id, reason, reported_date, game_name = r
        try:
            date_str = datetime.fromisoformat(reported_date).strftime("%d.%m %H:%M")
        except:
            date_str = "???"
        text += f"📋 #{order_id} | 🎮 {game_name}\n👤 Жалоба от: {reporter_id}\n📝 {reason} | 📅 {date_str}\n━\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=3)
        target_id, duration, reason = int(parts[1]), parts[2].lower(), parts[3] if len(parts) > 3 else "Без причины"
        if duration not in BAN_DURATIONS: bot.send_message(message.chat.id,
                                                           f"❌ Неверное время! {', '.join(BAN_DURATIONS.keys())}"); return
        ban_until = (datetime.now() + BAN_DURATIONS[duration]).isoformat() if BAN_DURATIONS[duration] else None
        conn = sqlite3.connect(DB_FILE);
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 1, ban_until = ?, ban_reason = ? WHERE user_id = ?",
                       (ban_until, reason, target_id))
        conn.commit();
        conn.close()
        bot.reply_to(message, f"✅ {target_id} забанен на {duration}")
        try:
            bot.send_message(target_id, f"🚫 Вы заблокированы\n⏰ {duration}\n📝 {reason}", parse_mode='HTML')
        except:
            pass
    except:
        bot.reply_to(message, "❌ /ban ID время причина")


@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target_id = int(message.text.split()[1])
        unban_user(target_id)
        bot.reply_to(message, f"✅ {target_id} разбанен")
        try:
            bot.send_message(target_id, "✅ Вы разблокированы")
        except:
            pass
    except:
        bot.reply_to(message, "❌ /unban ID")


@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=3)
        target_id, duration, reason = int(parts[1]), parts[2].lower(), parts[3] if len(parts) > 3 else "Без причины"
        if duration not in MUTE_DURATIONS: bot.send_message(message.chat.id,
                                                            f"❌ Неверное время! {', '.join(MUTE_DURATIONS.keys())}"); return
        mute_until = (datetime.now() + MUTE_DURATIONS[duration]).isoformat()
        conn = sqlite3.connect(DB_FILE);
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_muted = 1, mute_until = ?, mute_reason = ? WHERE user_id = ?",
                       (mute_until, reason, target_id))
        conn.commit();
        conn.close()
        bot.reply_to(message, f"✅ {target_id} замучен на {duration}")
        try:
            bot.send_message(target_id, f"🔇 Вы замучены\n⏰ {duration}\n📝 {reason}", parse_mode='HTML')
        except:
            pass
    except:
        bot.reply_to(message, "❌ /mute ID время причина")


@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target_id = int(message.text.split()[1])
        unmute_user(target_id)
        bot.reply_to(message, f"✅ Мут снят с {target_id}")
        try:
            bot.send_message(target_id, "✅ Вы размучены")
        except:
            pass
    except:
        bot.reply_to(message, "❌ /unmute ID")


@bot.message_handler(commands=['deleteorder'])
def delete_order_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=2)
        order_id, reason = int(parts[1]), parts[2] if len(parts) > 2 else "Без причины"
        conn = sqlite3.connect(DB_FILE);
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
        order = cursor.fetchone()
        if not order: bot.reply_to(message, f"❌ Заказ #{order_id} не найден"); conn.close(); return
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_likes WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_reports WHERE order_id = ?", (order_id,))
        conn.commit();
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
    conn = sqlite3.connect(DB_FILE);
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, username, first_name, downloads, is_banned, is_muted FROM users ORDER BY downloads DESC LIMIT 20")
    users = cursor.fetchall();
    conn.close()
    text = "👥 <b>ТОП-20 ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
    for u in users:
        uid, username, fn, dl, banned, muted = u
        name = f"@{username}" if username else fn or f"ID:{uid}"
        badge = "🚫" if banned else "🔇" if muted else ""
        text += f"{badge} {name} — {dl} скачиваний\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['userinfo'])
def userinfo_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE);
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone();
        conn.close()
        if not user: bot.reply_to(message, "❌ Пользователь не найден"); return
        (uid, username, fn, dl, orders, stars, first_seen, last_active, banned, ban_until, ban_reason, muted,
         mute_until, mute_reason) = user
        text = f"""👤 <b>ИНФО О ПОЛЬЗОВАТЕЛЕ</b>
🆔 {uid}
👤 {fn or 'Н/Д'} (@{username or 'Н/Д'})
📊 Скачиваний: {dl} | Заказов: {orders} | Stars: {stars}
📅 Первый вход: {first_seen or 'Н/Д'}
🕐 Активность: {last_active or 'Н/Д'}
{'🚫 ЗАБАНЕН до ' + ban_until if banned else '✅ Не забанен'}
{'🔇 ЗАМУЧЕН до ' + mute_until if muted else '✅ Не замучен'}"""
        bot.send_message(message.chat.id, text, parse_mode='HTML')
    except:
        bot.reply_to(message, "❌ /userinfo ID")


# ========== CALLBACK ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data.startswith('like_'):
        if is_banned(user_id): bot.answer_callback_query(call.id, "❌ Вы заблокированы"); return
        order_id = int(call.data.split('_')[1])
        conn = sqlite3.connect(DB_FILE);
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM order_likes WHERE order_id = ? AND user_id = ?", (order_id, user_id))
        if cursor.fetchone(): bot.answer_callback_query(call.id, "❌ Вы уже лайкали"); conn.close(); return
        cursor.execute("INSERT INTO order_likes (order_id, user_id, liked_date) VALUES (?, ?, ?)",
                       (order_id, user_id, datetime.now().isoformat()))
        cursor.execute("UPDATE orders SET likes = likes + 1 WHERE order_id = ?", (order_id,))
        conn.commit();
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
        history_cmd(call.message)

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
        # Оплачен приоритетный заказ — создаём его
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
        conn = sqlite3.connect(DB_FILE);
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET stars_donated = stars_donated + ? WHERE user_id = ?", (amount, user_id))
        conn.commit();
        conn.close()
        bot.send_message(message.chat.id,
                         f"✅ <b>СПАСИБО!</b>\n💰 Оплачено: {amount} Stars\n\nТеперь можно создать 🔴 приоритетный заказ!",
                         parse_mode='HTML')


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 FERWES GAMES BOT v8.5")
    print("=" * 50)
    print(f"🎮 Игр: {len(GAMES_DATABASE)}")
    print("🔴🔵 Приоритеты: через счёт Stars")
    print("⚠️ Репорты: ВКЛ")
    print("📜 История скачиваний: ВКЛ")
    print("🛡 Модерация: ВКЛ")
    print("💬 Баннер: цитирование")
    print("=" * 50)
    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        logger.critical(f"Ошибка: {e}")
        time.sleep(10)