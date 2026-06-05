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
BOT_TOKEN = '8781916300:AAHap0DI80QGxXJdbuyLcwl8ielIeGU064s'
bot = telebot.TeleBot(BOT_TOKEN)
GAMES_CHANNEL_ID = -1003421344618

# Константы
ORDER_EXPIRE_DAYS = 60

# ========== БАЗА ДАННЫХ SQLITE ==========
DATA_DIR = os.getenv('DATA_DIR', '.')
DB_FILE = os.path.join(DATA_DIR, 'bot_database.db')


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
            priority TEXT DEFAULT 'normal',
            created_date TIMESTAMP,
            anonymous BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'anonymous' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN anonymous BOOLEAN DEFAULT 0")
    if 'priority' not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN priority TEXT DEFAULT 'normal'")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_likes (
            order_id INTEGER,
            user_id INTEGER,
            liked_date TIMESTAMP,
            PRIMARY KEY (order_id, user_id)
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

# ========== БАЗА ВСЕХ ИГР ==========
GAMES_DATABASE = {
    'antonblast': [913, 914],
    'assassins creed': list(range(1028, 1033)),
    'artmoney': [1770, 1771],
    'bad cheese': list(range(1651, 1654)),
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


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

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


def send_game_files(chat_id, game_name, user_id=None):
    """Отправка игры файлами из канала"""
    if game_name not in GAMES_DATABASE:
        logger.error(f"Игра {game_name} не найдена в базе")
        return False

    file_ids = GAMES_DATABASE[game_name]

    try:
        total = len(file_ids)
        for idx, file_id in enumerate(file_ids, 1):
            try:
                bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=GAMES_CHANNEL_ID,
                    message_id=file_id
                )
                if idx % 10 == 0:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка отправки файла {file_id}: {e}")

        logger.info(f"Отправлена игра {game_name} ({total} файлов) для {user_id}")

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
        logger.error(f"Критическая ошибка отправки {game_name}: {e}")
        bot.send_message(chat_id, "❌ Ошибка при отправке игры. Попробуйте позже.")
        return False


def search_games(query):
    """Улучшенный поиск игр"""
    query = query.lower().strip()

    # Точное совпадение
    if query in GAMES_DATABASE:
        return [query]

    # Поиск по части названия
    results = []
    for game in GAMES_DATABASE:
        # Проверяем содержит ли запрос название игры или наоборот
        if query in game or game in query:
            results.append(game)

    # Сортировка по релевантности
    results.sort(key=lambda x: len(x))

    return results[:8]  # Максимум 8 результатов


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

    log_action(user.id, "start", "Запуск бота")

    text = """🎮 <b>FERWES GAMES</b>

Привет! Я бот для скачивания игр. Просто напиши название игры, и я отправлю тебе файлы.

📋 <b>Команды:</b>
/orders — Стол заказов
/neworder — Создать заказ
/myorders — Мои заказы
/donate — Поддержать
/help — Помощь

💡 <i>Нет нужной игры?</i> Создай заказ через /neworder"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
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

    text = """ℹ️ <b>ПОМОЩЬ</b>

🔍 <b>Поиск игр</b>
Просто напиши название игры в чат. Бот найдет её и отправит файлы.

📋 <b>Заказы</b>
/orders — Просмотр всех заказов
/neworder — Создать новый заказ
/myorders — Посмотреть свои заказы

💰 <b>Донат</b>
/donate — Поддержать развитие бота

<b>Особенности:</b>
• Можно лайкать заказы других пользователей
• Доступны анонимные заказы
• Приоритетные заказы выполняются быстрее

По вопросам: @FerwesGames"""

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

    show_donate_menu(message.chat.id)


def show_donate_menu(chat_id):
    text = """💰 <b>ПОДДЕРЖАТЬ БОТА</b>

