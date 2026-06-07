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
from difflib import SequenceMatcher

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
BOT_TOKEN = '8456295069:AAGz48djuL19fYnn9FCz8DgJRQgIO6rLlq0'
bot = telebot.TeleBot(BOT_TOKEN)
GAMES_CHANNEL_ID = -1003421344618
BANNER_ID = 1749  # ID сообщения с баннером

# Константы
LIKE_COOLDOWN_DAYS = 1000
ORDER_EXPIRE_DAYS = 60
ALBUM_BATCH_SIZE = 10  # Максимум файлов в одном альбоме
PRIORITY_COST = 50  # Стоимость приоритетного заказа в Stars

# ========== БАЗА ДАННЫХ SQLITE ==========
import os as _os

DATA_DIR = _os.getenv('DATA_DIR', '.')
DB_FILE = _os.path.join(DATA_DIR, 'bot_database.db')


def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

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
            is_muted BOOLEAN DEFAULT 0
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
            created_date TIMESTAMP,
            anonymous BOOLEAN DEFAULT 0,
            priority BOOLEAN DEFAULT 0,
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
            order_id INTEGER,
            user_id INTEGER,
            liked_date TIMESTAMP,
            PRIMARY KEY (order_id, user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS like_cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_like TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE,
            file_ids TEXT,
            downloads INTEGER DEFAULT 0,
            added_date TIMESTAMP
        )
    ''')

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


init_database()


def init_admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (7885915159,))
    conn.commit()
    conn.close()


init_admin()

# ========== СИНОНИМЫ ДЛЯ FUZZY-ПОИСКА ==========
GAME_SYNONYMS = {
    'гта 5': 'Grand Theft Auto V',
    'гта 4': 'Grand Theft Auto IV',
    'гта 3': 'Grand Theft Auto III',
    'гта са': 'Grand Theft Auto: San Andreas',
    'гта вайс': 'Grand Theft Auto: Vice City',
    'форза 5': 'forza horizon 5',
    'форза хорайзон 5': 'forza horizon 5',
    'сталкер': 'stalker anomaly',
    'сталкер зов припяти': 'stalker call of pripyat',
    'сталкер тень чернобыля': 'stalker shadow of chernobyl',
    'майнкрафт': 'minecraft',
    'кс 1.6': 'counter strike 1.6',
    'контра': 'counter strike 1.6',
    'симс 4': 'sims 4',
    'ведьмак 3': 'the witcher 3',
    'киберпанк': 'cyberpunk 2077',
    'ред дед 2': 'red dead redemption 2',
    'палворд': 'palworld',
    'скайрим': 'skyrim',
}

# ========== БАЗА ВСЕХ ИГР ==========
GAMES_DATABASE = {
    # A
    'antonblast': [913, 914],
    'assassins creed': list(range(1028, 1033)),
    'artmoney': [1770, 1771],
    # B
    'bad cheese': list(range(1651, 1654)),
    'battlefield 3': list(range(1773, 1784)),
    'BeamNG drive': list(range(861, 873)),
    'beholder': list(range(823, 825)),
    'bendy and the ink machine': list(range(652, 654)),
    'bioshock remaster': list(range(1070, 1080)),
    'blender': list(range(1306, 1310)),
    'borderlands 2': list(range(776, 782)),
    'bully': list(range(1639, 1642)),
    # C
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
    # D
    'dark souls 3': list(range(880, 894)),
    'dead space': list(range(1576, 1580)),
    'dead space remake': list(range(1581, 1599)),
    'detroit become human': list(range(1407, 1436)),
    'devil may cry 4': list(range(1244, 1258)),
    'dispatch': list(range(1311, 1320)),
    'distant worlds 2': list(range(1644, 1650)),
    'doom the dark ages': list(range(1706, 1748)),
    'dying light: the beast': list(range(1502, 1525)),
    # E
    'elden ring': list(range(552, 587)),
    'endoparasitic': [1942, 1943],
    # F
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
    # G
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
    # H
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
    # I
    'inscription': [1897],
    # J
    'jewel match': list(range(234, 236)),
    # K
    'korsary 3': list(range(1370, 1372)),
    # L
    'left 4 dead 2': list(range(1207, 1211)),
    'little nightmares 3': list(range(174, 182)),
    'lonarpg': list(range(1447, 1449)),
    # M
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
    # N
    'nier automata': list(range(164, 173)),
    'nier replicant': list(range(1670, 1682)),
    'no im not a human': list(range(517, 520)),
    'no mans sky': list(range(1751, 1765)),
    # O
    'one shot': list(range(1065, 1069)),
    'orion sandbox': list(range(814, 816)),
    # P
    'palworld': list(range(202, 216)),
    'payday the heist': list(range(876, 879)),
    'people playground': list(range(1603, 1605)),
    'plants vs zombies': list(range(549, 551)),
    'portal 2': list(range(1207, 1211)),
    'portal knights': list(range(1237, 1239)),
    'postal 2': list(range(1615, 1617)),
    'pragmata': list(range(1901, 1920)),
    'project zomboid': list(range(1093, 1095)),
    'prototype 1': list(range(895, 901)),
    'prototype 2': list(range(1044, 1050)),
    # Q
    'quasimorph': list(range(589, 591)),
    # R
    'rauniot': list(range(1926, 1937)),
    'red dead redemption': list(range(542, 548)),
    'red dead redemption 2': list(range(428, 485)),
    'resident evil revelations 2': list(range(788, 798)),
    'resident evil village': list(range(826, 845)),
    'rimworld': list(range(1298, 1301)),
    'risk of rain 2': list(range(1612, 1614)),
    'rock star life simulator': list(range(184, 186)),
    # S
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
    # T
    'teardown': list(range(906, 912)),
    'terraria': list(range(1459, 1461)),
    'the forest': list(range(633, 635)),
    'the last of us': list(range(1119, 1152)),
    'the long drive': list(range(1444, 1446)),
    'the spike': list(range(846, 852)),
    'the witcher 3': list(range(986, 1005)),
    'third crisis': list(range(1302, 1305)),
    'tomb raider 2013': list(range(1487, 1496)),
    # U
    'uber soldier': list(range(197, 201)),
    'undertale': list(range(1376, 1378)),
    # W
    'warhammer 40000 gladius relics of war': list(range(1702, 1705)),
    'watch dogs 2': list(range(1010, 1027)),
    'witcher 3': list(range(986, 1005)),
    'worldbox': list(range(1036, 1040)),
    # КИРИЛЛИЦА
    'корсары 3': list(range(1370, 1372)),
    # ДОП
    'arda launcher': list(range(1784, 1787)),
}

user_states = {}


# ========== FUZZY-ПОИСК ==========
def fuzzy_search(query, threshold=0.6):
    """Умный поиск с поддержкой опечаток и синонимов"""
    query = query.lower().strip()

    # Проверяем синонимы
    if query in GAME_SYNONYMS:
        return GAME_SYNONYMS[query], 1.0

    # Точное совпадение
    if query in GAMES_DATABASE:
        return query, 1.0

    # Поиск по подстроке
    for game in GAMES_DATABASE:
        if query in game.lower() or game.lower() in query:
            return game, 0.8

    # Fuzzy-поиск по схожести
    best_match = None
    best_score = 0

    for game in GAMES_DATABASE:
        score = SequenceMatcher(None, query, game.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = game

    return best_match, best_score


def find_similar_games(query, limit=5):
    """Находит похожие игры для предложения"""
    query = query.lower().strip()
    results = []

    # Проверяем синонимы
    for synonym, game in GAME_SYNONYMS.items():
        if query in synonym or synonym in query:
            if game not in results:
                results.append(game)

    # Поиск по подстроке
    for game in GAMES_DATABASE:
        if query in game.lower():
            if game not in results:
                results.append(game)

    # Fuzzy-поиск
    if len(results) < limit:
        scored = []
        for game in GAMES_DATABASE:
            if game not in results:
                score = SequenceMatcher(None, query, game.lower()).ratio()
                if score > 0.4:
                    scored.append((game, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        for game, _ in scored[:limit - len(results)]:
            results.append(game)

    return results[:limit]


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def escape_html(text):
    """Экранирует HTML-теги"""
    if text is None:
        return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def log_action(user_id, action, details=""):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO action_logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (str(user_id), action, details, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка записи лога: {e}")


def get_or_create_user(user_id, username=None, first_name=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, first_seen, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now().isoformat(), datetime.now().isoformat()))
    else:
        cursor.execute(
            "UPDATE users SET last_active = ?, username = ?, first_name = ? WHERE user_id = ?",
            (datetime.now().isoformat(), username, first_name, user_id)
        )
    conn.commit()
    conn.close()
    return True


def is_banned(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def is_muted(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT is_muted FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1


def is_admin(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def can_like(user_id):
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
    return False, (next_like - datetime.now()).days


def update_like_cooldown(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO like_cooldowns (user_id, last_like) VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def clean_old_orders():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        expire_date = (datetime.now() - timedelta(days=ORDER_EXPIRE_DAYS)).isoformat()
        cursor.execute("DELETE FROM orders WHERE created_date < ?", (expire_date,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            logger.info(f"Удалено {deleted} старых заказов")
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")


def send_game_files(chat_id, game_name, user_id=None):
    """Отправка игры АЛЬБОМАМИ по 10 файлов"""
    if game_name not in GAMES_DATABASE:
        return False

    file_ids = GAMES_DATABASE[game_name]
    total_files = len(file_ids)

    # Сообщение о начале загрузки
    status_msg = bot.send_message(
        chat_id,
        f"📦 Отправка: 0/{total_files} файлов...",
        parse_mode='HTML'
    )

    try:
        for i in range(0, total_files, ALBUM_BATCH_SIZE):
            batch = file_ids[i:i + ALBUM_BATCH_SIZE]
            media_group = []

            for fid in batch:
                media_group.append(types.InputMediaDocument(media=fid))

            bot.send_media_group(chat_id, media_group)

            # Обновляем прогресс
            sent = min(i + ALBUM_BATCH_SIZE, total_files)
            try:
                bot.edit_message_text(
                    f"📦 Отправка: {sent}/{total_files} файлов...",
                    chat_id,
                    status_msg.message_id,
                    parse_mode='HTML'
                )
            except:
                pass

            time.sleep(0.5)

        # Отправляем баннер
        bot.copy_message(chat_id, GAMES_CHANNEL_ID, BANNER_ID)

        # Удаляем сообщение о прогрессе
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except:
            pass

        # Статистика
        if user_id:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE user_id = ?", (user_id,))
            cursor.execute("UPDATE games SET downloads = downloads + 1 WHERE game_name = ?", (game_name,))
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO games (game_name, file_ids, downloads, added_date) VALUES (?, ?, ?, ?)",
                    (game_name, ','.join(map(str, file_ids)), 1, datetime.now().isoformat())
                )
            conn.commit()
            conn.close()

        return True

    except Exception as e:
        logger.error(f"Ошибка отправки {game_name}: {e}")
        # Запасной вариант
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except:
            pass

        for fid in file_ids:
            try:
                bot.copy_message(chat_id, GAMES_CHANNEL_ID, fid)
                time.sleep(0.2)
            except:
                pass
        bot.copy_message(chat_id, GAMES_CHANNEL_ID, BANNER_ID)
        return True


# ========== АДМИН-ПАНЕЛЬ ==========
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'active'")
    active_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE priority = 1 AND status = 'active'")
    priority_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(downloads) FROM users")
    total_downloads = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(stars_donated) FROM users")
    total_stars = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    banned = cursor.fetchone()[0]

    conn.close()

    text = f"""<b>👑 АДМИН-ПАНЕЛЬ v8.0</b>

━━━━━━━━━━━━━━━━━━
<b>📊 СТАТИСТИКА</b>
━━━━━━━━━━━━━━━━━━
👥 Пользователей: {total_users}
📋 Активных заказов: {active_orders}
🔴 Приоритетных: {priority_orders}
📥 Всего скачиваний: {total_downloads}
💰 Собрано Stars: {total_stars}
🔨 Забанено: {banned}

━━━━━━━━━━━━━━━━━━
<b>⚡ ДЕЙСТВИЯ</b>
━━━━━━━━━━━━━━━━━━
/make_priority [ID] — Приоритет заказу
/remove_priority [ID] — Убрать приоритет
/complete_order [ID] — Завершить заказ
/ban [ID] — Забанить
/unban [ID] — Разбанить
/mute [ID] — Замутить
/unmute [ID] — Размутить
/delorder [ID] — Удалить заказ
/broadcast [текст] — Рассылка
/logs — Логи
/clean — Очистка старых заказов"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== УПРАВЛЕНИЕ ПРИОРИТЕТАМИ ==========
@bot.message_handler(commands=['make_priority'])
def make_priority_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        order_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET priority = 1 WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"🔴 Заказ #{order_id} теперь приоритетный!")
    except:
        bot.reply_to(message, "❌ /make_priority [ID]")


@bot.message_handler(commands=['remove_priority'])
def remove_priority_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        order_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET priority = 0 WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"🔵 Приоритет снят с заказа #{order_id}")
    except:
        bot.reply_to(message, "❌ /remove_priority [ID]")


@bot.message_handler(commands=['complete_order'])
def complete_order_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        order_id = int(message.text.split()[1])
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = 'done' WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Заказ #{order_id} завершён!")
    except:
        bot.reply_to(message, "❌ /complete_order [ID]")


# ========== ОСТАЛЬНЫЕ АДМИН-КОМАНДЫ ==========
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
        log_action(message.from_user.id, "ban", str(user_id))
        bot.reply_to(message, f"✅ Пользователь {user_id} забанен")
    except:
        bot.reply_to(message, "❌ /ban [ID]")


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
        bot.reply_to(message, f"✅ Пользователь {user_id} разбанен")
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
        bot.reply_to(message, f"✅ Пользователь {user_id} замучен")
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
        bot.reply_to(message, f"✅ Мут снят с {user_id}")
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
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Заказ #{order_id} удалён")
    except:
        bot.reply_to(message, "❌ /delorder [ID]")


@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return
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

        bot.reply_to(message, f"✅ Отправлено: {sent} из {len(users)}")
    except:
        bot.reply_to(message, "❌ /broadcast [текст]")


@bot.message_handler(commands=['logs'])
def logs_cmd(message):
    if not is_admin(message.from_user.id):
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, action, details, timestamp FROM action_logs ORDER BY log_id DESC LIMIT 20")
    logs = cursor.fetchall()
    conn.close()

    if not logs:
        bot.reply_to(message, "📭 Логи пусты")
        return

    text = "<b>📋 ПОСЛЕДНИЕ ДЕЙСТВИЯ</b>\n\n"
    for log in logs:
        uid, action, details, ts = log
        try:
            time_str = datetime.fromisoformat(ts).strftime("%d.%m %H:%M")
        except:
            time_str = "???"
        text += f"{time_str} | {uid} | {action}"
        if details:
            text += f" ({details})"
        text += "\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


@bot.message_handler(commands=['clean'])
def clean_cmd(message):
    if not is_admin(message.from_user.id):
        return
    clean_old_orders()
    bot.reply_to(message, "✅ Старые заказы очищены")


# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return

    user = message.from_user
    get_or_create_user(user.id, user.username, user.first_name)

    if is_banned(user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    text = f"""Привет, {escape_html(user.first_name)}!

🔍 <b>Напиши название игры</b> — я найду и отправлю.

📋 /orders — заказы (🔴 приоритет, 🔵 обычный)
📝 /neworder — создать заказ
👤 /myorders — мои заказы
📊 /stats — статистика
🔥 /top — топ игр
💰 /donate — поддержать автора

💡 Нет игры? → /neworder
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

    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    text = """━━━━━━━━━━━━━━━━━━
<b>КОМАНДЫ БОТА</b>
━━━━━━━━━━━━━━━━━━

🔍 <b>Поиск игр</b>
Просто напиши название игры
Понимает опечатки и синонимы!

📋 <b>Заказы</b>
/orders — все заказы
/neworder — создать заказ
/myorders — мои заказы

📊 <b>Статистика</b>
/stats — моя статистика
/top — топ игр

💰 <b>Поддержка</b>
/donate — поддержать автора

━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | @FerwesGrid"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== КОМАНДА DONATE ==========
@bot.message_handler(commands=['donate'])
def donate_cmd(message):
    if message.chat.type != 'private':
        return

    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    show_donate_menu(message.chat.id, message.from_user.id)


def show_donate_menu(chat_id, user_id):
    text = f"""💰 <b>ПОДДЕРЖАТЬ АВТОРА</b>

Поддержите развитие бота звёздами Telegram!

⭐ {PRIORITY_COST} Stars = 🔴 Приоритетный заказ (выполняется быстрее)

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
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="back_to_start"))

    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== КОМАНДА STATS ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT downloads, created_orders, stars_donated, first_seen FROM users WHERE user_id = ?",
                   (user_id,))
    user = cursor.fetchone()

    if not user:
        bot.send_message(message.chat.id, "📊 У вас пока нет скачиваний\n\nНапиши название игры, чтобы начать!")
        conn.close()
        return

    downloads, created_orders, stars, first_seen = user
    cursor.execute("SELECT SUM(likes) FROM orders WHERE user_id = ?", (user_id,))
    total_likes = cursor.fetchone()[0] or 0
    conn.close()

    try:
        days_active = (datetime.now() - datetime.fromisoformat(first_seen)).days
    except:
        days_active = 0

    text = f"""📊 <b>МОЯ СТАТИСТИКА</b>

🎮 Скачано игр: {downloads}
📋 Создано заказов: {created_orders}
❤️ Получено лайков: {total_likes}
💰 Пожертвовано Stars: {stars}
📅 Дней в боте: {days_active}

━━━━━━━━━━━━━━━━━━
💰 /donate — поддержать автора"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== КОМАНДА TOP ==========
@bot.message_handler(commands=['top'])
def top_cmd(message):
    if message.chat.type != 'private':
        return

    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT game_name, downloads FROM games ORDER BY downloads DESC LIMIT 10")
    top_games = cursor.fetchall()
    conn.close()

    if top_games:
        text = "🔥 <b>ТОП-10 ИГР</b>\n\n"
        for i, (game, downloads) in enumerate(top_games, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {escape_html(game)} — {downloads} 📥\n"
        bot.send_message(message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "📊 Нет данных")


# ========== КОМАНДА ORDERS (С ПРИОРИТЕТАМИ) ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return

    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    show_orders_page(message.chat.id, 0)


def show_orders_page(chat_id, page=0):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.game_name, o.size, o.likes, o.status, o.created_date, o.anonymous, o.priority, u.username 
        FROM orders o 
        LEFT JOIN users u ON o.user_id = u.user_id 
        WHERE o.status = 'active' 
        ORDER BY o.priority DESC, o.created_date DESC
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

    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0

    start_idx = page * orders_per_page
    end_idx = min(start_idx + orders_per_page, len(all_orders))
    page_orders = all_orders[start_idx:end_idx]

    priority_count = sum(1 for o in all_orders if o[8] == 1)

    text = f"📋 <b>ЗАКАЗЫ</b> ({len(all_orders)} всего)\n"
    text += f"🔴 Приоритетных: {priority_count} | 🔵 Обычных: {len(all_orders) - priority_count}\n"
    text += f"📄 Страница {page + 1}/{total_pages}\n"
    text += "━\n"

    for order in page_orders:
        order_id, user_id, game_name, size, likes, status, created_date, anonymous, priority, username = order

        try:
            date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y")
        except:
            date_str = "неизвестно"

        # 🔴 Приоритет / 🔵 Обычный
        priority_emoji = "🔴" if priority else "🔵"
        priority_text = "ПРИОРИТЕТ" if priority else "Обычный"

        if anonymous:
            author = "Аноним"
        elif username:
            author = f"@{username}"
        else:
            author = f"ID:{user_id}"

        text += f"{priority_emoji} <b>#{order_id}</b> | {escape_html(game_name)}\n"
        text += f"👤 {author} | 💾 {size}\n"
        text += f"📅 {date_str} | ❤️ {likes} | {priority_text}\n"
        text += "━\n"

    markup = types.InlineKeyboardMarkup(row_width=5)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)

    like_buttons = []
    for order in page_orders[:3]:
        short_name = escape_html(order[2][:15])
        like_buttons.append(types.InlineKeyboardButton(
            f"❤️ {short_name}",
            callback_data=f"like_{order[0]}"
        ))
    if like_buttons:
        markup.row(*like_buttons)

    markup.add(
        types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders")
    )
    markup.add(types.InlineKeyboardButton("Главное меню", callback_data="back_to_start"))

    try:
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
    except:
        clean_text = re.sub(r'<[^>]+>', '', text)
        bot.send_message(chat_id, clean_text, reply_markup=markup)


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

    user_states[message.chat.id] = {'state': 'waiting_game'}

    bot.send_message(
        message.chat.id,
        "📝 <b>НОВЫЙ ЗАКАЗ</b>\n\nВведите название игры:",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Отмена", callback_data="cancel_order")
        )
    )


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and user_states[m.chat.id].get('state') == 'waiting_game')
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
        f"🎮 <b>{escape_html(game_name)}</b>\n\nВведите размер игры в ГБ (только цифры):",
        parse_mode='HTML'
    )


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and isinstance(user_states[m.chat.id], dict) and user_states[
        m.chat.id].get('state') == 'waiting_size')
def get_game_size(message):
    if message.chat.type != 'private':
        return

    size_input = message.text.strip()

    if not re.match(r'^[\d.]+$', size_input):
        bot.send_message(
            message.chat.id,
            "❌ <b>Ошибка!</b>\n\nРазмер должен содержать только цифры!\nНапример: 50 или 12.5\n\nПопробуйте ещё раз:",
            parse_mode='HTML'
        )
        return

    size = f"{size_input} ГБ"
    data = user_states[message.chat.id]
    data['size'] = size
    data['state'] = 'waiting_priority'

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔵 Обычный (бесплатно)", callback_data="priority_no"),
        types.InlineKeyboardButton(f"🔴 Приоритет ({PRIORITY_COST} ⭐)", callback_data="priority_yes")
    )
    markup.add(types.InlineKeyboardButton("Отмена", callback_data="cancel_order"))

    bot.send_message(
        message.chat.id,
        f"🎮 <b>{escape_html(data['game'])}</b>\n💾 Размер: {size}\n\n<b>Тип заказа:</b>\n🔵 Обычный — бесплатно\n🔴 Приоритет — {PRIORITY_COST} Stars (выполняется быстрее)",
        parse_mode='HTML',
        reply_markup=markup
    )


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
    priority = call.data == 'priority_yes'
    user_id = call.from_user.id

    if priority:
        # Проверяем, хватает ли звёзд
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT stars_donated FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        stars = result[0] if result else 0
        conn.close()

        if stars < PRIORITY_COST:
            bot.answer_callback_query(call.id, f"❌ Недостаточно Stars! Нужно {PRIORITY_COST}, у вас {stars}",
                                      show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            del user_states[call.message.chat.id]
            return

        # Списываем звёзды
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET stars_donated = stars_donated - ? WHERE user_id = ?", (PRIORITY_COST, user_id))
        conn.commit()
        conn.close()

    data['state'] = 'waiting_anonymous'
    data['priority'] = priority
    user_states[call.message.chat.id] = data

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 Открыто", callback_data="anon_no"),
        types.InlineKeyboardButton("👻 Анонимно", callback_data="anon_yes")
    )

    priority_text = "🔴 Приоритетный" if priority else "🔵 Обычный"

    bot.send_message(
        call.message.chat.id,
        f"🎮 <b>{escape_html(data['game'])}</b>\n💾 Размер: {data['size']}\n{priority_text}\n\n<b>Опубликовать анонимно?</b>",
        parse_mode='HTML',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('anon_'))
def anonymous_choice(call):
    if call.message.chat.id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return

    data = user_states[call.message.chat.id]
    anonymous = call.data == 'anon_yes'
    priority = data.get('priority', False)
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, game_name, size, created_date, anonymous, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, data['game'], data['size'], datetime.now().isoformat(), 1 if anonymous else 0, 1 if priority else 0))
    order_id = cursor.lastrowid

    cursor.execute("UPDATE users SET created_orders = created_orders + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    del user_states[call.message.chat.id]
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    anon_text = "👻 Анонимно" if anonymous else "👤 Открыто"
    priority_text = "🔴 Приоритетный" if priority else "🔵 Обычный"

    text = f"""✅ <b>ЗАКАЗ #{order_id} СОЗДАН</b>

🎮 Игра: {escape_html(data['game'])}
💾 Размер: {data['size']}
{priority_text}
{anon_text}

Спасибо за заказ!"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Все заказы", callback_data="show_orders"))
    markup.add(types.InlineKeyboardButton("Главное меню", callback_data="back_to_start"))

    bot.send_message(call.message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    bot.answer_callback_query(call.id)


# ========== КОМАНДА MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, game_name, size, likes, status, created_date, anonymous, priority FROM orders WHERE user_id = ? ORDER BY created_date DESC LIMIT 10",
        (user_id,)
    )
    user_orders = cursor.fetchall()
    conn.close()

    if not user_orders:
        text = "👤 <b>МОИ ЗАКАЗЫ</b>\n\n📭 У вас пока нет заказов.\n\nСоздайте первый через /neworder"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
        return

    text = f"👤 <b>МОИ ЗАКАЗЫ</b> ({len(user_orders)} шт.)\n\n"
    for order in user_orders:
        order_id, game_name, size, likes, status, created_date, anonymous, priority = order
        priority_emoji = "🔴" if priority else "🔵"
        anon_badge = " 👻" if anonymous else ""
        status_text = "Активен" if status == 'active' else "Завершён"
        text += f"{priority_emoji} <b>#{order_id}</b> | {escape_html(game_name)}\n"
        text += f"💾 {size} | ❤️ {likes} | {status_text}{anon_badge}\n"
        text += "━\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== ПОИСК ИГР (С FUZZY) ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def search_handler(message):
    user_id = message.from_user.id

    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    query = message.text.strip()

    # Fuzzy-поиск
    match, score = fuzzy_search(query)

    if match and score >= 0.8:
        total_files = len(GAMES_DATABASE[match])
        bot.send_message(
            message.chat.id,
            f"🎮 <b>{escape_html(match)}</b>\n📦 Файлов: {total_files}\n\n⏳ Загружаю...",
            parse_mode='HTML'
        )
        send_game_files(message.chat.id, match, user_id)
        return

    # Похожие игры
    similar = find_similar_games(query)

    if similar:
        text = f"❌ <b>'{escape_html(query)}' не найдено</b>\n\n🎯 <i>Возможно вы искали:</i>"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for game in similar[:5]:
            markup.add(types.InlineKeyboardButton(
                f"🎮 {game}",
                callback_data=f"play_{game}"
            ))
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    else:
        text = f"❌ <b>'{escape_html(query)}' не найдено</b>\n\n📝 Создайте заказ через /neworder"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== CALLBACK ОБРАБОТЧИК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data.startswith('like_'):
        if is_banned(user_id):
            bot.answer_callback_query(call.id, "❌ Вы заблокированы")
            return

        can, days_left = can_like(user_id)
        if not can:
            bot.answer_callback_query(call.id, f"❌ Следующий лайк через {days_left} дней", show_alert=True)
            return

        order_id = int(call.data.split('_')[1])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM order_likes WHERE order_id = ? AND user_id = ?", (order_id, user_id))
        if cursor.fetchone():
            bot.answer_callback_query(call.id, "❌ Вы уже лайкали этот заказ")
            conn.close()
            return

        cursor.execute(
            "INSERT INTO order_likes (order_id, user_id, liked_date) VALUES (?, ?, ?)",
            (order_id, user_id, datetime.now().isoformat())
        )
        cursor.execute("UPDATE orders SET likes = likes + 1 WHERE order_id = ?", (order_id,))
        conn.commit()
        conn.close()

        update_like_cooldown(user_id)
        bot.answer_callback_query(call.id, "❤️ Лайк поставлен!")

    elif call.data.startswith('play_'):
        game_name = call.data[5:]
        bot.answer_callback_query(call.id, f"⏳ Загружаю {game_name}...")
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

        prices = {
            10: [types.LabeledPrice("Поддержка автора", 10)],
            50: [types.LabeledPrice("Поддержка автора", 50)],
            100: [types.LabeledPrice("Поддержка автора", 100)],
            300: [types.LabeledPrice("Поддержка автора", 300)],
            500: [types.LabeledPrice("Поддержка автора", 500)],
            1000: [types.LabeledPrice("Поддержка автора", 1000)]
        }

        try:
            bot.send_invoice(
                chat_id=call.message.chat.id,
                title="Поддержка Ferwes Games",
                description=f"Пожертвование {amount} Stars",
                invoice_payload=f"donate_{user_id}_{amount}",
                provider_token="",
                currency="XTR",
                prices=prices[amount]
            )
            bot.answer_callback_query(call.id, "✅ Счёт создан")
        except Exception as e:
            logger.error(f"Ошибка счёта: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка")

    elif call.data == "show_donate":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_donate_menu(call.message.chat.id, user_id)

    elif call.data == "show_orders":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        orders_cmd(call.message)

    elif call.data == "new_order":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        neworder_cmd(call.message)

    elif call.data == "my_orders":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        myorders_cmd(call.message)

    elif call.data == "my_stats":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        stats_cmd(call.message)

    elif call.data == "show_top":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        top_cmd(call.message)

    elif call.data == "show_help":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        help_cmd(call.message)

    elif call.data == "back_to_start":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        start_cmd(call.message)

    elif call.data == "cancel_order":
        if call.message.chat.id in user_states:
            del user_states[call.message.chat.id]
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.send_message(call.message.chat.id, "❌ Создание заказа отменено")
        start_cmd(call.message)

    elif call.data == "current_page":
        bot.answer_callback_query(call.id)


# ========== ОБРАБОТЧИК ОПЛАТЫ ==========
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout_handler(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def successful_payment_handler(message):
    user_id = message.from_user.id
    payment = message.successful_payment

    try:
        amount = int(payment.invoice_payload.split('_')[-1])
    except:
        amount = 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET stars_donated = stars_donated + ? WHERE user_id = ?",
        (amount, user_id)
    )
    conn.commit()
    conn.close()

    text = f"""✅ <b>СПАСИБО ЗА ПОДДЕРЖКУ!</b>

💰 Оплачено: {amount} Stars

Теперь вы можете создать 🔴 приоритетный заказ за {PRIORITY_COST} Stars!"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 FERWES GAMES BOT v8.0")
    print("=" * 60)
    print(f"🎮 Игр: {len(GAMES_DATABASE)}")
    print("🔍 Fuzzy-поиск: ВКЛ")
    print("📦 Альбомы: по 10 файлов")
    print("🔴🔵 Приоритеты: ВКЛ")
    print("👑 Админ-панель: /admin")
    print("=" * 60)

    clean_old_orders()

    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        time.sleep(10)