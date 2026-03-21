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

# Константы
LIKE_COOLDOWN_DAYS = 1000
ORDERS_PER_PAGE = 5

# ========== ДАННЫЕ ==========
orders = []
user_stats = {}
admins = ["7885915159"]
user_states = {}
like_cooldowns = {}
game_stats = {}

# ========== БАЗА ВСЕХ ИГР ==========
GAMES_DATABASE = {
    # A
    'antonblast': list(range(913, 915)) + [1749],
    'assassins creed': list(range(1028, 1033)) + [1749],
    'artmoney': list(range(1770, 1771)) + [1749],
    # B
    'bad cheese': list(range(1651, 1654)) + [1749],
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
    'doom the dark ages': list(range(1706, 1749)) + [1749],
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
}


# ========== ЗАГРУЗКА ДАННЫХ ==========
def load_data():
    global orders, user_stats, admins, like_cooldowns, game_stats

    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders.extend(json.load(f))

    if os.path.exists(USER_STATS_FILE):
        with open(USER_STATS_FILE, 'r', encoding='utf-8') as f:
            user_stats.update(json.load(f))

    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            admins.clear()
            admins.extend(json.load(f))

    if os.path.exists(LIKE_COOLDOWN_FILE):
        with open(LIKE_COOLDOWN_FILE, 'r', encoding='utf-8') as f:
            like_cooldowns.update(json.load(f))

    if os.path.exists(GAME_STATS_FILE):
        with open(GAME_STATS_FILE, 'r', encoding='utf-8') as f:
            game_stats.update(json.load(f))


