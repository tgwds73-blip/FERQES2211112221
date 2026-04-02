import telebot
from telebot import types
import json
import os
import time
import random
from datetime import datetime, timedelta
from collections import Counter

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = '8456295069:AAGz48djuL19fYnn9FCz8DgJRQgIO6rLlq0'
bot = telebot.TeleBot(BOT_TOKEN)
GAMES_CHANNEL_ID = -1003421344618

# Файлы данных
ORDERS_FILE = 'orders.json'
USER_STATS_FILE = 'user_stats.json'
ADMINS_FILE = 'admins.json'
LIKE_COOLDOWN_FILE = 'like_cooldown.json'
GAME_STATS_FILE = 'game_stats.json'
BANNED_FILE = 'banned_users.json'
MUTED_FILE = 'muted_users.json'
ACTION_LOG_FILE = 'action_log.json'

# Константы
LIKE_COOLDOWN_DAYS = 1000
ORDERS_PER_PAGE = 5
ORDER_EXPIRE_DAYS = 60

# ========== ДАННЫЕ ==========
orders = []
user_stats = {}
admins = ["7885915159"]
user_states = {}
like_cooldowns = {}
game_stats = {}
banned_users = []
muted_users = []
action_log = []

# ========== БАЗА ВСЕХ ИГР ==========
GAMES_DATABASE = {
    # A
    'antonblast': list(range(913, 915)) + [1749],
    'assassins creed': list(range(1028, 1033)) + [1749],
    'artmoney': [1770, 1771] + [1749],
    # B
    'bad cheese': list(range(1651, 1654)) + [1749],
    'battlefield 3': list(range(1773, 1784)) + [1749],
    'bf3': list(range(1773, 1784)) + [1749],
    'beamng drive': list(range(861, 873)) + [1749],
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
    'gta 3': list(range(1088, 1090)) + [1749],
    'gta 4': list(range(799, 810)) + [1749],
    'gta 5': list(range(705, 742)) + [1749],
    'gta san andreas': list(range(1259, 1270)) + [1749],
    'gta vice city': list(range(1450, 1452)) + [1749],
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
    'hotline miami 2': [1159, 1160] + [1749],
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
    # ARDA
    'arda launcher': list(range(1784, 1787)) + [1749],
    'arda': list(range(1784, 1787)) + [1749],
}

# ========== ЗАГРУЗКА ДАННЫХ ==========
def load_data():
    global orders, user_stats, admins, like_cooldowns, game_stats, banned_users, muted_users, action_log

    files = {
        ORDERS_FILE: orders,
        USER_STATS_FILE: user_stats,
        ADMINS_FILE: admins,
        LIKE_COOLDOWN_FILE: like_cooldowns,
        GAME_STATS_FILE: game_stats,
        BANNED_FILE: banned_users,
        MUTED_FILE: muted_users,
        ACTION_LOG_FILE: action_log
    }

    for file, data_var in files.items():
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    if isinstance(data_var, list):
                        data_var.clear()
                        data_var.extend(json.load(f))
                    elif isinstance(data_var, dict):
                        data_var.clear()
                        data_var.update(json.load(f))
            except:
                pass


def save_data():
    files = {
        ORDERS_FILE: orders,
        USER_STATS_FILE: user_stats,
        ADMINS_FILE: admins,
        LIKE_COOLDOWN_FILE: like_cooldowns,
        GAME_STATS_FILE: game_stats,
        BANNED_FILE: banned_users,
        MUTED_FILE: muted_users,
        ACTION_LOG_FILE: action_log
    }

    for file, data in files.items():
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass


def log_action(user_id, action, details=""):
    """Логирует действие пользователя"""
    action_log.append({
        'user_id': user_id,
        'action': action,
        'details': details,
        'time': datetime.now().isoformat()
    })
    # Оставляем только последние 1000 записей
    if len(action_log) > 1000:
        action_log.pop(0)
    save_data()


def is_banned(user_id):
    return str(user_id) in banned_users


def is_muted(user_id):
    return str(user_id) in muted_users


def clean_old_orders():
    """Удаляет заказы старше ORDER_EXPIRE_DAYS дней"""
    now = datetime.now()
    to_remove = []
    for i, order in enumerate(orders):
        try:
            order_date = datetime.fromisoformat(order['date'])
            if (now - order_date).days > ORDER_EXPIRE_DAYS:
                to_remove.append(i)
        except:
            pass

    for i in reversed(to_remove):
        orders.pop(i)

    if to_remove:
        save_data()
        log_action("system", "clean_orders", f"Удалено {len(to_remove)} старых заказов")