Выберите сумму пожертвования:"""

    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("⭐ 10", callback_data="donate_10"),
        types.InlineKeyboardButton("⭐ 20", callback_data="donate_20"),
        types.InlineKeyboardButton("⭐ 30", callback_data="donate_30"),
        types.InlineKeyboardButton("⭐ 40", callback_data="donate_40"),
        types.InlineKeyboardButton("⭐ 50", callback_data="donate_50"),
        types.InlineKeyboardButton("⭐ 100", callback_data="donate_100")
    )
    markup.add(types.InlineKeyboardButton("« Назад", callback_data="back_to_start"))

    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)


# ========== КОМАНДА ORDERS ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    show_orders_page(message.chat.id, 0, user_id)


def show_orders_page(chat_id, page=0, viewer_id=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.user_id, o.game_name, o.size, o.likes, o.status, o.created_date, 
               o.anonymous, o.priority, u.username 
        FROM orders o 
        LEFT JOIN users u ON o.user_id = u.user_id 
        WHERE o.status = 'active' 
        ORDER BY 
            CASE o.priority WHEN 'urgent' THEN 0 ELSE 1 END,
            o.created_date DESC
    """)
    all_orders = cursor.fetchall()
    conn.close()

    if not all_orders:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(chat_id, "📭 Нет активных заказов\n\nСтаньте первым!", parse_mode='HTML', reply_markup=markup)
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

    text = f"📋 <b>ЗАКАЗЫ</b> ({len(all_orders)})\n"
    text += f"Страница {page + 1}/{total_pages}\n\n"

    for order in page_orders:
        order_id, user_id, game_name, size, likes, status, created_date, anonymous, priority, username = order

        try:
            date_str = datetime.fromisoformat(created_date).strftime("%d.%m.%Y")
        except:
            date_str = "неизвестно"

        priority_emoji = "🔴" if priority == 'urgent' else "🟢"

        if anonymous:
            author = "Аноним"
        elif username:
            author = f"@{username}"
        else:
            author = f"ID:{user_id}"

        text += f"{priority_emoji} <b>#{order_id}</b> — {game_name}\n"
        text += f"👤 {author} | 💾 {size} | ❤️ {likes}\n"
        text += f"📅 {date_str}\n\n"

    markup = types.InlineKeyboardMarkup(row_width=5)

    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)

    # Кнопки лайков для всех заказов на странице
    like_buttons = []
    for order in page_orders:
        like_buttons.append(types.InlineKeyboardButton(
            f"❤️ #{order[0]}",
            callback_data=f"like_{order[0]}"
        ))

    # Размещаем по 3 кнопки в ряд
    for i in range(0, len(like_buttons), 3):
        markup.row(*like_buttons[i:i + 3])

    markup.add(
        types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders")
    )
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))

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

    user_states[message.chat.id] = {'state': 'waiting_game'}

    bot.send_message(
        message.chat.id,
        "📝 <b>НОВЫЙ ЗАКАЗ</b>\n\nВведите название игры:",
        parse_mode='HTML',
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("« Отмена", callback_data="cancel_order")
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
        f"🎮 Игра: {game_name}\n\nВведите размер в ГБ (только цифры):",
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
            "❌ Размер должен содержать только цифры!\nНапример: 50 или 12.5\n\nПопробуйте ещё раз:",
            parse_mode='HTML'
        )
        return

    size = f"{size_input} ГБ"
    data = user_states[message.chat.id]
    data['size'] = size
    data['state'] = 'waiting_priority'

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟢 Обычный", callback_data="priority_normal"),
        types.InlineKeyboardButton("🔴 Срочный", callback_data="priority_urgent")
    )

    bot.send_message(
        message.chat.id,
        f"🎮 Игра: {data['game']}\n💾 Размер: {size}\n\n<b>Выберите приоритет:</b>",
        parse_mode='HTML',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('priority_'))
