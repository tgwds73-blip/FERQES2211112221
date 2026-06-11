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

BAN_DURATIONS = {'1h': timedelta(hours=1), '6h': timedelta(hours=6), '12h': timedelta(hours=12),
                 '1d': timedelta(days=1), '3d': timedelta(days=3), '7d': timedelta(days=7), '30d': timedelta(days=30),
                 'forever': None}
MUTE_DURATIONS = {'1h': timedelta(hours=1), '6h': timedelta(hours=6), '12h': timedelta(hours=12),
                  '1d': timedelta(days=1), '3d': timedelta(days=3), '7d': timedelta(days=7)}
PRIORITY_COST = 50
ORDER_EXPIRE_DAYS = 70
AUTO_DELETE_REPORTS = 15
MAX_BANNED_WORD_ATTEMPTS = 3

BANNED_WORDS = ['продам', 'продаю', 'куплю', 'купить', 'цена', 'недорого', 'реклама', 'пиар', 'накрутка', 'подписчики',
                'buy', 'price', 'cheap', 'spam', 'http', 'https', 'www', '.com', '.ru', 'telegram', 't.me', 'vk.com',
                'discord', 'whatsapp', 'пишите', 'звоните', 'сука', 'бля', 'блять', 'блядь', 'хуй', 'пизда', 'ебать',
                'нахуй', 'fuck', 'shit', 'bitch', 'казино', 'ставки', 'заработок', 'схема', 'лохотрон', 'casino', 'bet',
                'scam', 'нарко', 'трава', 'закладка', 'клад', 'weed', 'drugs']

# ========== БАЗА ДАННЫХ ==========
DATA_DIR = os.getenv('DATA_DIR', '.')
DB_FILE = os.path.join(DATA_DIR, 'bot_database.db')