def save_data():
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    with open(USER_STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_stats, f, ensure_ascii=False, indent=2)

    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins, f, ensure_ascii=False, indent=2)

    with open(LIKE_COOLDOWN_FILE, 'w', encoding='utf-8') as f:
        json.dump(like_cooldowns, f, ensure_ascii=False, indent=2)

    with open(GAME_STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(game_stats, f, ensure_ascii=False, indent=2)


# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    if user_id not in user_stats:
        user_stats[user_id] = {
            'downloads': 0,
            'created_orders': 0,
            'first_seen': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        save_data()

    text = """🎮 *FERWES GAMES* — твой проводник в мир игр!

🔍 *Напиши название игры* — я найду её в базе и отправлю.

━━━━━━━━━━━━━━━━━━
📋 `/orders` — стол заказов  
📝 `/neworder` — создать заказ  
👤 `/myorders` — мои заказы  
📊 `/stats` — моя статистика  
🔥 `/top` — топ игр  
🎲 `/randgame` — случайная игра  
🏆 `/toporders` — топ заказов  
✏️ `/editorder [ID]` — редактировать заказ
🎯 `/today` — игра дня
🎁 `/bonus` — получить бонус
📜 `/rules` — правила
🔔 `/notify` — уведомления
👥 `/online` — кто в сети
📈 `/leaderboard` — таблица лидеров
🎨 `/favorite` — избранное
⭐ `/rate` — оценить игру

💡 *Совет:* если игры нет в базе — создай заказ, и мы добавим её!
━━━━━━━━━━━━━━━━━━
📢 Наш канал: @FerwesGames"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="my_stats"),
        types.InlineKeyboardButton("🔥 Топ игр", callback_data="show_top"),
        types.InlineKeyboardButton("🎲 Случайная", callback_data="rand_game"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private':
        return

    text = """📚 *ПОМОЩЬ ПО КОМАНДАМ*

━━━━━━━━━━━━━━━━━━
🎮 *ОСНОВНЫЕ КОМАНДЫ*
━━━━━━━━━━━━━━━━━━
`/start` — главное меню
`/help` — эта справка
`/stats` — моя статистика
`/today` — игра дня
`/bonus` — получить бонус

━━━━━━━━━━━━━━━━━━
📦 *ЗАКАЗЫ*
━━━━━━━━━━━━━━━━━━
`/orders` — стол заказов
`/neworder` — создать заказ
`/myorders` — мои заказы
`/editorder [ID]` — редактировать заказ

━━━━━━━━━━━━━━━━━━
🎲 *ИГРЫ*
━━━━━━━━━━━━━━━━━━
`/top` — топ скачиваемых игр
`/randgame` — случайная игра
`/toporders` — топ заказов по лайкам
`/favorite` — добавить в избранное
`/rate` — оценить игру

━━━━━━━━━━━━━━━━━━
👥 *СОЦИАЛЬНЫЕ*
━━━━━━━━━━━━━━━━━━
`/online` — кто сейчас в сети
`/leaderboard` — таблица лидеров
`/notify` — настроить уведомления

━━━━━━━━━━━━━━━━━━
💡 *КАК ИСКАТЬ ИГРЫ?*
━━━━━━━━━━━━━━━━━━
Просто напиши название в чат:
• `gta 5` или `gta v`
• `witcher 3` или `ведьмак 3`
• `cyberpunk 2077`

━━━━━━━━━━━━━━━━━━
🎁 *БОНУСЫ*
━━━━━━━━━━━━━━━━━━
`/bonus` — раз в 7 дней даёт +1 скачивание
`/today` — игра дня
`/rate` — оцени игру и получи +1

━━━━━━━━━━━━━━━━━━
❓ *ВОПРОСЫ?*
━━━━━━━━━━━━━━━━━━
По всем вопросам: @sweacher
Наш канал: @FerwesGames"""

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="my_stats"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="get_bonus")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== НОВАЯ КОМАНДА: ONLINE ==========
@bot.message_handler(commands=['online'])
def online_cmd(message):
    if message.chat.type != 'private':
        return

    now = datetime.now()
    online_count = 0
    online_users = []

    for uid, data in user_stats.items():
        last = data.get('last_active', '')
        if last:
            try:
                last_time = datetime.fromisoformat(last)
                if (now - last_time).seconds < 300:  # активны последние 5 минут
                    online_count += 1
                    online_users.append(uid)
            except:
                pass

    text = f"👥 *СЕЙЧАС В СЕТИ*\n\n━━━━━━━━━━━━━━━━━━\n👤 Онлайн: {online_count} пользователей\n\n💡 *Совет:* будь активнее, чтобы попасть в список!"

    if online_users:
        text += f"\n🟢 Активны: {len(online_users)}"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== НОВАЯ КОМАНДА: LEADERBOARD ==========
@bot.message_handler(commands=['leaderboard'])
def leaderboard_cmd(message):
    if message.chat.type != 'private':
        return

    sorted_users = sorted(user_stats.items(), key=lambda x: x[1].get('downloads', 0), reverse=True)[:10]

    if not sorted_users:
        text = "📊 *ТАБЛИЦА ЛИДЕРОВ*\n\nНет данных для отображения"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    text = "🏆 *ТАБЛИЦА ЛИДЕРОВ*\n\n"

    for i, (uid, data) in enumerate(sorted_users, 1):
        downloads = data.get('downloads', 0)
        created = data.get('created_orders', 0)

        medal = ""
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."

        text += f"{medal} *ID {uid}* — {downloads} 📥, {created} 📋\n"

    text += "\n💡 *Совет:* качай больше игр, чтобы подняться в топе!"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== НОВАЯ КОМАНДА: NOTIFY ==========
@bot.message_handler(commands=['notify'])
def notify_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)
    current = user_stats.get(user_id, {}).get('notify', True)

    if current:
        user_stats[user_id]['notify'] = False
        text = "🔕 *УВЕДОМЛЕНИЯ ВЫКЛЮЧЕНЫ*\n\nВы больше не будете получать уведомления о новых играх и заказах."
    else:
        user_stats[user_id]['notify'] = True
        text = "🔔 *УВЕДОМЛЕНИЯ ВКЛЮЧЕНЫ*\n\nВы будете получать уведомления о новых играх и заказах."

    save_data()
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== НОВАЯ КОМАНДА: FAVORITE ==========
@bot.message_handler(commands=['favorite'])
def favorite_cmd(message):
    if message.chat.type != 'private':
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        # Показываем список избранного
        favorites = user_stats.get(str(message.from_user.id), {}).get('favorites', [])

        if not favorites:
            text = "⭐ *ИЗБРАННОЕ*\n\nУ вас пока нет избранных игр.\n\n💡 *Совет:* используй `/favorite [название игры]` чтобы добавить игру в избранное!"
        else:
            text = "⭐ *ВАШИ ИЗБРАННЫЕ ИГРЫ*\n\n"
            for i, game in enumerate(favorites, 1):
                text += f"{i}. 🎮 {game}\n"
            text += "\n💡 *Совет:* `/favorite удалить [название]` — удалить из избранного"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    action = parts[1].strip().lower()

    if action.startswith('удалить'):
        game_to_remove = action.replace('удалить', '').strip()
        favorites = user_stats.get(str(message.from_user.id), {}).get('favorites', [])

        if game_to_remove in favorites:
            favorites.remove(game_to_remove)
            user_stats[str(message.from_user.id)]['favorites'] = favorites
            save_data()
            text = f"✅ Игра *{game_to_remove}* удалена из избранного!"
        else:
            text = f"❌ Игра *{game_to_remove}* не найдена в избранном"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        # Добавляем игру в избранное
        game_name = action
        favorites = user_stats.get(str(message.from_user.id), {}).get('favorites', [])

        if game_name not in favorites:
            favorites.append(game_name)
            user_stats[str(message.from_user.id)]['favorites'] = favorites
            save_data()
            text = f"⭐ Игра *{game_name}* добавлена в избранное!"
        else:
            text = f"⚠️ Игра *{game_name}* уже в избранном"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== НОВАЯ КОМАНДА: RATE ==========
@bot.message_handler(commands=['rate'])
def rate_cmd(message):
    if message.chat.type != 'private':
        return

    parts = message.text.split()

    if len(parts) < 3:
        text = "⭐ *ОЦЕНИТЬ ИГРУ*\n\nИспользование: `/rate [название игры] [1-5]`\n\nПример: `/rate gta 5 5`"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    # Парсим название и оценку
    rating = parts[-1]
    game_name = ' '.join(parts[1:-1])

    try:
        rating_num = int(rating)
        if rating_num < 1 or rating_num > 5:
            raise ValueError
    except:
        text = "❌ Оценка должна быть числом от 1 до 5!"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    # Проверяем, есть ли игра в базе
    found = False
    for db_game in GAMES_DATABASE.keys():
        if game_name.lower() in db_game.lower() or db_game.lower() in game_name.lower():
            found = True
            game_name = db_game
            break

    if not found:
        text = f"❌ Игра *{game_name}* не найдена в базе!\n\n💡 *Совет:* проверь название или добавь заказ через /neworder"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    # Сохраняем оценку
    if 'ratings' not in game_stats:
        game_stats[game_name] = game_stats.get(game_name, {'downloads': 0, 'ratings': []})

    if 'ratings' not in game_stats[game_name]:
        game_stats[game_name]['ratings'] = []

    game_stats[game_name]['ratings'].append(rating_num)
    save_data()

    # Начисляем бонус за оценку
    user_id = str(message.from_user.id)
    if user_id not in user_stats:
        user_stats[user_id] = {'downloads': 0, 'created_orders': 0}

    user_stats[user_id]['downloads'] = user_stats[user_id].get('downloads', 0) + 1
    user_stats[user_id]['last_bonus_rating'] = datetime.now().isoformat()
    user_stats[user_id]['last_active'] = datetime.now().isoformat()
    save_data()

    avg_rating = sum(game_stats[game_name]['ratings']) / len(game_stats[game_name]['ratings'])

    text = f"⭐ *ОЦЕНКА ПОСТАВЛЕНА!*\n\n🎮 Игра: {game_name}\n⭐ Ваша оценка: {rating_num}/5\n📊 Средний рейтинг: {avg_rating:.1f}/5\n\n🎁 Бонус: +1 к скачиваниям!"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА TODAY ==========
@bot.message_handler(commands=['today'])
def today_cmd(message):
    if message.chat.type != 'private':
        return

    game_name = random.choice(list(GAMES_DATABASE.keys()))

    text = f"""🎲 *ИГРА ДНЯ*

━━━━━━━━━━━━━━━━━━
🎮 {game_name.upper()}

📥 Нажми на кнопку ниже, чтобы скачать!

💡 *Совет:* сегодня особенный день — игра дня будет доступна весь день!

━━━━━━━━━━━━━━━━━━
📢 @FerwesGames"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🎮 Скачать {game_name}", callback_data=f"play_{game_name}"))

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА RULES ==========
@bot.message_handler(commands=['rules'])
def rules_cmd(message):
    if message.chat.type != 'private':
        return

    text = """📜 *ПРАВИЛА ЧАТА*

━━━━━━━━━━━━━━━━━━
1️⃣ *Без спама и флуда*
• Повторяющиеся сообщения, стикеры, гифки

2️⃣ *Без оскорблений*
• Уважайте других участников

3️⃣ *Без рекламы*
• Запрещена реклама сторонних каналов и ботов

4️⃣ *Без нацистской символики*
• Запрещены любые проявления

5️⃣ *Без 18+ контента*
• Порнография, насилие, расчленёнка

━━━━━━━━━━━━━━━━━━
⚠️ *НАРУШЕНИЯ*
• 1-е нарушение — предупреждение
• 2-е нарушение — мут на 24 часа
• 3-е нарушение — бан

━━━━━━━━━━━━━━━━━━
📢 @FerwesGames"""

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА BONUS ==========
@bot.message_handler(commands=['bonus'])
def bonus_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)

    last_bonus = user_stats.get(user_id, {}).get('last_bonus')

    if last_bonus:
        try:
            last_date = datetime.fromisoformat(last_bonus)
            days_passed = (datetime.now() - last_date).days
            if days_passed < 7:
                days_left = 7 - days_passed
                text = f"🎁 *БОНУС НЕДОСТУПЕН*\n\n━━━━━━━━━━━━━━━━━━\n⏳ Следующий бонус будет доступен через {days_left} дней.\n\n💡 Бонус даёт +1 к скачиваниям!\n━━━━━━━━━━━━━━━━━━\n📢 @FerwesGames"
                bot.send_message(message.chat.id, text, parse_mode='Markdown')
                return
        except:
            pass

    if user_id not in user_stats:
        user_stats[user_id] = {'downloads': 0, 'created_orders': 0}

    user_stats[user_id]['downloads'] = user_stats[user_id].get('downloads', 0) + 1
    user_stats[user_id]['last_bonus'] = datetime.now().isoformat()
    user_stats[user_id]['last_active'] = datetime.now().isoformat()
    save_data()

    downloads = user_stats[user_id]['downloads']

    text = f"🎁 *БОНУС ПОЛУЧЕН!*\n\n━━━━━━━━━━━━━━━━━━\n✅ Вы получили +1 к скачиваниям!\n\n📊 Теперь у вас: {downloads} скачиваний\n\n💡 Следующий бонус через 7 дней!\n━━━━━━━━━━━━━━━━━━\n📢 @FerwesGames"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА STATS ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.chat.type != 'private':
        return

    user_id_str = str(message.from_user.id)

    if user_id_str not in user_stats:
        text = "📊 *ВЫ ЕЩЁ НИЧЕГО НЕ СКАЧАЛИ*\n\nНапиши название игры и начни коллекционировать!\n\n📢 @FerwesGames"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')
        return

    stats = user_stats[user_id_str]
    downloads = stats.get('downloads', 0)
    created_orders = stats.get('created_orders', 0)

    try:
        first_seen = datetime.fromisoformat(stats.get('first_seen', datetime.now().isoformat()))
        days_active = (datetime.now() - first_seen).days
    except:
        days_active = 0

    user_orders = [o for o in orders if o.get('user_id') == message.chat.id]
    total_likes_received = sum(o.get('likes', 0) for o in user_orders)

    if downloads >= 500:
        rank = "👑 ЛЕГЕНДА"
    elif downloads >= 250:
        rank = "⭐ ГУРУ"
    elif downloads >= 100:
        rank = "🎖️ ВЕТЕРАН"
    elif downloads >= 50:
        rank = "⚡ ПРОФИ"
    elif downloads >= 25:
        rank = "🔄 ЛЮБИТЕЛЬ"
    elif downloads >= 10:
        rank = "🆕 НОВИЧОК"
    else:
        rank = "🌱 НАЧИНАЮЩИЙ"

    if downloads < 10:
        need = 10 - downloads
        progress = downloads * 10
    elif downloads < 25:
        need = 25 - downloads
        progress = downloads * 4
    elif downloads < 50:
        need = 50 - downloads
        progress = downloads * 2
    elif downloads < 100:
        need = 100 - downloads
        progress = downloads
    elif downloads < 250:
        need = 250 - downloads
        progress = downloads * 0.4
    elif downloads < 500:
        need = 500 - downloads
        progress = downloads * 0.2
    else:
        need = 0
        progress = 100

    active_orders = sum(1 for o in user_orders if o.get('status') != 'done')
    done_orders = sum(1 for o in user_orders if o.get('status') == 'done')

    text = f"""📊 *ТВОЯ СТАТИСТИКА*

━━━━━━━━━━━━━━━━━━
👤 *ПРОФИЛЬ*
━━━━━━━━━━━━━━━━━━
🏆 Ранг: {rank}
📅 В игре: {days_active} дней

━━━━━━━━━━━━━━━━━━
📥 *АКТИВНОСТЬ*
━━━━━━━━━━━━━━━━━━
🎮 Скачано игр: {downloads}
📋 Создано заказов: {created_orders}
❤️ Получено лайков: {total_likes_received}
📦 Активных заказов: {active_orders}
✅ Выполненных: {done_orders}

━━━━━━━━━━━━━━━━━━
📈 *ПРОГРЕСС*
━━━━━━━━━━━━━━━━━━
До следующего ранга: {need} скачиваний
▰▰▰▰▰▰▰▰▰▰ {progress:.0f}%

━━━━━━━━━━━━━━━━━━
💡 *СОВЕТЫ*
━━━━━━━━━━━━━━━━━━
• Ищи игры по названию
• Ставь лайки к заказам
• Используй /bonus раз в неделю

📢 @FerwesGames"""

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("🔥 Топ игр", callback_data="show_top"),
        types.InlineKeyboardButton("🎁 Бонус", callback_data="get_bonus"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_stats")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА MODERATOR ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if str(message.from_user.id) not in admins or message.chat.type != 'private':
        return

    total_users = len(user_stats)
    total_orders = len(orders)
    total_downloads = sum(u.get('downloads', 0) for u in user_stats.values())
    total_likes = sum(o.get('likes', 0) for o in orders)

    today = datetime.now().date()
    active_today = 0
    for uid, data in user_stats.items():
        last = data.get('last_active', '')
        if last and datetime.fromisoformat(last).date() == today:
            active_today += 1

    text = f"""👑 *ПАНЕЛЬ МОДЕРАТОРА*

━━━━━━━━━━━━━━━━━━
📊 *ОБЩАЯ СТАТИСТИКА*
━━━━━━━━━━━━━━━━━━
👥 Пользователей: {total_users}
📋 Заказов: {total_orders}
📥 Скачиваний: {total_downloads}
❤️ Лайков: {total_likes}
📅 Активных сегодня: {active_today}

━━━━━━━━━━━━━━━━━━
⚡ *АДМИН-КОМАНДЫ*
━━━━━━━━━━━━━━━━━━
`/delorder [ID]` — удалить заказ
`/addadmin [ID]` — добавить админа
`/broadcast [текст]` — рассылка
`/set_status [ID] [статус]` — изменить статус
`/done [ID]` — отметить как готово

━━━━━━━━━━━━━━━━━━
📊 *СТАТУСЫ ЗАКАЗОВ*
━━━━━━━━━━━━━━━━━━
🟢 active — активный
🟡 found — найден
🔴 done — готово"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("🟢 Активные", callback_data="mod_active"),
        types.InlineKeyboardButton("🟡 Найденные", callback_data="mod_found"),
        types.InlineKeyboardButton("🔴 Готовые", callback_data="mod_done"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="mod_stats"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_mod")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== ОСТАЛЬНЫЕ КОМАНДЫ ==========
@bot.message_handler(commands=['randgame'])
def randgame_cmd(message):
    if message.chat.type != 'private':
        return

    game_name = random.choice(list(GAMES_DATABASE.keys()))
    send_game_files(message.chat.id, game_name, message.from_user.id)


@bot.message_handler(commands=['top'])
def top_cmd(message):
    if message.chat.type != 'private':
        return

    if game_stats:
        sorted_games = sorted(game_stats.items(), key=lambda x: x[1]['downloads'], reverse=True)[:10]

        text = "🔥 *ТОП-10 СКАЧИВАЕМЫХ ИГР*\n\n"
        for i, (game, stats) in enumerate(sorted_games, 1):
            text += f"{i}. 🎮 *{game}* — {stats['downloads']} 📥\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "📊 *Нет данных для топа*")


@bot.message_handler(commands=['toporders'])
def toporders_cmd(message):
    if message.chat.type != 'private':
        return

    if not orders:
        bot.send_message(message.chat.id, "📭 *Нет заказов*")
        return

    sorted_orders = sorted(orders, key=lambda x: x.get('likes', 0), reverse=True)[:10]

    text = "🏆 *ТОП-10 ЗАКАЗОВ ПО ЛАЙКАМ*\n\n"
    for i, order in enumerate(sorted_orders, 1):
        text += f"{i}. 🎮 {order['game']} — ❤️ {order.get('likes', 0)} лайков\n"
        text += f"   👤 {order.get('username', 'User')} | 🆔 {order['id']}\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return
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

    text = f"📋 *СТОЛ ЗАКАЗОВ* (Страница {page + 1}/{total_pages})\n\n"

    for order in page_orders:
        try:
            order_date = datetime.fromisoformat(order['date']).strftime("%d.%m.%Y")
        except:
            order_date = "неизвестно"

        status_emoji = {'active': '🟢', 'found': '🟡', 'done': '🔴'}.get(order.get('status'), '🟢')
        status_text = {'active': 'активен', 'found': 'найден', 'done': 'готов'}.get(order.get('status'), 'активен')

        text += f"{status_emoji} *{order['game']}*\n"
        text += f"👤 {order.get('username', 'Пользователь')}\n"
        text += f"📅 {order_date} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} лайков | {status_text}\n"
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
        btn_text = f"❤️ {order['game'][:12]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"like_{order['id']}"))

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = 'waiting_game'
    bot.send_message(message.chat.id, "📝 *Напиши название игры, которую хочешь заказать:*", parse_mode='Markdown')


@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_game')
def get_game(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = {'game': message.text, 'state': 'waiting_size'}
    bot.send_message(message.chat.id, "💾 *Напиши примерный размер игры (в ГБ):*", parse_mode='Markdown')


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

    bot.send_message(message.chat.id,
                     f"✅ *Заказ создан!*\n🆔 ID: {order_id}\n\nСледить за заказами можно по команде /orders",
                     parse_mode='Markdown')


@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private':
        return

    user_orders = [o for o in orders if o.get('user_id') == message.chat.id]
    if not user_orders:
        bot.send_message(message.chat.id, "📭 *У вас нет заказов*\n\nСоздай первый заказ командой /neworder",
                         parse_mode='Markdown')
        return

    text = "👤 *МОИ ЗАКАЗЫ*\n\n"
    for order in user_orders[-10:]:
        status_emoji = {'active': '🟢', 'found': '🟡', 'done': '🔴'}.get(order.get('status'), '🟢')
        text += f"{status_emoji} {order['game']}\n"
        text += f"🆔 {order['id']} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} лайков\n"
        text += "─\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


@bot.message_handler(commands=['editorder'])
def editorder_cmd(message):
    if message.chat.type != 'private':
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: /editorder [ID]")
            return

        order_id = int(parts[1])

        order = None
        for o in orders:
            if o['id'] == order_id:
                order = o
                break

        if not order:
            bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
            return

        if order['user_id'] != message.chat.id and str(message.from_user.id) not in admins:
            bot.reply_to(message, "❌ Редактировать можно только свои заказы")
            return

        user_states[message.chat.id] = {'state': 'editing_order', 'order_id': order_id, 'order': order}

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎮 Изменить название", callback_data=f"edit_name_{order_id}"),
            types.InlineKeyboardButton("💾 Изменить размер", callback_data=f"edit_size_{order_id}"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="edit_cancel")
        )

        bot.send_message(
            message.chat.id,
            f"✏️ *Редактирование заказа #{order_id}*\n\nТекущее название: {order['game']}\nТекущий размер: {order.get('size', 'N/A')}",
            parse_mode='Markdown',
            reply_markup=markup
        )
    except:
        bot.reply_to(message, "❌ Использование: /editorder [ID]")


# ========== ФУНКЦИЯ ОТПРАВКИ ИГР ==========
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
        except Exception as e:
            print(f"Ошибка отправки {file_id}: {e}")

    if user_id:
        uid = str(user_id)
        if uid not in user_stats:
            user_stats[uid] = {'downloads': 0, 'created_orders': 0}
        user_stats[uid]['downloads'] = user_stats[uid].get('downloads', 0) + 1
        user_stats[uid]['last_active'] = datetime.now().isoformat()

        if game_name not in game_stats:
            game_stats[game_name] = {'downloads': 0, 'last_download': None}
        game_stats[game_name]['downloads'] += 1
        game_stats[game_name]['last_download'] = datetime.now().isoformat()
        save_data()

    bot.send_message(chat_id, f"✅ *Готово!* Отправлено {sent_count} файлов\n\n👉 По вопросам: @sweacher")
    return True


# ========== ОБРАБОТЧИК ПОИСКА ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def search_handler(message):
    if message.chat.type != 'private':
        return

    query = message.text.strip().lower()

    if query in GAMES_DATABASE:
        send_game_files(message.chat.id, query, message.from_user.id)
        return

    similar = []
    for game in GAMES_DATABASE.keys():
        if query in game or game in query:
            similar.append(game)

    if similar:
        text = f"❌ *'{message.text}' не найдено*\n\n🎯 *Возможно вы искали:*\n\n"

        markup = types.InlineKeyboardMarkup(row_width=1)
        for game in similar[:5]:
            markup.add(types.InlineKeyboardButton(f"🎮 {game.title()}", callback_data=f"play_{game}"))

        text += "Нажми на кнопку, чтобы скачать:"
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
    else:
        text = f"❌ *'{message.text}' не найдено*\n\n"
        text += "📝 *Создать заказ:* /neworder\n"
        text += "📋 *Посмотреть заказы:* /orders\n\n"
        text += "💡 *Совет:* попробуй написать название на английском"
        bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if str(message.from_user.id) not in admins:
        return

    try:
        broadcast_text = message.text.split(' ', 1)[1]
        sent = 0
        failed = 0

        for uid in user_stats.keys():
            try:
                bot.send_message(int(uid), f"📢 *ОБЪЯВЛЕНИЕ*\n\n{broadcast_text}", parse_mode='Markdown')
                sent += 1
                time.sleep(0.1)
            except:
                failed += 1

        bot.reply_to(message, f"✅ *Рассылка завершена*\n📤 Отправлено: {sent}\n❌ Не отправлено: {failed}",
                     parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Использование: /broadcast [текст]")


@bot.message_handler(commands=['addadmin'])
def addadmin_cmd(message):
    if str(message.from_user.id) not in admins:
        return

    try:
        user_id = str(message.text.split()[1])
        if user_id not in admins:
            admins.append(user_id)
            save_data()
            bot.reply_to(message, f"✅ Пользователь {user_id} добавлен в админы")
        else:
            bot.reply_to(message, "⚠️ Уже админ")
    except:
        bot.reply_to(message, "❌ Использование: /addadmin [ID]")


@bot.message_handler(commands=['delorder'])
def delorder_cmd(message):
    if str(message.from_user.id) not in admins:
        return

    try:
        order_id = int(message.text.split()[1])
        for i, order in enumerate(orders):
            if order['id'] == order_id:
                del orders[i]
                save_data()
                bot.reply_to(message, f"✅ Заказ #{order_id} удалён")
                return
        bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
    except:
        bot.reply_to(message, "❌ Использование: /delorder [ID]")


@bot.message_handler(commands=['set_status'])
def set_status_cmd(message):
    if str(message.from_user.id) not in admins:
        return

    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "❌ Использование: /set_status [ID] [active/found/done]")
            return

        order_id = int(parts[1])
        new_status = parts[2].lower()

        if new_status not in ['active', 'found', 'done']:
            bot.reply_to(message, "❌ Статус должен быть: active, found, done")
            return

        for order in orders:
            if order['id'] == order_id:
                old_status = order.get('status', 'active')
                order['status'] = new_status
                save_data()

                bot.reply_to(message, f"✅ Статус заказа #{order_id}: {old_status} → {new_status}")

                if new_status == 'done' and old_status != 'done':
                    if order['user_id'] != 0:
                        try:
                            bot.send_message(order['user_id'],
                                             f"✅ *ЗАКАЗ ВЫПОЛНЕН!*\n\n🎮 {order['game']}\n🆔 #{order_id}\n\nИгра уже в канале!",
                                             parse_mode='Markdown')
                        except:
                            pass

                    for uid in order.get('liked_by', []):
                        try:
                            bot.send_message(int(uid),
                                             f"✅ *ЗАКАЗ ГОТОВ!*\n\n🎮 {order['game']}\n🆔 #{order_id}\n\nСпасибо за лайк!",
                                             parse_mode='Markdown')
                        except:
                            pass
                return
        bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
    except:
        bot.reply_to(message, "❌ Ошибка")


@bot.message_handler(commands=['done'])
def done_cmd(message):
    if str(message.from_user.id) not in admins:
        return

    try:
        order_id = int(message.text.split()[1])
        for order in orders:
            if order['id'] == order_id:
                if order.get('status') == 'done':
                    bot.reply_to(message, f"⚠️ Заказ #{order_id} уже отмечен как готовый")
                    return

                order['status'] = 'done'
                save_data()

                if order['user_id'] != 0:
                    try:
                        bot.send_message(order['user_id'],
                                         f"✅ *ВАШ ЗАКАЗ ВЫПОЛНЕН!*\n\n🎮 {order['game']}\n🆔 #{order_id}\n\nИгра уже в канале!",
                                         parse_mode='Markdown')
                    except:
                        pass

                for uid in order.get('liked_by', []):
                    try:
                        bot.send_message(int(uid),
                                         f"✅ *ЗАКАЗ ГОТОВ!*\n\n🎮 {order['game']}\n🆔 #{order_id}\n\nСпасибо за лайк!",
                                         parse_mode='Markdown')
                    except:
                        pass

                bot.reply_to(message, f"✅ Заказ #{order_id} отмечен как выполнен, уведомления отправлены")
                return
        bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
    except:
        bot.reply_to(message, "❌ Использование: /done [ID]")


# ========== CALLBACK ОБРАБОТЧИК ==========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith('like_'):
        order_id = int(call.data.split('_')[1])
        for order in orders:
            if order['id'] == order_id:
                if 'liked_by' not in order:
                    order['liked_by'] = []
                if str(call.from_user.id) in order['liked_by']:
                    bot.answer_callback_query(call.id, "❌ Вы уже лайкали этот заказ")
                    return
                order['likes'] = order.get('likes', 0) + 1
                order['liked_by'].append(str(call.from_user.id))
                save_data()
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

    elif call.data.startswith('edit_'):
        if call.data == 'edit_cancel':
            if call.from_user.id in user_states:
                del user_states[call.from_user.id]
            bot.edit_message_text("❌ Редактирование отменено", call.message.chat.id, call.message.message_id)
            return

        parts = call.data.split('_')
        if len(parts) < 3:
            return

        action = parts[1]
        order_id = int(parts[2])

        order = None
        for o in orders:
            if o['id'] == order_id:
                order = o
                break

        if not order:
            bot.answer_callback_query(call.id, "❌ Заказ не найден")
            return

        if order['user_id'] != call.from_user.id and str(call.from_user.id) not in admins:
            bot.answer_callback_query(call.id, "❌ Не ваш заказ")
            return

        if action == 'name':
            user_states[call.from_user.id] = {'state': 'editing_name', 'order_id': order_id}
            bot.edit_message_text(f"✏️ *Введите новое название для заказа #{order_id}*", call.message.chat.id,
                                  call.message.message_id, parse_mode='Markdown')
            bot.answer_callback_query(call.id)
        elif action == 'size':
            user_states[call.from_user.id] = {'state': 'editing_size', 'order_id': order_id}
            bot.edit_message_text(f"✏️ *Введите новый размер для заказа #{order_id} (в ГБ)*", call.message.chat.id,
                                  call.message.message_id, parse_mode='Markdown')
            bot.answer_callback_query(call.id)

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
    elif call.data == "rand_game":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        randgame_cmd(call.message)
    elif call.data == "show_help":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        help_cmd(call.message)
    elif call.data == "get_bonus":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bonus_cmd(call.message)
    elif call.data == "refresh_stats":
        stats_cmd(call.message)
    elif call.data == "mod_active":
        filtered = [o for o in orders if o.get('status') == 'active']
        text = "🟢 *АКТИВНЫЕ ЗАКАЗЫ*\n\n" + "\n".join(
            [f"ID {o['id']}: {o['game']}" for o in filtered[:10]]) if filtered else "Нет активных заказов"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    elif call.data == "mod_found":
        filtered = [o for o in orders if o.get('status') == 'found']
        text = "🟡 *НАЙДЕННЫЕ ЗАКАЗЫ*\n\n" + "\n".join(
            [f"ID {o['id']}: {o['game']}" for o in filtered[:10]]) if filtered else "Нет найденных заказов"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    elif call.data == "mod_done":
        filtered = [o for o in orders if o.get('status') == 'done']
        text = "🔴 *ГОТОВЫЕ ЗАКАЗЫ*\n\n" + "\n".join(
            [f"ID {o['id']}: {o['game']}" for o in filtered[:10]]) if filtered else "Нет готовых заказов"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    elif call.data == "mod_stats":
        total_users = len(user_stats)
        total_orders = len(orders)
        total_downloads = sum(u.get('downloads', 0) for u in user_stats.values())
        text = f"📊 *СТАТИСТИКА*\n\n👥 Пользователей: {total_users}\n📋 Заказов: {total_orders}\n📥 Скачиваний: {total_downloads}"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    elif call.data == "refresh_mod":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        moderator_cmd(call.message)
    elif call.data == "current":
        bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('state') == 'editing_name')
def process_edit_name(message):
    if message.chat.type != 'private':
        return

    data = user_states[message.chat.id]
    order_id = data['order_id']
    new_name = message.text

    for order in orders:
        if order['id'] == order_id:
            order['game'] = new_name
            save_data()
            bot.reply_to(message, f"✅ Название заказа #{order_id} изменено на '{new_name}'")
            break

    del user_states[message.chat.id]


@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('state') == 'editing_size')
def process_edit_size(message):
    if message.chat.type != 'private':
        return

    data = user_states[message.chat.id]
    order_id = data['order_id']
    new_size = message.text.upper() + " ГБ"

    for order in orders:
        if order['id'] == order_id:
            order['size'] = new_size
            save_data()
            bot.reply_to(message, f"✅ Размер заказа #{order_id} изменён на '{new_size}'")
            break

    del user_states[message.chat.id]


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК FERWES GAMES БОТА")
    print("=" * 60)

    files_to_create = [ORDERS_FILE, USER_STATS_FILE, ADMINS_FILE, LIKE_COOLDOWN_FILE, GAME_STATS_FILE]
    for file in files_to_create:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump([] if 'orders' in file else {}, f)

    load_data()

    print(f"🎮 Игр в базе: {len(GAMES_DATABASE)}")
    print(f"📋 Заказов: {len(orders)}")
    print(f"👥 Пользователей: {len(user_stats)}")
    print(f"👑 Админов: {len(admins)}")
    print("=" * 60)
    print("⚡ Бот запущен и готов!")
    print("=" * 60)

    try:
        bot.polling(none_stop=True, skip_pending=True, timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)