def priority_choice(call):
    if call.message.chat.id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла")
        return

    data = user_states[call.message.chat.id]
    priority = call.data.split('_')[1]
    data['priority'] = priority
    data['state'] = 'waiting_anonymous'

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 Открыто", callback_data="anon_no"),
        types.InlineKeyboardButton("👻 Анонимно", callback_data="anon_yes")
    )

    try:
        bot.edit_message_text(
            f"🎮 Игра: {data['game']}\n💾 Размер: {data['size']}\n{'🔴 Срочный' if priority == 'urgent' else '🟢 Обычный'}\n\n<b>Опубликовать анонимно?</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=markup
        )
    except:
        pass

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('anon_'))
def anonymous_choice(call):
    if call.message.chat.id not in user_states:
        bot.answer_callback_query(call.id, "❌ Сессия истекла")
        return

    data = user_states[call.message.chat.id]
    anonymous = call.data == 'anon_yes'
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (user_id, game_name, size, created_date, anonymous, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, data['game'], data['size'], datetime.now().isoformat(), 1 if anonymous else 0,
          data.get('priority', 'normal')))
    order_id = cursor.lastrowid

    cursor.execute(
        "UPDATE users SET created_orders = created_orders + 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    conn.close()

    del user_states[call.message.chat.id]

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    anon_text = "Анонимно" if anonymous else "Открыто"
    priority_text = "Срочный" if data.get('priority') == 'urgent' else "Обычный"

    text = f"""✅ <b>ЗАКАЗ #{order_id} СОЗДАН</b>

🎮 Игра: {data['game']}
💾 Размер: {data['size']}
🔴 Приоритет: {priority_text}
👤 {anon_text}

Спасибо за заказ!"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Все заказы", callback_data="show_orders"))
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_start"))

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
        text = "👤 <b>МОИ ЗАКАЗЫ</b>\n\nУ вас пока нет заказов.\n\nСоздайте первый через /neworder"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
        return

    text = f"👤 <b>МОИ ЗАКАЗЫ</b> ({len(user_orders)})\n\n"
    for order in user_orders:
        order_id, game_name, size, likes, status, created_date, anonymous, priority = order
        status_emoji = "🟢" if status == 'active' else "🔴"
        priority_emoji = "🔴" if priority == 'urgent' else ""
        anon_badge = " 👻" if anonymous else ""
        text += f"{status_emoji} <b>#{order_id}</b>{priority_emoji} — {game_name}\n"
        text += f"💾 {size} | ❤️ {likes}{anon_badge}\n\n"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== ПОИСК ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.chat.type == 'private')
def search_handler(message):
    user_id = message.from_user.id

    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 Вы заблокированы")
        return

    query = message.text.strip()
    results = search_games(query)

    if len(results) == 1 and query.lower() == results[0].lower():
        # Точное совпадение - сразу отправляем
        total_files = len(GAMES_DATABASE[results[0]])
        bot.send_message(
            message.chat.id,
            f"🎮 Найдено: {results[0]}\n📦 Файлов: {total_files}\n\n⏳ Отправляю...",
            parse_mode='HTML'
        )
        send_game_files(message.chat.id, results[0], user_id)
    elif results:
        # Показываем варианты
        text = f"🔍 <b>Результаты поиска для \"{query}\":</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i, game in enumerate(results, 1):
            text += f"{i}. {game}\n"
            markup.add(types.InlineKeyboardButton(
                f"📥 {game}",
                callback_data=f"play_{game}"
            ))
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)
    else:
        text = f"❌ Игра \"{query}\" не найдена\n\n📝 Создайте заказ через /neworder"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Создать заказ", callback_data="new_order"))

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)


# ========== УДАЛЕНИЕ ЗАКАЗОВ (АДМИН) ==========
@bot.message_handler(commands=['deleteorder'])
def delete_order_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав администратора")
        return

    try:
        parts = message.text.split(maxsplit=2)
        order_id = int(parts[1])
        reason = parts[2] if len(parts) > 2 else "Без причины"
    except:
        bot.send_message(message.chat.id, "❌ Использование: /deleteorder ID причина")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, game_name FROM orders WHERE order_id = ?", (order_id,))
    order = cursor.fetchone()

    if not order:
        bot.send_message(message.chat.id, f"❌ Заказ #{order_id} не найден")
        conn.close()
        return

    creator_id, game_name = order
    cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    cursor.execute("DELETE FROM order_likes WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()

    # Уведомление создателю
    try:
        bot.send_message(
            creator_id,
            f"📋 Ваш заказ <b>#{order_id}</b> ({game_name}) был удалён администратором.\n\n"
            f"<b>Причина:</b> {reason}",
            parse_mode='HTML'
        )
    except:
        logger.error(f"Не удалось уведомить пользователя {creator_id}")

    bot.send_message(message.chat.id, f"✅ Заказ #{order_id} удалён")


# ========== CALLBACK ОБРАБОТЧИК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data.startswith('like_'):
        if is_banned(user_id):
            bot.answer_callback_query(call.id, "❌ Вы заблокированы")
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
        show_orders_page(call.message.chat.id, page, user_id)

    elif call.data.startswith('donate_'):
        amount = int(call.data.split('_')[1])

        prices = {
            10: [types.LabeledPrice("Поддержка бота", 10)],
            20: [types.LabeledPrice("Поддержка бота", 20)],
            30: [types.LabeledPrice("Поддержка бота", 30)],
            40: [types.LabeledPrice("Поддержка бота", 40)],
            50: [types.LabeledPrice("Поддержка бота", 50)],
            100: [types.LabeledPrice("Поддержка бота", 100)]
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
            logger.error(f"Ошибка создания счёта: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка создания счёта")

    elif call.data == "show_donate":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        show_donate_menu(call.message.chat.id)

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

Ваша поддержка помогает развивать бота! ❤️"""

    bot.send_message(message.chat.id, text, parse_mode='HTML')


# ========== ЗАПУСК БОТА ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 FERWES GAMES BOT")
    print("=" * 50)

    logger.info("=" * 50)
    logger.info("ЗАПУСК БОТА")
    logger.info(f"База данных: {DB_FILE}")
    logger.info(f"Игр в базе: {len(GAMES_DATABASE)}")
    logger.info("=" * 50)

    print(f"🎮 Игр загружено: {len(GAMES_DATABASE)}")
    print("💾 База данных: SQLite")
    print("📝 Логирование: bot.log")
    print("=" * 50)
    print("⚡ Бот запущен!")
    print("=" * 50)

    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        time.sleep(10)