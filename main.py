import telebot
from telebot import types
import sqlite3
import os
import time
import random
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# ========== НАСТРОЙКИ ЛОГИРОВАНИЯ ==========
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Файловый handler с ротацией (10 файлов по 5 МБ)
file_handler = RotatingFileHandler('bot.log', maxBytes=5 * 1024 * 1024, backupCount=10, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Консольный handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ========== НАСТРОЙКИ БОТА ==========
BOT_TOKEN = '8456295069:AAGz48djuL19fYnn9FCz8DgJRQgIO6rLlq0'
bot = telebot.TeleBot(BOT_TOKEN)
GAMES_CHANNEL_ID = -1003421344618

# Константы
LIKE_COOLDOWN_DAYS = 1000
ORDER_EXPIRE_DAYS = 60

# ========== БАННЕР (исправлен - без Markdown) ==========
BANNER_TEXT = """🔥 БЕЗ ВСТРОЕННЫХ ПРОГРАММ ИЛИ ВИРУСОВ
🔥 FERWES / GAMES (https://t.me/FerwesGames)
🔥 FERWES / GRID (https://t.me/addlist/AW1LBTA9xa45NDIy)"""

# ========== БАЗА ДАННЫХ SQLITE ==========
DB_FILE = 'bot_database.db'


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            downloads INTEGER DEFAULT 0,
            created_orders INTEGER DEFAULT 0,
            stars_donated INTEGER DEFAULT 0,
            first_seen TIMESTAMP,
            last_active TIMESTAMP,
            is_banned BOOLEAN DEFAULT 0,
            is_muted BOOLEAN DEFAULT 0,
            is_vip BOOLEAN DEFAULT 0,
            vip_until TIMESTAMP
        )
    ''')

    # Таблица игр
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE,
            file_ids TEXT,
            downloads INTEGER DEFAULT 0,
            added_date TIMESTAMP
        )
    ''')

    # Таблица заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_name TEXT,
            size TEXT,
            likes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Таблица лайков заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_likes (
            order_id INTEGER,
            user_id INTEGER,
            liked_date TIMESTAMP,
            PRIMARY KEY (order_id, user_id)
        )
    ''')

    # Таблица лайков (кулдаун)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS like_cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_like TIMESTAMP
        )
    ''')

    # Таблица логов действий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP
        )
    ''')

    # Таблица админов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    # Таблица донатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stars_amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_date TIMESTAMP,
            completed_date TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")


# Инициализация БД
init_database()


# Добавляем стандартного админа
def init_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (7885915159,))
    conn.commit()
    conn.close()


init_admin()

# ========== БАЗА ВСЕХ ИГР ==========
GAMES_DATABASE = {
    # A
    'antonblast': [913, 914, 1749],
    'assassins creed': list(range(1028, 1033)) + [1749],
    'artmoney': [1770, 1771, 1749],
    # B
    'bad cheese': list(range(1651, 1654)) + [1749],
    'battlefield 3': list(range(1773, 1784)) + [1749],
    'BeamNG drive': list(range(861, 873)) + [1749],
    'beholder': list(range(823, 825)) + [1749],
    'bendy and the ink machine': list(range(652, 654)) + [1749],
    'bioshock remaster': list(range(1070, 1080)) + [1749],
    'blender': list(range(1306, 1310)) + [1749],
    'borderlands 2': list(range(776, 782)) + [1749],
    'bully': list(range(1639, 1642)) + [1749],
    # C
    'call of duty modern warfare 2': list(range(1212, 1221)) + [1749],
    'call of duty ww2': list(range(521, 541)) + [1749],
    'caves of qud': list(range(655, 657)) + [1749],
    'chesscraft': list(range(1655, 1657)) + [1749],
    'clair obscur: expedition 33': list(range(1552, 1575)) + [1749],
    'construction simulator 4': list(range(1373, 1375)) + [1749],
    'counter strike 1.6': list(range(1453, 1455)) + [1749],
    'cry of fear': list(range(1481, 1486)) + [1749],
    'cuphead': list(range(817, 821)) + [1749],
    'cyberpunk 2077': list(range(658, 704)) + [1749],
    # D
    'dark souls 3': list(range(880, 894)) + [1749],
    'dead space': list(range(1576, 1580)) + [1749],
    'dead space remake': list(range(1581, 1599)) + [1749],
    'detroit become human': list(range(1407, 1436)) + [1749],
    'devil may cry 4': list(range(1244, 1258)) + [1749],
    'dispatch': list(range(1311, 1320)) + [1749],
    'distant worlds 2': list(range(1644, 1650)) + [1749],
    'doom the dark ages': list(range(1706, 1748)) + [1749],
    'dying light: the beast': list(range(1502, 1525)) + [1749],
    # E
    'elden ring': list(range(552, 587)) + [1749],
    # F
    'fallout 3': list(range(1231, 1236)) + [1749],
    'fallout 4': list(range(1277, 1296)) + [1749],
    'far cry': list(range(1658, 1661)) + [1749],
    'far cry 2': list(range(1662, 1665)) + [1749],
    'far cry 3': list(range(783, 787)) + [1749],
    'far cry 4': list(range(1354, 1369)) + [1749],
    'far cry 5': list(range(242, 254)) + [1749],
    'farm frenzy': list(range(1456, 1458)) + [1749],
    'fifa 17': list(range(916, 931)) + [1749],
    'finding frankie': list(range(622, 626)) + [1749],
    'five nights at freddys': list(range(948, 950)) + [1749],
    'five nights at freddys secret of the mimic': list(range(1462, 1473)) + [1749],
    'fl studio 25': list(range(1153, 1156)) + [1749],
    'friday night funkin': list(range(748, 750)) + [1749],
    'frostpunk': list(range(1222, 1228)) + [1749],
    'frostpunk 2': list(range(1619, 1627)) + [1749],
    # G
    'garrys mod': list(range(858, 860)) + [1749],
    'ghost of tsushima': list(range(1527, 1551)) + [1749],
    'ghostrunner': list(range(1692, 1701)) + [1749],
    'goat simulator': list(range(618, 621)) + [1749],
    'god of war': list(range(1787, 1805)) + [1749],
    'Grand Theft Auto III': list(range(1088, 1090)) + [1749],
    'Grand Theft Auto IV': list(range(799, 810)) + [1749],
    'Grand Theft Auto V': list(range(705, 742)) + [1749],
    'Grand Theft Auto: San Andreas': list(range(1259, 1270)) + [1749],
    'Grand Theft Auto: Vice City': list(range(1450, 1452)) + [1749],
    # H
    'half life 2': list(range(1207, 1211)) + [1749],
    'hard time 3': list(range(1006, 1009)) + [1749],
    'hatred': list(range(1667, 1669)) + [1749],
    'hearts of iron 4': list(range(743, 747)) + [1749],
    'hearts of iron 4: ultimate bundle': list(range(1497, 1501)) + [1749],
    'hitman': list(range(962, 985)) + [1749],
    'hitman blood money': list(range(951, 960)) + [1749],
    'hollow knight': list(range(1060, 1062)) + [1749],
    'hollow knight silksong': list(range(1600, 1602)) + [1749],
    'hotline miami': list(range(1085, 1087)) + [1749],
    'hotline miami 2': [1159, 1160, 1749],
    'humanit z': list(range(1096, 1110)) + [1749],
    'hytale': list(range(1398, 1402)) + [1749],
    # J
    'jewel match': list(range(234, 236)) + [1749],
    # K
    'korsary 3': list(range(1370, 1372)) + [1749],
    # L
    'left 4 dead 2': list(range(1207, 1211)) + [1749],
    'little nightmares 3': list(range(174, 182)) + [1749],
    'lonarpg': list(range(1447, 1449)) + [1749],
    # M
    'mafia 1': list(range(1241, 1243)) + [1749],
    'mafia 2': list(range(942, 947)) + [1749],
    'metro 2033': list(range(1051, 1056)) + [1749],
    'metro last light redux': list(range(1606, 1611)) + [1749],
    'minecraft': list(range(932, 935)) + [1749],
    'my gaming club': list(range(811, 813)) + [1749],
    'my summer car': list(range(1441, 1443)) + [1749],
    'my winter car': list(range(1347, 1349)) + [1749],
    'miside': list(range(1057, 1059)) + [1749],
    # N
    'nier automata': list(range(164, 173)) + [1749],
    'nier replicant': list(range(1670, 1682)) + [1749],
    'no im not a human': list(range(517, 520)) + [1749],
    'no mans sky': list(range(1751, 1765)) + [1749],
    # O
    'one shot': list(range(1065, 1069)) + [1749],
    'orion sandbox': list(range(814, 816)) + [1749],
    # P
    'palworld': list(range(202, 216)) + [1749],
    'payday the heist': list(range(876, 879)) + [1749],
    'people playground': list(range(1603, 1605)) + [1749],
    'plants vs zombies': list(range(549, 551)) + [1749],
    'portal 2': list(range(1207, 1211)) + [1749],
    'portal knights': list(range(1237, 1239)) + [1749],
    'postal 2': list(range(1615, 1617)) + [1749],
    'project zomboid': list(range(1093, 1095)) + [1749],
    'prototype 1': list(range(895, 901)) + [1749],
    'prototype 2': list(range(1044, 1050)) + [1749],
    # Q
    'quasimorph': list(range(589, 591)) + [1749],
    # R
    'red dead redemption': list(range(542, 548)) + [1749],
    'red dead redemption 2': list(range(428, 485)) + [1749],
    'resident evil revelations 2': list(range(788, 798)) + [1749],
    'resident evil village': list(range(826, 845)) + [1749],
    'rimworld': list(range(1298, 1301)) + [1749],
    'risk of rain 2': list(range(1612, 1614)) + [1749],
    'rock star life simulator': list(range(184, 186)) + [1749],
    # S
    'stalker shadow of chernobyl': list(range(1326, 1329)) + [1749],
    'stalker anomaly': list(range(1628, 1634)) + [1749],
    'sally face': list(range(628, 632)) + [1749],
    'scorn': list(range(217, 227)) + [1749],
    'slim rancher': list(range(853, 857)) + [1749],
    'slime rancher 2': list(range(1323, 1325)) + [1749],
    'spider man remastered': list(range(486, 516)) + [1749],
    'stray': list(range(936, 941)) + [1749],
    'streets of rogue 2': list(range(1041, 1043)) + [1749],
    'system shock 2 remaster': list(range(187, 192)) + [1749],
    'swat 4': list(range(1766, 1769)) + [1749],
    # T
    'teardown': list(range(906, 912)) + [1749],
    'terraria': list(range(1459, 1461)) + [1749],
    'the forest': list(range(633, 635)) + [1749],
    'the last of us': list(range(1119, 1152)) + [1749],
    'the long drive': list(range(1444, 1446)) + [1749],
    'the spike': list(range(846, 852)) + [1749],
    'the witcher 3': list(range(986, 1005)) + [1749],
    'third crisis': list(range(1302, 1305)) + [1749],
    'tomb raider 2013': list(range(1487, 1496)) + [1749],
    # U
    'uber soldier': list(range(197, 201)) + [1749],
    'undertale': list(range(1376, 1378)) + [1749],
    # W
    'warhammer 40000 gladius relics of war': list(range(1702, 1705)) + [1749],
    'watch dogs 2': list(range(1010, 1027)) + [1749],
    'witcher 3': list(range(986, 1005)) + [1749],
    'worldbox': list(range(1036, 1040)) + [1749],
    # КИРИЛЛИЦА
    'корсары 3': list(range(1370, 1372)) + [1749],
    # ДОП
    'arda launcher': list(range(1784, 1787)) + [1749],
}

# Временное хранилище состояний пользователей
user_states = {}


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def log_action(user_id, action, details=""):
    """Запись действия в БД и лог-файл"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO action_logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (str(user_id), action, details, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        logger.info(f"User {user_id}: {action} - {details}")
    except Exception as e:
        logger.error(f"Ошибка записи лога: {e}")


def get_or_create_user(user_id, username=None, first_name=None):
    """Получить или создать пользователя"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, first_seen, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        logger.info(f"Новый пользователь: {user_id} (@{username})")
    else:
        cursor.execute(
            "UPDATE users SET last_active = ?, username = ?, first_name = ? WHERE user_id = ?",
            (datetime.now().isoformat(), username, first_name, user_id)
        )
        conn.commit()

    conn.close()
    return True


def is_banned(user_id):
    """Проверка бана"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def is_muted(user_id):
    """Проверка мута"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_muted FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def is_admin(user_id):
    """Проверка админа"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def is_vip(user_id):
    """Проверка VIP статуса"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_vip, vip_until FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == 1:
        if result[1]:
            vip_until = datetime.fromisoformat(result[1])
            if vip_until > datetime.now():
                return True
    return False


def can_like(user_id):
    """Проверка возможности лайка"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT last_like FROM like_cooldowns WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return True, None

    last_like = datetime.fromisoformat(result[0])
    next_like = last_like + timedelta(days=LIKE_COOLDOWN_DAYS)

    if datetime.now() >= next_like:
        return True, None
    else:
        days_left = (next_like - datetime.now()).days
        return False, days_left


def update_like_cooldown(user_id):
    """Обновление кулдауна лайка"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO like_cooldowns (user_id, last_like) VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def clean_old_orders():
    """Очистка старых заказов"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    expire_date = (datetime.now() - timedelta(days=ORDER_EXPIRE_DAYS)).isoformat()
    cursor.execute("DELETE FROM orders WHERE created_date < ?", (expire_date,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted > 0:
        logger.info(f"Удалено {deleted} старых заказов")
        log_action("system", "clean_orders", f"Удалено {deleted} старых заказов")


def send_game_album(chat_id, game_name, user_id=None):
    """Отправка игры альбомом (группой файлов)"""
    if game_name not in GAMES_DATABASE:
        return False

    file_ids = GAMES_DATABASE[game_name]

    try:
        # Создаём медиагруппу
        media_group = []
        for i, file_id in enumerate(file_ids):
            # Последний файл с баннером
            if i == len(file_ids) - 1:
                media_group.append(
                    types.InputMediaDocument(
                        media=file_id,
                        caption=BANNER_TEXT
                    )
                )
            else:
                media_group.append(
                    types.InputMediaDocument(media=file_id)
                )

        # Отправляем группой
        bot.send_media_group(chat_id, media_group)
        logger.info(f"Отправлена игра {game_name} для {user_id}")

        # Обновляем статистику
        if user_id:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Обновляем счётчик скачиваний пользователя
            cursor.execute(
                "UPDATE users SET downloads = downloads + 1 WHERE user_id = ?",
                (user_id,)
            )

            # Обновляем счётчик скачиваний игры
            cursor.execute(
                "UPDATE games SET downloads = downloads + 1 WHERE game_name = ?",
                (game_name,)
            )

            # Если игры нет в БД, добавляем
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO games (game_name, file_ids, downloads, added_date) VALUES (?, ?, ?, ?)",
                    (game_name, ','.join(map(str, file_ids)), 1, datetime.now().isoformat())
                )

            conn.commit()
            conn.close()

        return True

    except Exception as e:
        logger.error(f"Ошибка отправки игры {game_name}: {e}")
        # Пробуем отправить по одному
        try:
            for i, file_id in enumerate(file_ids):
                if i == len(file_ids) - 1:
                    bot.copy_message(chat_id, GAMES_CHANNEL_ID, file_id, caption=BANNER_TEXT)
                else:
                    bot.copy_message(chat_id, GAMES_CHANNEL_ID, file_id)
                time.sleep(0.5)
            return True
        except Exception as e2:
            logger.error(f"Ошибка отправки по одному: {e2}")
            return False


# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return

    user = message.from_user
    get_or_create_user(user.id, user.username, user.first_name)

    if is_banned(user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        logger.warning(f"Заблокированный пользователь {user.id} пытался использовать бота")
        return

    log_action(user.id, "start", "Запуск бота")

    text = """🔍 <b>Напиши название игры</b> — я найду и отправлю.

📋 /orders — заказы
📝 /neworder — создать заказ
👤 /myorders — мои заказы
📊 /stats — статистика
🔥 /top — топ игр
📜 /history — история скачиваний
💰 /donate — поддержать проект

💡 <i>Нет игры?</i> → /neworder
━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | ❓ /help"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="my_stats"),
        types.InlineKeyboardButton("🔥 Топ игр", callback_data="show_top"),
        types.InlineKeyboardButton("💰 Поддержать", callback_data="show_donate"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== КОМАНДА HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    log_action(user_id, "help", "Открыл помощь")

    text = """━━━━━━━━━━━━━━━━━━
<b>📋 КОМАНДЫ БОТА</b>
━━━━━━━━━━━━━━━━━━

🔍 <b>Поиск игр</b>
Просто напиши название игры

📋 <b>Заказы</b>
/orders — все заказы
/neworder — создать заказ
/myorders — мои заказы

📊 <b>Статистика</b>
/stats — моя статистика
/top — топ игр
/history — история скачиваний

💰 <b>Поддержка</b>
/donate — поддержать проект
/vip — информация о VIP

👑 <b>Для админов</b>
/moderator — панель управления

━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | @FerwesGrid"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== КОМАНДА DONATE ==========
@bot.message_handler(commands=['donate'])
def donate_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    show_donate_menu(message.chat.id, user_id)


def show_donate_menu(chat_id, user_id):
    """Показать меню доната"""
    text = """💰 <b>ПОДДЕРЖАТЬ ПРОЕКТ</b>

Вы можете поддержать разработку бота, отправив Telegram Stars. В благодарность вы получите VIP-статус!

<b>VIP-статус даёт:</b>
✨ Безлимитные скачивания
✨ Приоритет в заказах
✨ Отключение рекламы
✨ Специальный значок в профиле

<b>Выберите сумму:</b>"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⭐ 10 Stars", callback_data="donate_10"),
        types.InlineKeyboardButton("⭐ 50 Stars", callback_data="donate_50"),
        types.InlineKeyboardButton("⭐ 100 Stars", callback_data="donate_100"),
        types.InlineKeyboardButton("⭐ 300 Stars", callback_data="donate_300"),
        types.InlineKeyboardButton("💫 500 Stars", callback_data="donate_500"),
        types.InlineKeyboardButton("🌟 1000 Stars", callback_data="donate_1000")
    )
    markup.add(types.InlineKeyboardButton("ℹ️ О VIP", callback_data="vip_info"))
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="back_to_start"))

    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
    log_action(user_id, "donate_menu", "Открыл меню доната")


@bot.message_handler(commands=['vip'])
def vip_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    vip_status = is_vip(user_id)

    if vip_status:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT vip_until, stars_donated FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        text = f"""💎 <b>VIP СТАТУС АКТИВЕН</b>

✨ Статус: Активен
📅 До: {datetime.fromisoformat(result[0]).strftime('%d.%m.%Y') if result[0] else 'Навсегда'}
💰 Пожертвовано: {result[1] if result[1] else 0} Stars

Спасибо за поддержку проекта!"""
    else:
        text = """💎 <b>VIP СТАТУС</b>

У вас нет активного VIP-статуса.

<b>VIP-статус даёт:</b>
✨ Безлимитные скачивания
✨ Приоритет в заказах
✨ Отключение рекламы
✨ Специальный значок в профиле

Используйте /donate чтобы поддержать проект!"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== КОМАНДА STATS ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    log_action(user_id, "stats", "Статистика")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Статистика пользователя
    cursor.execute(
        "SELECT downloads, created_orders, stars_donated, first_seen, is_vip FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = cursor.fetchone()

    if not user:
        bot.send_message(message.chat.id, "📊 У вас пока нет скачиваний\n\nНапиши название игры, чтобы начать!")
        conn.close()
        return

    downloads, created_orders, stars, first_seen, is_vip = user

    # Количество заказов пользователя
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    user_orders_count = cursor.fetchone()[0]

    # Количество лайков на заказах пользователя
    cursor.execute('''
        SELECT SUM(likes) FROM orders WHERE user_id = ?
    ''', (user_id,))
    total_likes = cursor.fetchone()[0] or 0

    conn.close()

    try:
        days_active = (datetime.now() - datetime.fromisoformat(first_seen)).days
    except:
        days_active = 0

    vip_badge = " 💎 VIP" if is_vip else ""

    text = f"""📊 <b>МОЯ СТАТИСТИКА</b>{vip_badge}

🎮 Скачано игр: {downloads}
📋 Создано заказов: {created_orders}
❤️ Получено лайков: {total_likes}
💰 Пожертвовано Stars: {stars}
📅 Дней в боте: {days_active}

━━━━━━━━━━━━━━━━━━
💡 /vip — информация о VIP статусе"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== КОМАНДА HISTORY ==========
@bot.message_handler(commands=['history'])
def history_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    log_action(user_id, "history", "История скачиваний")

    # В будущем можно добавить таблицу истории скачиваний
    bot.send_message(message.chat.id, "📜 История скачиваний пока в разработке")


# ========== КОМАНДА TOP ==========
@bot.message_handler(commands=['top'])
def top_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT game_name, downloads FROM games ORDER BY downloads DESC LIMIT 10"
    )
    top_games = cursor.fetchall()
    conn.close()

    if top_games:
        text = "🔥 <b>ТОП-10 ИГР</b>\n\n"
        for i, (game, downloads) in enumerate(top_games, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {game} — {downloads} 📥\n"

        bot.send_message(message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "📊 Нет данных")


# ========== КОМАНДА ORDERS ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    log_action(user_id, "orders", "Открыл заказы")
    show_orders_page(message.chat.id, 0)


def show_orders_page(chat_id, page=0):
    """Показать страницу заказов"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, user_id, game_name, size, likes, status, created_date FROM orders WHERE status = 'active' ORDER BY created_date DESC"
    )
    all_orders = cursor.fetchall()
    conn.close()

    if not all_orders:
        bot.send_message(chat_id, "📭 Нет активных заказов\n\nСоздайте первый через /neworder")
        return

    orders_per_page = 5
    total_pages = (len(all_orders) + orders_per_page - 1) // orders_per_page

    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0

    start_idx = page * orders_per_page
    end_idx = min(start_idx + orders_per_page, len(all_orders))
    page_orders = all_orders[start_idx:end_idx]

    text = f"📋 <b>ЗАКАЗЫ</b> (Страница {page + 1}/{total_pages})\n\n"

    for order in page_orders:
        order_id, user_id, game_name, size, likes, status, created_date = order

        try:
            date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y")
        except:
            date_str = "неизвестно"

        status_emoji = "🟢" if status == 'active' else "🔴"

        text += f"{status_emoji} <b>{game_name}</b>\n"
        text += f"📅 {date_str} | 💾 {size}\n"
        text += f"❤️ {likes} | 🆔 #{order_id}\n"
        text += "─\n"

    markup = types.InlineKeyboardMarkup(row_width=5)

    # Навигационные кнопки
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)

    # Кнопки лайков
    for order in page_orders[:3]:
        markup.add(types.InlineKeyboardButton(
            f"❤️ {order[2][:20]}",
            callback_data=f"like_{order[0]}"
        ))

    markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="back_to_start"))

    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== КОМАНДА NEWORDER ==========
@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    if is_muted(user_id):
        bot.send_message(message.chat.id, "🔇 Вы не можете создавать заказы")
        return

    log_action(user_id, "neworder", "Начал создание заказа")
    user_states[message.chat.id] = 'waiting_game'

    bot.send_message(
        message.chat.id,
        "📝 <b>НОВЫЙ ЗАКАЗ</b>\n\nВведите название игры:",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Отмена", callback_data="cancel_order")
        )
    )


@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_game')
def get_game_name(message):
    if message.chat.type != 'private':
        return

    game_name = message.text.strip()
    user_states[message.chat.id] = {
        'state': 'waiting_size',
        'game': game_name
    }

    bot.send_message(
        message.chat.id,
        f"🎮 <b>{game_name}</b>\n\nВведите размер игры (например: 50 ГБ):",
        parse_mode='HTML'
    )


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and isinstance(user_states[m.chat.id], dict) and user_states[
        m.chat.id].get('state') == 'waiting_size')
def get_game_size(message):
    if message.chat.type != 'private':
        return

    data = user_states[message.chat.id]
    game_name = data['game']
    size = message.text.strip().upper()
    user_id = message.from_user.id

    # Добавляем заказ в БД
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, game_name, size, created_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, game_name, size, datetime.now().isoformat()))
    order_id = cursor.lastrowid

    # Обновляем статистику пользователя
    cursor.execute(
        "UPDATE users SET created_orders = created_orders + 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

    del user_states[message.chat.id]
    log_action(user_id, "neworder_created", f"Заказ #{order_id}: {game_name} ({size})")

    text = f"""✅ <b>ЗАКАЗ #{order_id} СОЗДАН</b>

🎮 Игра: {game_name}
💾 Размер: {size}
📋 Статус: Ожидает

Спасибо за заказ! Мы постараемся добавить игру как можно скорее."""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Все заказы", callback_data="show_orders"))
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== КОМАНДА MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    log_action(user_id, "myorders", "Посмотрел свои заказы")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, game_name, size, likes, status, created_date FROM orders WHERE user_id = ? ORDER BY created_date DESC LIMIT 10",
        (user_id,)
    )
    user_orders = cursor.fetchall()
    conn.close()

    if not user_orders:
        bot.send_message(message.chat.id, "📭 У вас нет заказов\n\nСоздайте первый через /neworder")
        return

    text = "👤 <b>МОИ ЗАКАЗЫ</b>\n\n"
    for order in user_orders:
        order_id, game_name, size, likes, status, created_date = order
        status_emoji = "🟢" if status == 'active' else "🔴"
        text += f"{status_emoji} <b>{game_name}</b>\n"
        text += f"🆔 #{order_id} | 💾 {size}\n"
        text += f"❤️ {likes}\n"
        text += "─\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== КОМАНДА MODERATOR ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if not is_admin(message.from_user.id):
        return

    log_action(message.from_user.id, "moderator", "Открыл панель")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(downloads) FROM users")
    total_downloads = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_muted = 1")
    muted_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(stars_donated) FROM users")
    total_stars = cursor.fetchone()[0] or 0

    conn.close()

    text = f"""👑 <b>ПАНЕЛЬ МОДЕРАТОРА</b>

📊 <b>Статистика</b>
👥 Пользователей: {total_users}
📋 Заказов: {total_orders}
📥 Скачиваний: {total_downloads}
💰 Всего Stars: {total_stars}
🔨 Забанено: {banned_count}
🔇 Замучено: {muted_count}

━━━━━━━━━━━━━━━━━━
⚡ <b>Команды</b>
/delorder [ID] — удалить заказ
/ban [ID] — заблокировать
/unban [ID] — разблокировать
/mute [ID] — запретить заказы
/unmute [ID] — снять мут
/broadcast [текст] — рассылка
/logs — последние действия
/clean — очистить старые заказы
/addadmin [ID] — добавить админа
/givevip [ID] [дни] — выдать VIP"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== АДМИН-КОМАНДЫ ==========

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_action(message.from_user.id, "ban", f"Забанен {user_id}")
        bot.reply_to(message, f"✅ Пользователь {user_id} забанен")

        # Уведомляем пользователя
        try:
            bot.send_message(user_id, "🚫 Вы были заблокированы в боте")
        except:
            pass

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: /ban [ID]")
        logger.error(f"Ошибка бана: {e}")


@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_action(message.from_user.id, "unban", f"Разбанен {user_id}")
        bot.reply_to(message, f"✅ Пользователь {user_id} разбанен")

        try:
            bot.send_message(user_id, "✅ Вы были разблокированы в боте")
        except:
            pass

    except:
        bot.reply_to(message, "❌ /unban [ID]")


@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_muted = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_action(message.from_user.id, "mute", f"Замучен {user_id}")
        bot.reply_to(message, f"✅ Пользователь {user_id} замучен")

        try:
            bot.send_message(user_id, "🔇 Вам запрещено создавать заказы")
        except:
            pass

    except:
        bot.reply_to(message, "❌ /mute [ID]")


@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_muted = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        log_action(message.from_user.id, "unmute", f"Снят мут с {user_id}")
        bot.reply_to(message, f"✅ Мут снят с {user_id}")

        try:
            bot.send_message(user_id, "✅ Вам снова можно создавать заказы")
        except:
            pass

    except:
        bot.reply_to(message, "❌ /unmute [ID]")


@bot.message_handler(commands=['delorder'])
def delorder_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        order_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted:
            log_action(message.from_user.id, "delorder", f"Удалён заказ #{order_id}")
            bot.reply_to(message, f"✅ Заказ #{order_id} удалён")
        else:
            bot.reply_to(message, f"❌ Заказ #{order_id} не найден")

    except:
        bot.reply_to(message, "❌ /delorder [ID]")


@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        broadcast_text = message.text.split(' ', 1)[1]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
        users = cursor.fetchall()
        conn.close()

        sent = 0
        failed = 0

        for (user_id,) in users:
            try:
                bot.send_message(
                    user_id,
                    f"📢 <b>ОБЪЯВЛЕНИЕ</b>\n\n{broadcast_text}",
                    parse_mode='HTML'
                )
                sent += 1
                time.sleep(0.1)
            except:
                failed += 1

        log_action(message.from_user.id, "broadcast", f"Рассылка: {len(broadcast_text)} символов")
        bot.reply_to(message, f"✅ Отправлено: {sent}\n❌ Не отправлено: {failed}")

    except:
        bot.reply_to(message, "❌ /broadcast [текст]")


@bot.message_handler(commands=['logs'])
def logs_cmd(message):
    if not is_admin(message.from_user.id):
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, action, details, timestamp FROM action_logs ORDER BY log_id DESC LIMIT 30"
    )
    logs = cursor.fetchall()
    conn.close()

    if not logs:
        bot.reply_to(message, "📭 Лог пуст")
        return

    text = "📋 <b>ПОСЛЕДНИЕ ДЕЙСТВИЯ</b>\n\n"
    for log in logs:
        user_id, action, details, timestamp = log
        try:
            time_str = datetime.fromisoformat(timestamp).strftime("%d.%m %H:%M")
        except:
            time_str = "???"
        text += f"{time_str} | {user_id} | {action}\n"
        if details:
            text += f"   └ {details}\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['clean'])
def clean_cmd(message):
    if not is_admin(message.from_user.id):
        return

    clean_old_orders()
    bot.reply_to(message, f"✅ Старые заказы (старше {ORDER_EXPIRE_DAYS} дней) удалены")


@bot.message_handler(commands=['addadmin'])
def addadmin_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        new_admin_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (new_admin_id,))
        conn.commit()
        conn.close()

        log_action(message.from_user.id, "addadmin", f"Добавлен админ {new_admin_id}")
        bot.reply_to(message, f"✅ Пользователь {new_admin_id} стал админом")

    except:
        bot.reply_to(message, "❌ /addadmin [ID]")


@bot.message_handler(commands=['givevip'])
def givevip_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        parts = message.text.split()
        user_id = int(parts[1])
        days = int(parts[2]) if len(parts) > 2 else 30

        vip_until = (datetime.now() + timedelta(days=days)).isoformat()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_vip = 1, vip_until = ? WHERE user_id = ?",
            (vip_until, user_id)
        )
        conn.commit()
        conn.close()

        log_action(message.from_user.id, "givevip", f"Выдан VIP {user_id} на {days} дней")
        bot.reply_to(message, f"✅ VIP выдан пользователю {user_id} на {days} дней")

        try:
            bot.send_message(user_id, f"💎 Вам выдан VIP-статус на {days} дней! Спасибо за активность!")
        except:
            pass

    except:
        bot.reply_to(message, "❌ /givevip [ID] [дни]")


# ========== ПОИСК ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def search_handler(message):
    user_id = message.from_user.id

    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    query = message.text.strip().lower()
    log_action(user_id, "search", f"Поиск: {query}")

    # Точное совпадение
    if query in GAMES_DATABASE:
        bot.send_message(message.chat.id, f"🎮 <b>{message.text}</b>\n\n⏳ Загружаю файлы...", parse_mode='HTML')
        send_game_album(message.chat.id, query, user_id)
        return

    # Поиск похожих
    similar = []
    for game in GAMES_DATABASE.keys():
        if query in game or game in query:
            similar.append(game)

    if similar:
        text = f"❌ <b>'{message.text}' не найдено</b>\n\n🎯 <i>Возможно вы искали:</i>"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for game in similar[:5]:
            markup.add(types.InlineKeyboardButton(
                f"🎮 {game.title()}",
                callback_data=f"play_{game}"
            ))
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    else:
        text = f"❌ <b>'{message.text}' не найдено</b>\n\n📝 Создайте заказ через /neworder"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== CALLBACK ОБРАБОТЧИК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    # Лайк заказа
    if call.data.startswith('like_'):
        if is_banned(user_id):
            bot.answer_callback_query(call.id, "❌ Вы заблокированы")
            return

        can_like_now, days_left = can_like(user_id)
        if not can_like_now:
            bot.answer_callback_query(call.id, f"❌ Следующий лайк через {days_left} дней", show_alert=True)
            return

        order_id = int(call.data.split('_')[1])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Проверяем, не лайкал ли уже
        cursor.execute(
            "SELECT * FROM order_likes WHERE order_id = ? AND user_id = ?",
            (order_id, user_id)
        )
        if cursor.fetchone():
            bot.answer_callback_query(call.id, "❌ Вы уже лайкали этот заказ")
            conn.close()
            return

        # Добавляем лайк
        cursor.execute(
            "INSERT INTO order_likes (order_id, user_id, liked_date) VALUES (?, ?, ?)",
            (order_id, user_id, datetime.now().isoformat())
        )
        cursor.execute(
            "UPDATE orders SET likes = likes + 1 WHERE order_id = ?",
            (order_id,)
        )
        conn.commit()
        conn.close()

        update_like_cooldown(user_id)
        log_action(user_id, "like", f"Лайк заказа #{order_id}")
        bot.answer_callback_query(call.id, "❤️ Лайк поставлен!")

        # Обновляем сообщение
        try:
            show_orders_page(call.message.chat.id, 0)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    # Отправка игры
    elif call.data.startswith('play_'):
        game_name = call.data[5:]
        bot.answer_callback_query(call.id, f"⏳ Загружаю {game_name}...")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_game_album(call.message.chat.id, game_name, user_id)

    # Навигация по страницам заказов
    elif call.data.startswith('orders_page_'):
        page = int(call.data.split('_')[2])
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_orders_page(call.message.chat.id, page)

    # Донаты
    elif call.data.startswith('donate_'):
        amount = int(call.data.split('_')[1])

        # Создаём счёт на оплату Stars
        prices = {
            10: [types.LabeledPrice("Поддержка проекта", 10)],
            50: [types.LabeledPrice("Поддержка проекта", 50)],
            100: [types.LabeledPrice("Поддержка проекта", 100)],
            300: [types.LabeledPrice("Поддержка проекта", 300)],
            500: [types.LabeledPrice("Поддержка проекта", 500)],
            1000: [types.LabeledPrice("Поддержка проекта", 1000)]
        }

        try:
            bot.send_invoice(
                chat_id=call.message.chat.id,
                title="Поддержка Ferwes Games",
                description=f"Пожертвование {amount} Stars на развитие бота",
                invoice_payload=f"donate_{user_id}_{amount}",
                provider_token="",  # Пусто для Telegram Stars
                currency="XTR",
                prices=prices[amount]
            )
            bot.answer_callback_query(call.id, "✅ Счёт создан")
            log_action(user_id, "donate_invoice", f"Счёт на {amount} Stars")
        except Exception as e:
            logger.error(f"Ошибка создания счёта: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка создания счёта")

    elif call.data == "show_donate":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_donate_menu(call.message.chat.id, user_id)

    elif call.data == "vip_info":
        bot.answer_callback_query(call.id)
        vip_cmd(call.message)

    # Навигация меню
    elif call.data == "show_orders":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        orders_cmd(call.message)

    elif call.data == "new_order":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        neworder_cmd(call.message)

    elif call.data == "my_orders":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        myorders_cmd(call.message)

    elif call.data == "my_stats":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        stats_cmd(call.message)

    elif call.data == "show_top":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        top_cmd(call.message)

    elif call.data == "show_help":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        help_cmd(call.message)

    elif call.data == "back_to_start":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_cmd(call.message)

    elif call.data == "cancel_order":
        if call.message.chat.id in user_states:
            del user_states[call.message.chat.id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "❌ Создание заказа отменено")
        start_cmd(call.message)

    elif call.data == "current_page":
        bot.answer_callback_query(call.id, f"Страница {call.message.text.split('/')[0].split()[-1]}")


# ========== ОБРАБОТЧИК УСПЕШНОЙ ОПЛАТЫ ==========
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout_handler(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def successful_payment_handler(message):
    user_id = message.from_user.id
    payment = message.successful_payment

    # Извлекаем сумму из payload
    try:
        amount = int(payment.invoice_payload.split('_')[-1])
    except:
        amount = 0

    # VIP на 30 дней за каждые 100 Stars
    vip_days = (amount // 100) * 30
    if vip_days == 0:
        vip_days = 30

    vip_until = (datetime.now() + timedelta(days=vip_days)).isoformat()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET stars_donated = stars_donated + ?, is_vip = 1, vip_until = ? WHERE user_id = ?",
        (amount, vip_until, user_id)
    )
    conn.commit()
    conn.close()

    log_action(user_id, "donate_success", f"Оплачено {amount} Stars, VIP на {vip_days} дней")
    logger.info(f"Пользователь {user_id} оплатил {amount} Stars")

    text = f"""✅ <b>СПАСИБО ЗА ПОДДЕРЖКУ!</b>

💰 Оплачено: {amount} Stars
💎 VIP-статус активирован на {vip_days} дней!

Спасибо, что поддерживаете развитие бота! ❤️"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК FERWES GAMES БОТА v2.0")
    print("=" * 60)

    logger.info("=" * 50)
    logger.info("ЗАПУСК БОТА")
    logger.info(f"Токен: {BOT_TOKEN[:10]}...")
    logger.info(f"База данных: {DB_FILE}")
    logger.info("=" * 50)

    # Очистка старых заказов при запуске
    clean_old_orders()

    print(f"🎮 Игр в базе: {len(GAMES_DATABASE)}")
    print("💾 База данных: SQLite")
    print("📝 Логирование: bot.log")
    print("=" * 60)
    print("⚡ Бот запущен и готов к работе!")
    print("=" * 60)

    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        time.sleep(10)