def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

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
            last_banned_attempt TIMESTAMP
        )
    ''')

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
            subscribers TEXT DEFAULT ''
        )
    ''')

    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS order_likes (order_id INTEGER, user_id INTEGER, liked_date TIMESTAMP, PRIMARY KEY (order_id, user_id))''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS order_reports (report_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, reporter_id INTEGER, reason TEXT, reported_date TIMESTAMP)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS download_history (history_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, game_name TEXT, file_count INTEGER, download_date TIMESTAMP)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS user_achievements (achievement_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, achievement_key TEXT, achievement_name TEXT, earned_date TIMESTAMP)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS games_lq (game_id INTEGER PRIMARY KEY AUTOINCREMENT, game_name TEXT UNIQUE, file_ids TEXT, downloads INTEGER DEFAULT 0, added_date TIMESTAMP)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS action_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, timestamp TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS donations (donation_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, stars_amount INTEGER, status TEXT DEFAULT 'pending', created_date TIMESTAMP, completed_date TIMESTAMP)''')

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


# Удаляем старую БД и создаём новую (чистую)
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    logger.info("Старая БД удалена")

init_database()


def init_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (7885915159,))
    conn.commit()
    conn.close()


init_admin()

# ========== ВСЕ ИГРЫ (ЗАГРУЗКА В LQ) ==========
ALL_GAMES = {
    'antonblast': [913, 914], 'assassins creed': list(range(1028, 1033)), 'artmoney': [1770, 1771],
    'bad cheese': list(range(1651, 1654)), 'batman legacy of the dark knight': list(range(1984, 2004)),
    'battlefield 3': list(range(1773, 1784)), 'BeamNG drive': list(range(861, 873)),
    'beholder': list(range(823, 825)), 'bendy and the ink machine': list(range(652, 654)),
    'bioshock remaster': list(range(1070, 1080)), 'blender': list(range(1306, 1310)),
    'borderlands 2': list(range(776, 782)), 'bully': list(range(1639, 1642)),
    'call of duty modern warfare 2': list(range(1212, 1221)), 'call of duty ww2': list(range(521, 541)),
    'caves of qud': list(range(655, 657)), 'chesscraft': list(range(1655, 1657)),
    'clair obscur: expedition 33': list(range(1552, 1575)), 'construction simulator 4': list(range(1373, 1375)),
    'counter strike 1.6': list(range(1453, 1455)), 'cry of fear': list(range(1481, 1486)),
    'cuphead': list(range(817, 821)), 'cyberpunk 2077': list(range(658, 705)),
    'cybernetic fault': list(range(1938, 1941)), 'dark souls remastered': list(range(1976, 1983)),
    'dark souls 3': list(range(880, 894)), 'dead space': list(range(1576, 1580)),
    'dead space remake': list(range(1581, 1599)), 'detroit become human': list(range(1407, 1436)),
    'devil may cry 4': list(range(1244, 1258)), 'dispatch': list(range(1311, 1320)),
    'distant worlds 2': list(range(1644, 1650)), 'doom the dark ages': list(range(1706, 1748)),
    'dying light: the beast': list(range(1502, 1525)), 'elden ring': list(range(552, 587)),
    'endoparasitic': [1942, 1943], 'fallout 3': list(range(1231, 1236)),
    'fallout 4': list(range(1277, 1296)), 'far cry': list(range(1658, 1661)),
    'far cry 2': list(range(1662, 1665)), 'far cry 3': list(range(783, 787)),
    'far cry 4': list(range(1354, 1369)), 'far cry 5': list(range(242, 254)),
    'farm frenzy': list(range(1456, 1458)), 'fifa 17': list(range(916, 931)),
    'finding frankie': list(range(622, 626)), 'five nights at freddys': list(range(948, 950)),
    'five nights at freddys secret of the mimic': list(range(1462, 1473)), 'fl studio 25': list(range(1153, 1156)),
    'forza horizon 5': list(range(1806, 1890)), 'friday night funkin': list(range(748, 750)),
    'frostpunk': list(range(1222, 1228)), 'frostpunk 2': list(range(1619, 1627)),
    'garrys mod': list(range(858, 860)), 'ghost of tsushima': list(range(1527, 1551)),
    'ghostrunner': list(range(1692, 1701)), 'goat simulator': list(range(618, 621)),
    'god of war': list(range(1787, 1805)), 'Grand Theft Auto III': list(range(1088, 1090)),
    'Grand Theft Auto IV': list(range(799, 810)), 'Grand Theft Auto V': list(range(705, 742)),
    'Grand Theft Auto: San Andreas': list(range(1259, 1270)), 'Grand Theft Auto: Vice City': list(range(1450, 1452)),
    'half life 2': list(range(1207, 1211)), 'hard time 3': list(range(1006, 1009)),
    'hatred': list(range(1667, 1669)), 'hearts of iron 4': list(range(743, 747)),
    'hearts of iron 4: ultimate bundle': list(range(1497, 1501)), 'hello neighbor 2': list(range(1891, 1896)),
    'hitman': list(range(962, 985)), 'hitman blood money': list(range(951, 960)),
    'hollow knight': list(range(1060, 1062)), 'hollow knight silksong': list(range(1600, 1602)),
    'hotline miami': list(range(1085, 1087)), 'hotline miami 2': [1159, 1160],
    'humanit z': list(range(1096, 1110)), 'hytale': list(range(1398, 1402)),
    'inscription': [1897], 'jewel match': list(range(234, 236)), 'korsary 3': list(range(1370, 1372)),
    'left 4 dead 2': list(range(1207, 1211)), 'little nightmares 3': list(range(174, 182)),
    'lonarpg': list(range(1447, 1449)), 'mafia 1': list(range(1241, 1243)),
    'mafia 2': list(range(942, 947)), 'mafia: the old country': list(range(1954, 1975)),
    'metro 2033': list(range(1051, 1056)), 'metro last light redux': list(range(1606, 1611)),
    'minecraft': list(range(932, 935)), 'my gaming club': list(range(811, 813)),
    'my summer car': list(range(1441, 1443)), 'my winter car': list(range(1347, 1349)),
    'miside': list(range(1057, 1059)), 'nier automata': list(range(164, 173)),
    'nier replicant': list(range(1670, 1682)), 'no im not a human': list(range(517, 520)),
    'no mans sky': list(range(1751, 1765)), 'one shot': list(range(1065, 1069)),
    'orion sandbox': list(range(814, 816)), 'palworld': list(range(202, 216)),
    'payday the heist': list(range(876, 879)), 'people playground': list(range(1603, 1605)),
    'plants vs zombies': list(range(549, 551)), 'Half Life 2': list(range(1207, 1211)),
    'portal knights': list(range(1237, 1239)), 'postal 2': list(range(1615, 1617)),
    'postal 2 complete': list(range(2011, 2014)), 'pragmata': list(range(1901, 1920)),
    'project zomboid': list(range(1093, 1095)), 'prototype 1': list(range(895, 901)),
    'prototype 2': list(range(1044, 1050)), 'quasimorph': list(range(589, 591)),
    'rauniot': list(range(1926, 1937)), 'red dead redemption': list(range(542, 548)),
    'red dead redemption 2': list(range(428, 485)), 'resident evil revelations 2': list(range(788, 798)),
    'resident evil village': list(range(826, 845)), 'rimworld': list(range(1298, 1301)),
    'risk of rain 2': list(range(1612, 1614)), 'rock star life simulator': list(range(184, 186)),
    'stalker call of pripyat': list(range(1922, 1925)), 'stalker anomaly': list(range(1628, 1634)),
    'stalker shadow of chernobyl': list(range(1326, 1329)), 'sally face': list(range(628, 632)),
    'scorn': list(range(217, 227)), 'slim rancher': list(range(853, 857)),
    'slime rancher 2': list(range(1323, 1325)), 'spider man remastered': list(range(486, 516)),
    'stray': list(range(936, 941)), 'streets of rogue 2': list(range(1041, 1043)),
    'subnautica 2': list(range(1945, 1953)), 'system shock 2 remaster': list(range(187, 192)),
    'swat 4': list(range(1766, 1769)), 'teardown': list(range(906, 912)),
    'terraria': list(range(1459, 1461)), 'the forest': list(range(633, 635)),
    'the last of us': list(range(1119, 1152)), 'the long drive': list(range(1444, 1446)),
    'the spike': list(range(846, 852)), 'the witcher 3': list(range(986, 1005)),
    'third crisis': list(range(1302, 1305)), 'tomb raider 2013': list(range(1487, 1496)),
    'uber soldier': list(range(197, 201)), 'undertale': list(range(1376, 1378)),
    'warhammer 40000 gladius relics of war': list(range(1702, 1705)), 'watch dogs 2': list(range(1010, 1027)),
    'worldbox': list(range(1036, 1040)), 'корсары 3': list(range(1370, 1372)),
    'arda launcher': list(range(1784, 1787)),
}


def load_games_to_lq():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for name, file_ids in ALL_GAMES.items():
        cursor.execute(
            "INSERT OR REPLACE INTO games_lq (game_name, file_ids, downloads, added_date) VALUES (?, ?, ?, ?)",
            (name, ','.join(map(str, file_ids)), 0, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.info(f"Загружено {len(ALL_GAMES)} игр в LQ")


load_games_to_lq()

# Загружаем игры из БД в память
GAMES_LQ = {}


def load_games_from_db():
    global GAMES_LQ
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, file_ids FROM games_lq")
    for name, file_ids in cursor.fetchall():
        GAMES_LQ[name] = list(map(int, file_ids.split(',')))
    conn.close()


load_games_from_db()

user_states = {}

BANNER_TEXT = """<blockquote>🔥 <b>БЕЗ ВСТРОЕННЫХ ПРОГРАММ ИЛИ ВИРУСОВ</b>
🔥 <b><a href="https://t.me/FerwesGames">FERWES / GAMES</a></b>
🔥 <b><a href="https://t.me/addlist/AW1LBTA9xa45NDIy">FERWES / GRID</a></b></blockquote>"""

ACHIEVEMENTS = {
    'first_download': ('🥉', 'Первый контакт', 'Первое скачивание'),
    'first_order': ('🥉', 'Искатель', 'Первый заказ'),
    'first_like': ('🥉', 'Доброе сердце', 'Первый лайк'),
    'first_donate': ('🥉', 'Меценат', 'Первый донат'),
    'downloads_10': ('🥈', 'Коллекционер', '10 игр'),
    'downloads_50': ('🥈', 'Геймер', '50 игр'),
    'downloads_100': ('🥇', 'Хардкорщик', '100 игр'),
    'downloads_500': ('🥇', 'Легенда', '500 игр'),
    'orders_5': ('🥈', 'Заказчик', '5 заказов'),
    'orders_20': ('🥇', 'Звезда', '20 заказов'),
    'likes_25': ('🥈', 'Популярный', '25 лайков'),
    'likes_100': ('🥇', 'Любимчик', '100 лайков'),
    'donate_500': ('🥇', 'Спонсор', '500 Stars'),
    'priority_10': ('👑', 'Бог заказов', '10 приоритетных'),
    'anonymous_5': ('💎', 'Шепчущий', '5 анонимных подряд'),
    'days_365': ('💎', 'Верный друг', '365 дней'),
    'night_download': ('👑', 'Ночной сталкер', 'Скачать в 3-5 утра'),
}


def get_user_badge(orders_count, likes_count, priority_count):
    badges = []
    if orders_count >= 50:
        badges.append('👑 Король заказов')
    elif orders_count >= 20:
        badges.append('💫 Мастер')
    elif orders_count >= 10:
        badges.append('⭐ Опытный')
    elif orders_count >= 5:
        badges.append('⭐ Заказчик')
    else:
        badges.append('🌟 Новичок')
    if likes_count >= 50: badges.append('🔥 Популярный')
    if priority_count >= 10: badges.append('💎 Элита')
    return ' | '.join(badges)


# ========== ВСПОМОГАТЕЛЬНЫЕ ==========
def escape_html(text):
    if text is None: return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def generate_unique_id():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    while True:
        uid = str(random.randint(100000, 999999))
        cursor.execute("SELECT COUNT(*) FROM users WHERE unique_id = ?", (uid,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return uid
    conn.close()


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
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned = 0, ban_until = NULL, ban_reason = NULL WHERE user_id = ?",
                           (user_id,))
            conn.commit()
            conn.close()
            return False
    return True


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
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_muted = 0, mute_until = NULL, mute_reason = NULL WHERE user_id = ?",
                           (user_id,))
            conn.commit()
            conn.close()
            return False
    return True


def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def check_banned_words(text):
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True, word
    return False, None


def check_and_award_achievement(user_id, key):
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


def send_game_files(chat_id, game_name, user_id=None):
    if game_name not in GAMES_LQ: return False
    file_ids = GAMES_LQ[game_name]
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
            cursor.execute("UPDATE games_lq SET downloads = downloads + 1 WHERE game_name = ?", (game_name,))
            cursor.execute(
                "INSERT INTO download_history (user_id, game_name, file_count, download_date) VALUES (?, ?, ?, ?)",
                (user_id, game_name, len(file_ids), datetime.now().isoformat()))
            conn.commit()
            conn.close()
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
            if 3 <= datetime.now().hour < 5: check_and_award_achievement(user_id, 'night_download')
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки {game_name}: {e}")
        bot.send_message(chat_id, "❌ Ошибка")
        return False


def search_games(query):
    query = query.lower().strip()
    if query in GAMES_LQ: return [query]
    results = [g for g in GAMES_LQ if query in g or g in query]
    results.sort(key=lambda x: len(x))
    return results[:8]


# ========== START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private': return
    user = message.from_user
    get_or_create_user(user.id, user.username, user.first_name)
    if is_banned(user.id): bot.send_message(message.chat.id, "🚫 Вы заблокированы"); return
    unique_id = get_user_unique_id(user.id)
    text = f"""👋 Привет, {user.first_name or 'пользователь'}!

🎮 <b>Ferwes Games Bot</b>
🆔 Ваш ID: <code>#{unique_id}</code>

🔍 Напиши название игры — я найду и отправлю
📋 /orders — стол заказов
📝 /neworder — создать заказ
👤 /me — профиль
💰 /donate — поддержать

━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | ❓ /help"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
               types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"))
    markup.add(types.InlineKeyboardButton("👤 Профиль", callback_data="show_me"),
               types.InlineKeyboardButton("📜 История", callback_data="show_history"))
    markup.add(types.InlineKeyboardButton("💰 Поддержать", callback_data="show_donate"),
               types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help"))
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== /me ==========
@bot.message_handler(commands=['me'])
def me_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫"); return
    show_profile(message.chat.id, message.from_user.id)


def show_profile(chat_id, user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unique_id, username, first_name, downloads, created_orders, stars_donated, first_seen FROM users WHERE user_id = ?",
        (user_id,))
    user = cursor.fetchone()
    if not user: bot.send_message(chat_id, "❌ Профиль не найден"); conn.close(); return
    unique_id, username, first_name, downloads, orders, stars, first_seen = user
    cursor.execute("SELECT SUM(likes) FROM orders WHERE user_id = ?", (user_id,))
    total_likes = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND priority = 1", (user_id,))
    priority_count = cursor.fetchone()[0]
    cursor.execute("SELECT achievement_name FROM user_achievements WHERE user_id = ? ORDER BY earned_date DESC",
                   (user_id,))
    achievements = cursor.fetchall()
    conn.close()
    try:
        days = (datetime.now() - datetime.fromisoformat(first_seen)).days
    except:
        days = 0
    badge = get_user_badge(orders, total_likes, priority_count)
    text = f"""👤 <b>ПРОФИЛЬ</b>
━━━━━━━━━━━━━━━━━━
🆔 <code>#{unique_id}</code>
👤 {first_name or 'Пользователь'} {f'(@{username})' if username else ''}
🛡 {badge}

📊 <b>СТАТИСТИКА</b>
🎮 Скачано: {downloads}
📋 Заказов: {orders}
❤️ Лайков: {total_likes}
⭐ Stars: {stars}
📅 Дней: {days}

🏆 <b>АЧИВКИ</b> ({len(achievements)}/{len(ACHIEVEMENTS)})"""
    if achievements: text += "\n" + " ".join([a[0].split()[0] for a in achievements[:10]])
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📜 Все ачивки", callback_data="all_achievements"),
               types.InlineKeyboardButton("🏆 Топ", callback_data="top_orders"))
    markup.add(types.InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders"),
               types.InlineKeyboardButton("📥 История", callback_data="show_history"))
    markup.add(types.InlineKeyboardButton("🏠 Меню", callback_data="back_to_start"))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private': return
    text = """ℹ️ <b>ПОМОЩЬ</b>
🔍 Напиши название игры
📋 /orders — стол заказов
📝 /neworder — создать заказ
👤 /me — профиль и ачивки
📜 /history — история
⚠️ /report ID причина
💰 /donate — поддержать"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== DONATE ==========
@bot.message_handler(commands=['donate'])
def donate_cmd(message):
    if message.chat.type != 'private': return
    show_donate_menu(message.chat.id)


def show_donate_menu(chat_id):
    text = f"💰 <b>ПОДДЕРЖАТЬ</b>\n⭐ {PRIORITY_COST} Stars = 🔴 Приоритетный заказ"
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("⭐10", callback_data="donate_10"),
               types.InlineKeyboardButton("⭐20", callback_data="donate_20"),
               types.InlineKeyboardButton("⭐30", callback_data="donate_30"))
    markup.add(types.InlineKeyboardButton("⭐40", callback_data="donate_40"),
               types.InlineKeyboardButton("⭐50", callback_data="donate_50"),
               types.InlineKeyboardButton("🌟100", callback_data="donate_100"))
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="back_to_start"))
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== HISTORY ==========
@bot.message_handler(commands=['history'])
def history_cmd(message):
    if message.chat.type != 'private': return
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
        bot.send_message(chat_id, "📜 <b>ИСТОРИЯ</b>\n\nУ вас пока нет скачиваний.", parse_mode='HTML')
        return
    text = f"📜 <b>ИСТОРИЯ</b> ({len(history)})\n\n"
    for game_name, file_count, download_date in history:
        try:
            date_str = datetime.fromisoformat(download_date).strftime("%d.%m.%Y %H:%M")
        except:
            date_str = "неизвестно"
        text += f"🎮 {game_name}\n📦 {file_count} файлов | 📅 {date_str}\n━\n"
    bot.send_message(chat_id, text, parse_mode='HTML')


# ========== ORDERS (КНОПКИ-ЗАКАЗЫ) ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫"); return
    show_orders_page(message.chat.id, 0)


def show_orders_page(chat_id, page=0):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, game_name, size, likes, priority, created_date, anonymous, (SELECT COUNT(*) FROM order_reports WHERE order_id = o.order_id) FROM orders o WHERE status = 'active' ORDER BY priority DESC, created_date DESC")
    all_orders = cursor.fetchall()
    conn.close()

    if not all_orders:
        bot.send_message(chat_id, "📭 Нет активных заказов\n\nСтаньте первым через /neworder", parse_mode='HTML')
        return

    orders_per_page = 10
    total_pages = (len(all_orders) + orders_per_page - 1) // orders_per_page
    if page >= total_pages: page = total_pages - 1
    if page < 0: page = 0

    start_idx = page * orders_per_page
    end_idx = min(start_idx + orders_per_page, len(all_orders))
    page_orders = all_orders[start_idx:end_idx]

    priority_count = sum(1 for o in all_orders if o[4] == 1)

    text = f"📋 <b>ЗАКАЗЫ</b> ({len(all_orders)}) | 🔴{priority_count} 🔵{len(all_orders) - priority_count} | Стр. {page + 1}/{total_pages}\n━━━━━━━━━━━━━━━━━━\n"

    markup = types.InlineKeyboardMarkup(row_width=1)

    for order in page_orders:
        order_id, game_name, size, likes, priority, created_date, anonymous, report_count = order
        try:
            date_str = datetime.fromisoformat(created_date).strftime("%d.%m")
        except:
            date_str = "???"
        priority_emoji = "🔴" if priority else "🔵"
        new_badge = " 🆕" if (datetime.now() - datetime.fromisoformat(created_date)).days < 2 else ""
        report_badge = f" ⚠️{report_count}" if report_count > 0 else ""
        anon_badge = " 👻" if anonymous else ""
        markup.add(types.InlineKeyboardButton(
            f"{priority_emoji} #{order_id} | {game_name[:20]} | {size} | ❤️{likes}{new_badge}{report_badge}{anon_badge}",
            callback_data=f"order_detail_{order_id}_{page}"))

    nav = []
    if page > 0: nav.append(types.InlineKeyboardButton("◀️", callback_data=f"orders_page_{page - 1}"))
    nav.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1: nav.append(types.InlineKeyboardButton("▶️", callback_data=f"orders_page_{page + 1}"))
    if nav: markup.row(*nav)

    markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"),
               types.InlineKeyboardButton("🏠 Меню", callback_data="back_to_start"))

    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== ДЕТАЛИ ЗАКАЗА ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('order_detail_'))
def order_detail_callback(call):
    parts = call.data.split('_')
    order_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, u.username, u.first_name,
               (SELECT COUNT(*) FROM orders WHERE user_id = o.user_id),
               (SELECT SUM(likes) FROM orders WHERE user_id = o.user_id),
               (SELECT COUNT(*) FROM orders WHERE user_id = o.user_id AND priority = 1)
        FROM orders o LEFT JOIN users u ON o.user_id = u.user_id WHERE o.order_id = ?
    """, (order_id,))
    order = cursor.fetchone()
    conn.close()

    if not order: bot.answer_callback_query(call.id, "❌"); return

    game_name = order[2];
    size = order[3];
    likes = order[4];
    priority = order[6];
    created_date = order[7]
    anonymous = order[8];
    views = order[9] or 0;
    username = order[11];
    first_name = order[12]
    user_orders = order[13];
    user_likes = order[14] or 0;
    user_priority = order[15] or 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET views = views + 1 WHERE order_id = ?", (order_id,))
    cursor.execute("SELECT COUNT(*) FROM order_reports WHERE order_id = ?", (order_id,))
    report_count = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    views += 1

    try:
        date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y %H:%M")
    except:
        date_str = "неизвестно"
    days_left = ORDER_EXPIRE_DAYS - (datetime.now() - datetime.fromisoformat(created_date)).days

    priority_text = "🔴 ПРИОРИТЕТ" if priority else "🔵 Обычный"
    author = "👤 Аноним" if anonymous else f"👤 @{username}" if username else f"👤 {first_name or 'Пользователь'}"
    badge = get_user_badge(user_orders, user_likes, user_priority)

    text = f"""📋 <b>ЗАКАЗ #{order_id}</b>
━━━━━━━━━━━━━━━━━━
🎮 <b>{escape_html(game_name)}</b>
💾 {size}
{priority_text}
{author} | 🛡 {badge}
━━━━━━━━━━━━━━━━━━
📅 {date_str}
👁 Просмотров: {views}
❤️ Лайков: {likes}
⚠️ Жалоб: {report_count}
⏳ Осталось: {days_left} дней"""

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("❤️", callback_data=f"like_{order_id}"),
               types.InlineKeyboardButton("⚠️", callback_data=f"report_menu_{order_id}"),
               types.InlineKeyboardButton("📋", callback_data=f"copy_order_{order_id}"))
    markup.add(types.InlineKeyboardButton("📢", callback_data=f"share_order_{order_id}"),
               types.InlineKeyboardButton("🔔", callback_data=f"subscribe_order_{order_id}"))
    markup.add(types.InlineKeyboardButton("▲ К заказам", callback_data=f"orders_page_{page}"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML',
                              reply_markup=markup)
    except:
        pass
    bot.answer_callback_query(call.id)


# ========== CALLBACKS ==========
@bot.callback_query_handler(func=lambda call: call.data == 'all_achievements')
def all_achievements_cb(call):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_key FROM user_achievements WHERE user_id = ?", (call.from_user.id,))
    earned = [r[0] for r in cursor.fetchall()]
    conn.close()
    text = "🏆 <b>АЧИВКИ</b>\n\n"
    for key, (emoji, name, desc) in ACHIEVEMENTS.items():
        text += f"{'✅' if key in earned else '🔒'} {emoji} {name} — {desc}\n"
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML',
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("« Назад", callback_data="show_me")))
    except:
        pass
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == 'top_orders')
def top_orders_cb(call):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT u.username, u.first_name, u.unique_id, COUNT(o.order_id), COALESCE(SUM(o.likes),0), COUNT(CASE WHEN o.priority=1 THEN 1 END) FROM users u LEFT JOIN orders o ON u.user_id=o.user_id GROUP BY u.user_id ORDER BY COUNT(o.order_id) DESC LIMIT 10")
    top = cursor.fetchall()
    conn.close()
    text = "🏆 <b>ТОП-10</b>\n\n"
    for i, u in enumerate(top, 1):
        username, fn, uid, cnt, likes, prio = u
        name = f"@{username}" if username else fn or f"#{uid}"
        badge = get_user_badge(cnt, likes, prio).split('|')[0]
        text += f"{'🥇🥈🥉'[i - 1] if i < 4 else f'{i}.'} {badge} {name} — {cnt} зак, {likes}❤️\n"
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML',
                              reply_markup=types.InlineKeyboardMarkup().add(
                                  types.InlineKeyboardButton("« Назад", callback_data="show_me")))
    except:
        pass
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('share_order_'))
def share_cb(call):
    bot.answer_callback_query(call.id, f"https://t.me/{bot.get_me().username}?start=order_{call.data.split('_')[2]}",
                              show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('subscribe_order_'))
def subscribe_cb(call):
    order_id = int(call.data.split('_')[2])
    user_id = call.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT subscribers FROM orders WHERE order_id = ?", (order_id,))
    result = cursor.fetchone()
    if result:
        subs = result[0].split(',') if result[0] else []
        uid_str = str(user_id)
        if uid_str in subs:
            subs.remove(uid_str); msg = "🔔 Отписались"
        else:
            subs.append(uid_str); msg = "🔔 Подписались!"
        cursor.execute("UPDATE orders SET subscribers = ? WHERE order_id = ?", (','.join(subs), order_id))
        conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, msg, show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('copy_order_'))
def copy_cb(call):
    order_id = int(call.data.split('_')[2])
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT game_name FROM orders WHERE order_id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        user_states[call.message.chat.id] = {'state': 'waiting_size', 'game': result[0]}
        bot.send_message(call.message.chat.id, f"📝 Копируем: <b>{result[0]}</b>\n\nВведите размер в ГБ:",
                         parse_mode='HTML')
    bot.answer_callback_query(call.id)


# ========== NEWORDER ==========
@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private': return
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫"); return
    if is_muted(message.from_user.id): bot.send_message(message.chat.id, "🔇"); return
    user_states[message.chat.id] = {'state': 'waiting_game'}
    bot.send_message(message.chat.id, "📝 <b>НОВЫЙ ЗАКАЗ</b>\n\nВведите название игры:", parse_mode='HTML',
                     reply_markup=types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("Отмена", callback_data="cancel_order")))


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and user_states[m.chat.id].get('state') == 'waiting_game')
def get_game_name(message):
    if message.chat.type != 'private': return
    game_name = message.text.strip()
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
            bot.send_message(message.chat.id, f"🔇 <b>Мут на 24ч!</b>\n{MAX_BANNED_WORD_ATTEMPTS} попытки.",
                             parse_mode='HTML')
            return
        bot.send_message(message.chat.id,
                         f"❌ Запрещённое слово: \"{banned_word}\"\n⚠️ {attempts}/{MAX_BANNED_WORD_ATTEMPTS}",
                         parse_mode='HTML')
        return
    user_states[message.chat.id] = {'state': 'waiting_size', 'game': game_name}
    bot.send_message(message.chat.id, f"🎮 {game_name}\n\nВведите размер в ГБ (только цифры):", parse_mode='HTML')


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and isinstance(user_states[m.chat.id], dict) and user_states[
        m.chat.id].get('state') == 'waiting_size')
def get_game_size(message):
    if message.chat.type != 'private': return
    size_input = message.text.strip()
    if not re.match(r'^[\d.]+$', size_input):
        bot.send_message(message.chat.id, "❌ Только цифры!", parse_mode='HTML')
        return
    data = user_states[message.chat.id]
    data['size'] = f"{size_input} ГБ"
    data['state'] = 'waiting_priority'
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🔵 Обычный", callback_data="priority_normal"),
               types.InlineKeyboardButton(f"🔴 Приоритет ({PRIORITY_COST}⭐)", callback_data="priority_urgent"))
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel_order"))
    bot.send_message(message.chat.id, f"🎮 {data['game']}\n💾 {data['size']}\n\n<b>Тип заказа:</b>", parse_mode='HTML',
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('priority_'))
def priority_choice(call):
    if call.message.chat.id not in user_states: bot.answer_callback_query(call.id, "❌"); return
    data = user_states[call.message.chat.id]
    if call.data == 'priority_urgent':
        prices = [types.LabeledPrice(f"Приоритет: {data['game'][:20]}", PRIORITY_COST)]
        try:
            bot.send_invoice(call.message.chat.id, "🔴 Приоритетный заказ",
                             f"Игра: {data['game'][:50]}\nРазмер: {data['size']}",
                             f"priority_order_{call.from_user.id}", "", "XTR", prices)
            data['state'] = 'waiting_payment';
            data['priority'] = True
            user_states[call.message.chat.id] = data
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
            bot.answer_callback_query(call.id, "✅ Счёт создан!")
        except:
            bot.answer_callback_query(call.id, "❌")
    else:
        data['priority'] = False;
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
    if call.message.chat.id not in user_states: bot.answer_callback_query(call.id, "❌"); return
    data = user_states[call.message.chat.id]
    anonymous = call.data == 'anon_yes'
    priority = data.get('priority', False)
    user_id = call.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, game_name, size, created_date, anonymous, priority) VALUES (?,?,?,?,?,?)",
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
        if len([r for r in cursor.fetchall() if r[0] == 1]) >= 5: check_and_award_achievement(user_id, 'anonymous_5')
    conn.close()
    text = f"""✅ <b>ЗАКАЗ #{order_id} СОЗДАН</b>
🎮 {data['game']}
💾 {data['size']}
{'🔴 Приоритетный' if priority else '🔵 Обычный'}
{'👻 Анонимно' if anonymous else '👤 Открыто'}"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Все заказы", callback_data="show_orders"))
    markup.add(types.InlineKeyboardButton("🏠 Меню", callback_data="back_to_start"))
    bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)


# ========== MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private': return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, game_name, size, likes, status, priority, anonymous FROM orders WHERE user_id = ? ORDER BY created_date DESC LIMIT 10",
        (message.from_user.id,))
    orders = cursor.fetchall()
    conn.close()
    if not orders: bot.send_message(message.chat.id, "📭 Нет заказов"); return
    text = f"👤 <b>МОИ ЗАКАЗЫ</b> ({len(orders)})\n\n"
    for o in orders:
        text += f"{'🔴' if o[5] else '🔵'} <b>#{o[0]}</b> | {o[1]}\n💾 {o[2]} | ❤️{o[3]} | {'Активен' if o[4] == 'active' else 'Завершён'}{' 👻' if o[6] else ''}\n━\n"
    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== REPORT ==========
@bot.message_handler(commands=['report'])
def report_cmd(message):
    if message.chat.type != 'private': return
    try:
        parts = message.text.split(maxsplit=2)
        order_id, reason = int(parts[1]), parts[2] if len(parts) > 2 else "Без причины"
    except:
        bot.send_message(message.chat.id, "❌ /report ID причина"); return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone(): bot.send_message(message.chat.id, f"❌ #{order_id} не найден"); conn.close(); return
    cursor.execute("SELECT report_id FROM order_reports WHERE order_id = ? AND reporter_id = ?",
                   (order_id, message.from_user.id))
    if cursor.fetchone(): bot.send_message(message.chat.id, "❌ Уже жаловались"); conn.close(); return
    cursor.execute("INSERT INTO order_reports (order_id, reporter_id, reason, reported_date) VALUES (?,?,?,?)",
                   (order_id, message.from_user.id, reason, datetime.now().isoformat()))
    cursor.execute("SELECT COUNT(*) FROM order_reports WHERE order_id = ?", (order_id,))
    if cursor.fetchone()[0] >= AUTO_DELETE_REPORTS:
        cursor.execute("SELECT user_id, game_name FROM orders WHERE order_id = ?", (order_id,))
        o = cursor.fetchone()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_likes WHERE order_id = ?", (order_id,))
        cursor.execute("DELETE FROM order_reports WHERE order_id = ?", (order_id,))
        if o:
            try:
                bot.send_message(o[0], f"📋 Заказ #{order_id} ({o[1]}) удалён ({AUTO_DELETE_REPORTS}+ жалоб)",
                                 parse_mode='HTML')
            except:
                pass
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"⚠️ Жалоба на #{order_id} отправлена")


# ========== ПОИСК ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def search_handler(message):
    if is_banned(message.from_user.id): bot.send_message(message.chat.id, "🚫"); return
    query = message.text.strip()
    results = search_games(query)
    if len(results) == 1 and query.lower() == results[0].lower():
        bot.send_message(message.chat.id, f"🎮 {results[0]}\n📦 {len(GAMES_LQ[results[0]])} файлов\n⏳ Отправляю...",
                         parse_mode='HTML')
        send_game_files(message.chat.id, results[0], message.from_user.id)
    elif results:
        text = f"🔍 \"{query}\":\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for g in results[:8]:
            markup.add(types.InlineKeyboardButton(f"📥 {g}", callback_data=f"play_{g}"))
            text += f"• {g}\n"
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"❌ \"{query}\" не найдено\n📝 /neworder", parse_mode='HTML')


# ========== MODERATOR ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if not is_admin(message.from_user.id): return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users");
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status='active'");
    orders = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM order_reports");
    reports = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM games_lq");
    games = cursor.fetchone()[0]
    conn.close()
    text = f"""🛡 <b>ПАНЕЛЬ МОДЕРАТОРА</b>
━━━━━━━━━━━━━━━━━━
👥 {users} | 📋 {orders} | ⚠️ {reports} | 🎮 {games}
━━━━━━━━━━━━━━━━━━
/addgame Название IDначала IDконца
/ban #ID время причина
/mute #ID время причина
/unban #ID | /unmute #ID
/addadmin #ID | /removeadmin #ID
/addword слово | /removeword слово
/deleteorder ID причина
/broadcast текст
/userinfo #ID"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['addgame'])
def addgame_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split()
        end_id, start_id = int(parts[-1]), int(parts[-2])
        name = ' '.join(parts[1:-2]).lower()
        file_ids = list(range(start_id, end_id + 1))
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO games_lq (game_name, file_ids, downloads, added_date) VALUES (?,?,?,?)",
                       (name, ','.join(map(str, file_ids)), 0, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        load_games_from_db()
        bot.reply_to(message, f"✅ {name} добавлена ({len(file_ids)} файлов)")
    except:
        bot.reply_to(message, "❌ /addgame Название IDначала IDконца")


@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=3)
        unique_id, duration, reason = parts[1].replace('#', ''), parts[2].lower(), parts[3] if len(
            parts) > 3 else "Без причины"
        target = get_user_by_unique_id(unique_id)
        if not target: bot.reply_to(message, f"❌ #{unique_id} не найден"); return
        if duration not in BAN_DURATIONS: bot.reply_to(message, f"❌ Время: {', '.join(BAN_DURATIONS.keys())}"); return
        ban_until = (datetime.now() + BAN_DURATIONS[duration]).isoformat() if BAN_DURATIONS[duration] else None
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned=1, ban_until=?, ban_reason=? WHERE user_id=?",
                       (ban_until, reason, target))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ #{unique_id} забанен на {duration}")
    except:
        bot.reply_to(message, "❌ /ban #ID время причина")


@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target = get_user_by_unique_id(message.text.split()[1].replace('#', ''))
        if target:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned=0, ban_until=NULL, ban_reason=NULL WHERE user_id=?", (target,))
            conn.commit()
            conn.close()
            bot.reply_to(message, "✅ Разбанен")
        else:
            bot.reply_to(message, "❌ Не найден")
    except:
        bot.reply_to(message, "❌ /unban #ID")


@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=3)
        unique_id, duration, reason = parts[1].replace('#', ''), parts[2].lower(), parts[3] if len(
            parts) > 3 else "Без причины"
        target = get_user_by_unique_id(unique_id)
        if not target: bot.reply_to(message, f"❌ #{unique_id} не найден"); return
        if duration not in MUTE_DURATIONS: bot.reply_to(message, f"❌ Время: {', '.join(MUTE_DURATIONS.keys())}"); return
        mute_until = (datetime.now() + MUTE_DURATIONS[duration]).isoformat()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_muted=1, mute_until=?, mute_reason=? WHERE user_id=?",
                       (mute_until, reason, target))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ #{unique_id} замучен на {duration}")
    except:
        bot.reply_to(message, "❌ /mute #ID время причина")


@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target = get_user_by_unique_id(message.text.split()[1].replace('#', ''))
        if target:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_muted=0, mute_until=NULL, mute_reason=NULL WHERE user_id=?", (target,))
            conn.commit()
            conn.close()
            bot.reply_to(message, "✅ Размучен")
        else:
            bot.reply_to(message, "❌ Не найден")
    except:
        bot.reply_to(message, "❌ /unmute #ID")


@bot.message_handler(commands=['addadmin'])
def addadmin_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target = get_user_by_unique_id(message.text.split()[1].replace('#', ''))
        if target:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (target,))
            conn.commit()
            conn.close()
            bot.reply_to(message, "✅ Админ добавлен")
        else:
            bot.reply_to(message, "❌ Не найден")
    except:
        bot.reply_to(message, "❌ /addadmin #ID")


@bot.message_handler(commands=['removeadmin'])
def removeadmin_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target = get_user_by_unique_id(message.text.split()[1].replace('#', ''))
        if target and target != 7885915159:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id=?", (target,))
            conn.commit()
            conn.close()
            bot.reply_to(message, "✅ Админ удалён")
        else:
            bot.reply_to(message, "❌ Нельзя")
    except:
        bot.reply_to(message, "❌ /removeadmin #ID")


@bot.message_handler(commands=['addword'])
def addword_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        word = message.text.split(' ', 1)[1].lower()
        if word not in BANNED_WORDS:
            BANNED_WORDS.append(word); bot.reply_to(message, f"✅ {word}")
        else:
            bot.reply_to(message, "❌ Уже есть")
    except:
        bot.reply_to(message, "❌ /addword слово")


@bot.message_handler(commands=['removeword'])
def removeword_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        word = message.text.split(' ', 1)[1].lower()
        if word in BANNED_WORDS:
            BANNED_WORDS.remove(word); bot.reply_to(message, f"✅ {word}")
        else:
            bot.reply_to(message, "❌ Не найдено")
    except:
        bot.reply_to(message, "❌ /removeword слово")


@bot.message_handler(commands=['deleteorder'])
def deleteorder_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        parts = message.text.split(maxsplit=2)
        order_id, reason = int(parts[1]), parts[2] if len(parts) > 2 else "Без причины"
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM orders WHERE order_id=?", (order_id,))
        o = cursor.fetchone()
        if not o: bot.reply_to(message, "❌ Не найден"); conn.close(); return
        cursor.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
        cursor.execute("DELETE FROM order_likes WHERE order_id=?", (order_id,))
        cursor.execute("DELETE FROM order_reports WHERE order_id=?", (order_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ #{order_id} удалён")
        try:
            bot.send_message(o[0], f"📋 Заказ #{order_id} удалён\nПричина: {reason}", parse_mode='HTML')
        except:
            pass
    except:
        bot.reply_to(message, "❌ /deleteorder ID причина")


@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        text = message.text.split(' ', 1)[1]
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned=0")
        users = cursor.fetchall()
        conn.close()
        sent = 0
        for (u,) in users:
            try:
                bot.send_message(u, f"📢 {text}", parse_mode='HTML'); sent += 1; time.sleep(0.1)
            except:
                pass
        bot.reply_to(message, f"✅ {sent}/{len(users)}")
    except:
        bot.reply_to(message, "❌ /broadcast текст")


@bot.message_handler(commands=['userinfo'])
def userinfo_cmd(message):
    if not is_admin(message.from_user.id): return
    try:
        target = get_user_by_unique_id(message.text.split()[1].replace('#', ''))
        if not target: bot.reply_to(message, "❌ Не найден"); return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (target,))
        u = cursor.fetchone()
        conn.close()
        if u:
            text = f"""👤 #{u[1]}
👤 {u[3] or 'Н/Д'} (@{u[2] or 'Н/Д'})
📊 Скачиваний: {u[4]} | Заказов: {u[5]} | Stars: {u[6]}
{'🚫 ЗАБАНЕН' if u[9] else '✅'} {'🔇 ЗАМУЧЕН' if u[12] else '✅'}"""
            bot.send_message(message.chat.id, text, parse_mode='HTML')
    except:
        bot.reply_to(message, "❌ /userinfo #ID")


# ========== ОСТАЛЬНЫЕ CALLBACKS ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data.startswith('like_'):
        if is_banned(user_id): bot.answer_callback_query(call.id, "❌"); return
        order_id = int(call.data.split('_')[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM order_likes WHERE order_id=? AND user_id=?", (order_id, user_id))
        if cursor.fetchone(): bot.answer_callback_query(call.id, "❌ Уже"); conn.close(); return
        cursor.execute("INSERT INTO order_likes (order_id, user_id, liked_date) VALUES (?,?,?)",
                       (order_id, user_id, datetime.now().isoformat()))
        cursor.execute("UPDATE orders SET likes=likes+1 WHERE order_id=?", (order_id,))
        conn.commit()
        conn.close()
        check_and_award_achievement(user_id, 'first_like')
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(likes) FROM orders WHERE user_id=?", (user_id,))
        total = cursor.fetchone()[0] or 0
        if total >= 25: check_and_award_achievement(user_id, 'likes_25')
        if total >= 100: check_and_award_achievement(user_id, 'likes_100')
        conn.close()
        bot.answer_callback_query(call.id, "❤️")

    elif call.data.startswith('play_'):
        game_name = call.data[5:]
        bot.answer_callback_query(call.id, "⏳")
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
        show_orders_page(call.message.chat.id, page)

    elif call.data.startswith('donate_'):
        amount = int(call.data.split('_')[1])
        prices = {10: [types.LabeledPrice("Поддержка", 10)], 20: [types.LabeledPrice("Поддержка", 20)],
                  30: [types.LabeledPrice("Поддержка", 30)], 40: [types.LabeledPrice("Поддержка", 40)],
                  50: [types.LabeledPrice("Поддержка", 50)], 100: [types.LabeledPrice("Поддержка", 100)]}
        try:
            bot.send_invoice(call.message.chat.id, "Поддержка", f"{amount} Stars", f"donate_{user_id}_{amount}", "",
                             "XTR", prices[amount])
            bot.answer_callback_query(call.id, "✅")
        except:
            bot.answer_callback_query(call.id, "❌")

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
        bot.send_message(call.message.chat.id, "❌ Отменено")
        start_cmd(call.message)

    elif call.data == "current_page":
        bot.answer_callback_query(call.id)


# ========== ОПЛАТА ==========
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(q): bot.answer_pre_checkout_query(q.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def payment(message):
    user_id = message.from_user.id
    payload = message.successful_payment.invoice_payload
    if payload.startswith('priority_order_'):
        if user_id in user_states and user_states[user_id].get('state') == 'waiting_payment':
            data = user_states[user_id]
            data['state'] = 'waiting_anonymous';
            data['priority'] = True
            user_states[user_id] = data
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("👤 Открыто", callback_data="anon_no"),
                       types.InlineKeyboardButton("👻 Анонимно", callback_data="anon_yes"))
            bot.send_message(message.chat.id,
                             f"✅ Оплачено!\n\n🎮 {data['game']}\n💾 {data['size']}\n🔴 Приоритетный\n\n<b>Анонимно?</b>",
                             parse_mode='HTML', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "✅ Оплачено, но сессия истекла.")
    elif payload.startswith('donate_'):
        try:
            amount = int(payload.split('_')[2])
        except:
            amount = 0
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET stars_donated=stars_donated+? WHERE user_id=?", (amount, user_id))
        cursor.execute("SELECT stars_donated FROM users WHERE user_id=?", (user_id,))
        total = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        check_and_award_achievement(user_id, 'first_donate')
        if total >= 500: check_and_award_achievement(user_id, 'donate_500')
        bot.send_message(message.chat.id, f"✅ <b>СПАСИБО!</b>\n💰 {amount} Stars", parse_mode='HTML')


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 FERWES GAMES BOT v9.0")
    print(f"🎮 Игр: {len(GAMES_LQ)}")
    print("👤 /me | 📋 /orders | 📝 /neworder")
    print("🛡 /moderator — панель модератора")
    print("=" * 50)
    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        logger.critical(f"Ошибка: {e}")
        time.sleep(10)