def check_and_clean_orders():
    """Запускает очистку старых заказов при запуске"""
    clean_old_orders()


# ========== ПРОВЕРКИ ==========
def is_admin(user_id):
    return str(user_id) in admins


def can_like(user_id):
    user_id_str = str(user_id)
    if user_id_str not in like_cooldowns:
        return True, None
    last_like_str = like_cooldowns[user_id_str]
    try:
        last_like_date = datetime.fromisoformat(last_like_str)
        next_like_date = last_like_date + timedelta(days=LIKE_COOLDOWN_DAYS)
        now = datetime.now()
        if now >= next_like_date:
            return True, None
        else:
            days_left = (next_like_date - now).days
            return False, days_left
    except:
        return True, None


def update_like_cooldown(user_id):
    user_id_str = str(user_id)
    like_cooldowns[user_id_str] = datetime.now().isoformat()
    save_data()


# ========== ОТПРАВКА ИГР ==========
def send_game_files(chat_id, game_name, user_id=None):
    if game_name not in GAMES_DATABASE:
        return False

    file_ids = GAMES_DATABASE[game_name]
    sent_count = 0

    bot.send_message(chat_id, f"🎮 *{game_name.upper()}*\n📥 Отправляю...", parse_mode='Markdown')

    for file_id in file_ids:
        try:
            bot.copy_message(chat_id, GAMES_CHANNEL_ID, file_id)
            sent_count += 1
            time.sleep(0.3)
        except:
            pass

    if user_id:
        uid = str(user_id)
        if uid not in user_stats:
            user_stats[uid] = {'downloads': 0, 'created_orders': 0}
        user_stats[uid]['downloads'] = user_stats[uid].get('downloads', 0) + 1

        if game_name not in game_stats:
            game_stats[game_name] = {'downloads': 0}
        game_stats[game_name]['downloads'] += 1
        save_data()

    bot.send_message(chat_id, f"✅ *Готово!* Отправлено {sent_count} файлов")
    return True


# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    if user_id not in user_stats:
        user_stats[user_id] = {
            'downloads': 0,
            'created_orders': 0,
            'first_seen': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        save_data()

    log_action(user_id, "start", "Пользователь запустил бота")

    text = """🎮 *Ferwes Games*

🔍 *Напиши название игры* — я найду и отправлю.

📋 `/orders` — заказы
📝 `/neworder` — создать заказ
👤 `/myorders` — мои заказы
📊 `/stats` — статистика
🔥 `/top` — топ игр
📜 `/history` — история скачиваний

💡 *Нет игры?* → /neworder
━━━━━━━━━━━━━━━━━━
📢 @FerwesGames | ❓ /help"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="my_stats"),
        types.InlineKeyboardButton("🔥 Топ игр", callback_data="show_top"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    log_action(user_id, "help", "Пользователь открыл помощь")

    text = """📚 *Помощь*

━━━━━━━━━━━━━━━━━━
📦 *Заказы*
━━━━━━━━━━━━━━━━━━
/orders — стол заказов
/neworder — создать заказ
/myorders — мои заказы

━━━━━━━━━━━━━━━━━━
🎲 *Игры*
━━━━━━━━━━━━━━━━━━
/top — топ-10 игр
/history — история скачиваний

━━━━━━━━━━━━━━━━━━
👤 *Профиль*
━━━━━━━━━━━━━━━━━━
/stats — моя статистика

━━━━━━━━━━━━━━━━━━
💡 *Нет игры?* → /neworder
━━━━━━━━━━━━━━━━━━
📢 @FerwesGames"""

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА STATS ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    log_action(user_id, "stats", "Пользователь посмотрел статистику")

    if user_id not in user_stats:
        text = "📊 *У вас пока нет скачиваний*\n\nНапиши название игры, чтобы начать!"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    stats = user_stats[user_id]
    downloads = stats.get('downloads', 0)
    created_orders = stats.get('created_orders', 0)

    try:
        first_seen = datetime.fromisoformat(stats.get('first_seen', datetime.now().isoformat()))
        days_active = (datetime.now() - first_seen).days
    except:
        days_active = 0

    user_orders = [o for o in orders if o.get('user_id') == message.chat.id]
    total_likes = sum(o.get('likes', 0) for o in user_orders)

    text = f"""📊 *Моя статистика*

🎮 Скачано: {downloads}
📋 Заказов: {created_orders}
❤️ Лайков: {total_likes}
📅 В боте: {days_active} дней"""

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА HISTORY ==========
@bot.message_handler(commands=['history'])
def history_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    log_action(user_id, "history", "Пользователь посмотрел историю")

    # Собираем историю скачиваний из game_stats
    user_games = []
    for game, stats in game_stats.items():
        if stats.get('downloads', 0) > 0:
            user_games.append(game)

    if not user_games:
        text = "📜 *История скачиваний*\n\nУ вас пока нет скачанных игр"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    text = "📜 *История скачиваний*\n\n"
    for i, game in enumerate(user_games[-20:], 1):
        text += f"{i}. 🎮 {game}\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА TOP ==========
@bot.message_handler(commands=['top'])
def top_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    if game_stats:
        sorted_games = sorted(game_stats.items(), key=lambda x: x[1]['downloads'], reverse=True)[:10]

        text = "🔥 *Топ-10 игр*\n\n"
        for i, (game, stats) in enumerate(sorted_games, 1):
            text += f"{i}. {game} — {stats['downloads']} 📥\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "📊 *Нет данных*")


# ========== КОМАНДА ORDERS ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    log_action(user_id, "orders", "Пользователь открыл стол заказов")
    show_orders_page(message.chat.id, 0, message)


def show_orders_page(chat_id, page=0, original_message=None):
    if not orders:
        bot.send_message(chat_id, "📭 *Нет заказов*")
        return

    sorted_orders = sorted(orders, key=lambda x: datetime.fromisoformat(x['date']) if 'date' in x else datetime.min,
                           reverse=True)

    total_pages = (len(sorted_orders) + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0

    start_idx = page * ORDERS_PER_PAGE
    end_idx = min(start_idx + ORDERS_PER_PAGE, len(sorted_orders))
    page_orders = sorted_orders[start_idx:end_idx]

    text = f"📋 *Заказы* (Страница {page + 1}/{total_pages})\n\n"

    for order in page_orders:
        try:
            order_date = datetime.fromisoformat(order['date']).strftime("%d.%m.%Y")
        except:
            order_date = "неизвестно"

        status = "🟢 активен"
        if order.get('status') == 'done':
            status = "🔴 готов"

        text += f"🎮 {order['game']}\n"
        text += f"👤 {order.get('username', 'User')}\n"
        text += f"📅 {order_date} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} | {status}\n"
        text += f"🆔 {order['id']}\n"
        text += "─\n"

    markup = types.InlineKeyboardMarkup(row_width=3)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="current"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)

    for order in page_orders:
        markup.add(types.InlineKeyboardButton(f"❤️ {order['game'][:12]}", callback_data=f"like_{order['id']}"))

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА NEWORDER ==========
@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    if is_muted(user_id):
        bot.send_message(message.chat.id, "🔇 *Вы не можете создавать заказы*")
        return

    log_action(user_id, "neworder", "Пользователь начал создание заказа")
    user_states[message.chat.id] = 'waiting_game'
    bot.send_message(message.chat.id, "📝 *Название игры:*", parse_mode='Markdown')


@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_game')
def get_game(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = {'game': message.text, 'state': 'waiting_size'}
    bot.send_message(message.chat.id, "💾 *Размер в ГБ:*", parse_mode='Markdown')


@bot.message_handler(
    func=lambda m: user_states.get(m.chat.id) and user_states[m.chat.id].get('state') == 'waiting_size')
def get_size(message):
    if message.chat.type != 'private':
        return

    data = user_states[message.chat.id]
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"

    order_id = len(orders) + 1
    orders.append({
        'id': order_id,
        'game': data['game'],
        'size': message.text.upper() + " ГБ",
        'likes': 0,
        'liked_by': [],
        'user_id': message.chat.id,
        'username': user_info,
        'date': datetime.now().isoformat(),
        'status': 'active'
    })

    user_id_str = str(message.from_user.id)
    if user_id_str not in user_stats:
        user_stats[user_id_str] = {'downloads': 0, 'created_orders': 0}
    user_stats[user_id_str]['created_orders'] = user_stats[user_id_str].get('created_orders', 0) + 1
    user_stats[user_id_str]['last_active'] = datetime.now().isoformat()

    save_data()
    del user_states[message.chat.id]

    log_action(user_id_str, "neworder", f"Создан заказ #{order_id}: {data['game']}")

    bot.send_message(message.chat.id, f"✅ *Заказ #{order_id} создан*", parse_mode='Markdown')


# ========== КОМАНДА MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    log_action(user_id, "myorders", "Пользователь посмотрел свои заказы")

    user_orders = [o for o in orders if o.get('user_id') == message.chat.id]
    if not user_orders:
        bot.send_message(message.chat.id, "📭 *У вас нет заказов*")
        return

    text = "👤 *Мои заказы*\n\n"
    for order in user_orders[-10:]:
        status = "🟢" if order.get('status') != 'done' else "🔴"
        text += f"{status} {order['game']}\n"
        text += f"🆔 {order['id']} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)}\n"
        text += "─\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА MODERATOR ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if not is_admin(message.from_user.id) or message.chat.type != 'private':
        return

    log_action(message.from_user.id, "moderator", "Админ открыл панель")

    total_users = len(user_stats)
    total_orders = len(orders)
    total_downloads = sum(u.get('downloads', 0) for u in user_stats.values())

    text = f"""👑 *Панель модератора*

📊 *Статистика*
👥 Пользователей: {total_users}
📋 Заказов: {total_orders}
📥 Скачиваний: {total_downloads}
🔨 Забанено: {len(banned_users)}
🔇 Замучено: {len(muted_users)}

━━━━━━━━━━━━━━━━━━
⚡ *Команды*
/delorder [ID] — удалить заказ
/ban [ID] — заблокировать
/unban [ID] — разблокировать
/mute [ID] — запретить заказы
/unmute [ID] — снять мут
/broadcast [текст] — рассылка
/logs — последние действия
/clean — очистить старые заказы"""

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['delorder'])
def delorder_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        order_id = int(message.text.split()[1])
        for i, order in enumerate(orders):
            if order['id'] == order_id:
                game_name = order['game']
                del orders[i]
                save_data()
                log_action(message.from_user.id, "delorder", f"Удалён заказ #{order_id}: {game_name}")
                bot.reply_to(message, f"✅ Заказ #{order_id} удалён")
                return
        bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
    except:
        bot.reply_to(message, "❌ /delorder [ID]")


@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = message.text.split()[1]
        if user_id not in banned_users:
            banned_users.append(user_id)
            save_data()
            log_action(message.from_user.id, "ban", f"Забанен {user_id}")
            bot.reply_to(message, f"✅ Пользователь {user_id} забанен")
        else:
            bot.reply_to(message, "⚠️ Уже в бане")
    except:
        bot.reply_to(message, "❌ /ban [ID]")


@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = message.text.split()[1]
        if user_id in banned_users:
            banned_users.remove(user_id)
            save_data()
            log_action(message.from_user.id, "unban", f"Разбанен {user_id}")
            bot.reply_to(message, f"✅ Пользователь {user_id} разбанен")
        else:
            bot.reply_to(message, "⚠️ Не в бане")
    except:
        bot.reply_to(message, "❌ /unban [ID]")


@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = message.text.split()[1]
        if user_id not in muted_users:
            muted_users.append(user_id)
            save_data()
            log_action(message.from_user.id, "mute", f"Замучен {user_id}")
            bot.reply_to(message, f"✅ Пользователь {user_id} замучен")
        else:
            bot.reply_to(message, "⚠️ Уже в муте")
    except:
        bot.reply_to(message, "❌ /mute [ID]")


@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = message.text.split()[1]
        if user_id in muted_users:
            muted_users.remove(user_id)
            save_data()
            log_action(message.from_user.id, "unmute", f"Снят мут с {user_id}")
            bot.reply_to(message, f"✅ Мут снят с {user_id}")
        else:
            bot.reply_to(message, "⚠️ Не в муте")
    except:
        bot.reply_to(message, "❌ /unmute [ID]")


@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        broadcast_text = message.text.split(' ', 1)[1]
        sent = 0
        failed = 0

        for uid in user_stats.keys():
            if uid in banned_users:
                continue
            try:
                bot.send_message(int(uid), f"📢 *Объявление*\n\n{broadcast_text}", parse_mode='Markdown')
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

    if not action_log:
        bot.reply_to(message, "📭 Лог пуст")
        return

    text = "📋 *Последние действия*\n\n"
    for log in action_log[-20:]:
        time_str = datetime.fromisoformat(log['time']).strftime("%d.%m %H:%M")
        text += f"{time_str} | {log['user_id']} | {log['action']}\n"
        if log.get('details'):
            text += f"   └ {log['details']}\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['clean'])
def clean_cmd(message):
    if not is_admin(message.from_user.id):
        return

    old_count = len(orders)
    clean_old_orders()
    new_count = len(orders)
    deleted = old_count - new_count

    log_action(message.from_user.id, "clean", f"Удалено {deleted} старых заказов")
    bot.reply_to(message, f"✅ Удалено {deleted} заказов старше {ORDER_EXPIRE_DAYS} дней")


# ========== ПОИСК ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def search_handler(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if is_banned(user_id):
        bot.send_message(message.chat.id, "🚫 *Вы заблокированы*")
        return

    query = message.text.strip().lower()
    log_action(user_id, "search", f"Поиск: {query}")

    if query in GAMES_DATABASE:
        send_game_files(message.chat.id, query, message.from_user.id)
        return

    similar = []
    for game in GAMES_DATABASE.keys():
        if query in game or game in query:
            similar.append(game)

    if similar:
        text = f"❌ *'{message.text}' не найдено*\n\n🎯 *Возможно вы искали:*\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for game in similar[:5]:
            markup.add(types.InlineKeyboardButton(f"🎮 {game.title()}", callback_data=f"play_{game}"))

        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
    else:
        text = f"❌ *'{message.text}' не найдено*\n\n📝 /neworder — создать заказ"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== CALLBACK ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith('like_'):
        if is_banned(str(call.from_user.id)):
            bot.answer_callback_query(call.id, "❌ Вы заблокированы")
            return

        can_like_now, days_left = can_like(call.from_user.id)
        if not can_like_now:
            bot.answer_callback_query(call.id, f"❌ Следующий лайк через {days_left} дней", show_alert=True)
            return

        order_id = int(call.data.split('_')[1])
        for order in orders:
            if order['id'] == order_id:
                if 'liked_by' not in order:
                    order['liked_by'] = []
                if str(call.from_user.id) in order['liked_by']:
                    bot.answer_callback_query(call.id, "❌ Уже лайкали")
                    return
                order['likes'] = order.get('likes', 0) + 1
                order['liked_by'].append(str(call.from_user.id))
                update_like_cooldown(call.from_user.id)
                save_data()
                log_action(call.from_user.id, "like", f"Лайк заказа #{order_id}")
                bot.answer_callback_query(call.id, "❤️ Лайк поставлен!")
                return
        bot.answer_callback_query(call.id, "❌ Заказ не найден")

    elif call.data.startswith('play_'):
        game_name = call.data[5:]
        send_game_files(call.message.chat.id, game_name, call.from_user.id)
        bot.answer_callback_query(call.id)

    elif call.data.startswith('orders_page_'):
        page = int(call.data.split('_')[2])
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_orders_page(call.message.chat.id, page, call.message)

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
    elif call.data == "current":
        bot.answer_callback_query(call.id)


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК FERWES GAMES БОТА")
    print("=" * 60)

    files_to_create = [
        ORDERS_FILE, USER_STATS_FILE, ADMINS_FILE,
        LIKE_COOLDOWN_FILE, GAME_STATS_FILE,
        BANNED_FILE, MUTED_FILE, ACTION_LOG_FILE
    ]

    for file in files_to_create:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump([] if 'orders' in file or file == ACTION_LOG_FILE else {}, f)

    load_data()
    check_and_clean_orders()

    print(f"🎮 Игр в базе: {len(GAMES_DATABASE)}")
    print(f"📋 Заказов: {len(orders)}")
    print(f"👥 Пользователей: {len(user_stats)}")
    print(f"👑 Админов: {len(admins)}")
    print(f"🔨 Забанено: {len(banned_users)}")
    print(f"🔇 Замучено: {len(muted_users)}")
    print("=" * 60)
    print("⚡ Бот запущен и готов!")
    print("=" * 60)

    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)