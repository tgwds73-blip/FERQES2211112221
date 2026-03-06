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
GAMES_CHANNEL_ID = -1003421344618  # Канал с играми

# Файлы данных
ORDERS_FILE = 'orders.json'
LIKES_FILE = 'likes.json'
ADMINS_FILE = 'admins.json'
USER_STATS_FILE = 'user_stats.json'
LIKE_COOLDOWN_FILE = 'like_cooldown.json'
GAME_STATS_FILE = 'game_stats.json'
WEEKLY_STATS_FILE = 'weekly_stats.json'
PREMIUM_FILE = 'premium_users.json'
BANNED_FILE = 'banned_users.json'
MUTED_FILE = 'muted_users.json'
ORDER_STATS_FILE = 'order_stats.json'
REPORTS_FILE = 'reports.json'

# Константы
LIKE_COOLDOWN_DAYS = 1000
ORDERS_PER_PAGE = 5
PREMIUM_CHAT_LINK = "https://t.me/+Cy47-Mts-h00ZDYy"
PREMIUM_CONTACT = "@sweacher"

# Ранги
RANKS = {
    1000: "👑 GABEN",
    500: "📦 REPACKER",
    100: "🏴‍☠️ PIRATE"
}

# ========== ДАННЫЕ ==========
orders = []
likes_data = {}
admins = ["7885915159"]
user_states = {}
user_stats = {}
like_cooldowns = {}
game_stats = {}
weekly_stats = {}
premium_users = {}
banned_users = {}
muted_users = {}
order_stats = {}
reports = []


# ========== ЗАГРУЗКА/СОХРАНЕНИЕ ==========
def load_all():
    global orders, likes_data, admins, user_stats, like_cooldowns, game_stats, weekly_stats, premium_users, banned_users, muted_users, order_stats, reports

    files = {
        ORDERS_FILE: orders,
        LIKES_FILE: likes_data,
        ADMINS_FILE: admins,
        USER_STATS_FILE: user_stats,
        LIKE_COOLDOWN_FILE: like_cooldowns,
        GAME_STATS_FILE: game_stats,
        WEEKLY_STATS_FILE: weekly_stats,
        PREMIUM_FILE: premium_users,
        BANNED_FILE: banned_users,
        MUTED_FILE: muted_users,
        ORDER_STATS_FILE: order_stats,
        REPORTS_FILE: reports
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
            except Exception as e:
                print(f"Ошибка загрузки {file}: {e}")


def save_all():
    files = {
        ORDERS_FILE: orders,
        LIKES_FILE: likes_data,
        ADMINS_FILE: admins,
        USER_STATS_FILE: user_stats,
        LIKE_COOLDOWN_FILE: like_cooldowns,
        GAME_STATS_FILE: game_stats,
        WEEKLY_STATS_FILE: weekly_stats,
        PREMIUM_FILE: premium_users,
        BANNED_FILE: banned_users,
        MUTED_FILE: muted_users,
        ORDER_STATS_FILE: order_stats,
        REPORTS_FILE: reports
    }

    for file, data in files.items():
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения {file}: {e}")


# ========== ПРОВЕРКИ ==========
def is_admin(user_id):
    return str(user_id) in admins


def is_premium(user_id):
    return str(user_id) in premium_users


def get_user_display_name(user_id, username=None, first_name=None):
    user_id_str = str(user_id)
    if user_id_str in premium_users:
        prefix = premium_users[user_id_str].get('prefix', '')
        if prefix:
            return f"[{prefix}] {first_name or username or user_id}"
    return first_name or username or str(user_id)


def check_rank_update(user_id, old_downloads, new_downloads):
    """Проверяет обновление ранга и возвращает новый ранг если есть"""
    old_rank = None
    new_rank = None

    for threshold, rank_name in sorted(RANKS.items(), reverse=True):
        if old_downloads >= threshold:
            old_rank = rank_name
            break

    for threshold, rank_name in sorted(RANKS.items(), reverse=True):
        if new_downloads >= threshold:
            new_rank = rank_name
            break

    if new_rank and new_rank != old_rank:
        return new_rank
    return None


# ========== БАЗА ИГР ==========
GAMES_DATABASE = {
    'antonblast': list(range(913, 916)),
    'assassins creed': list(range(1028, 1034)),
    'beamng drive': list(range(861, 874)),
    'beholder': list(range(823, 826)),
    'bendy and the ink machine': list(range(652, 655)),
    'bioshock remaster': list(range(1070, 1081)),
    'blender': list(range(1306, 1311)),
    'borderlands 2': list(range(776, 783)),
    'bully': list(range(1639, 1643)),
    'call of duty modern 2': list(range(1212, 1222)),
    'call of duty ww2': list(range(521, 542)),
    'caves of qud': list(range(655, 658)),
    'clair obscur: expedition 33': list(range(1552, 1576)),
    'construction simulator 4': list(range(1373, 1376)),
    'counter strike 1.6': list(range(1453, 1456)),
    'cry of fear': list(range(1481, 1487)),
    'cry of fear 2012': list(range(1481, 1487)),
    'cuphead': list(range(817, 822)),
    'cyberpunk 2077': list(range(658, 705)),
    'dark souls 3': list(range(880, 895)),
    'dead space': list(range(1576, 1581)),
    'dead space remake': list(range(1581, 1600)),
    'detroit': list(range(1407, 1437)),
    'detroit become human': list(range(1407, 1437)),
    'devil may cry 4 special edition': list(range(1244, 1259)),
    'dispatch': list(range(1311, 1321)),
    'distant worlds 2': list(range(1644, 1651)),
    'dying light: the beast': list(range(1502, 1526)),
    'elden ring': list(range(552, 588)),
    'fallout 3': list(range(1231, 1237)),
    'fallout 4': list(range(1277, 1297)),
    'far cry 2': list(range(1437, 1441)),
    'far cry 3': list(range(783, 788)),
    'far cry 4': list(range(1354, 1370)),
    'far cry 5': list(range(242, 255)),
    'farm frenzy': list(range(1456, 1459)),
    'fifa 17': list(range(916, 932)),
    'finding frankie': list(range(622, 627)),
    'five nights at freddys': list(range(948, 951)),
    'five nights at freddys secret of the mimic': list(range(1462, 1474)),
    'fl studio 25': list(range(1153, 1157)),
    'friday night funkin': list(range(748, 751)),
    'frostpunk': list(range(1222, 1229)),
    'frostpunk 2': list(range(1619, 1628)),
    'garrys mod': list(range(858, 861)),
    'ghost of tsushima': list(range(1527, 1552)),
    'ghostrunner': list(range(1379, 1389)),
    'goat simulator': list(range(618, 622)),
    'Grand Theft Auto III': list(range(1088, 1091)),
    'Grand Theft Auto IV': list(range(799, 811)),
    'Grand Theft Auto: Liberty City Stories': list(range(1082, 1085)),
    'Grand Theft Auto: San Andreas': list(range(1259, 1271)),
    'Grand Theft Auto V': list(range(705, 743)),
    'Grand Theft Auto: Vice City': list(range(1450, 1453)),
    'Grand Theft Auto: Vice City Stories': list(range(902, 905)),
    'half life 2': list(range(1207, 1212)),
    'hard time 3': list(range(1006, 1010)),
    'hearts of iron 4': list(range(743, 748)),
    'hearts of iron 4: ultimate bundle': list(range(1497, 1502)),
    'hitman': list(range(962, 986)),
    'hitman blood money': list(range(951, 961)),
    'hollow knight': list(range(1060, 1063)),
    'hollow knight: silksong': list(range(1600, 1603)),
    'hotline miami': list(range(1085, 1088)),
    'hotline miami 2': [1159, 1160],
    'humanit z': list(range(1096, 1111)),
    'hytale': list(range(1398, 1403)),
    'jewel match': list(range(234, 237)),
    'korsary 3': list(range(1370, 1373)),
    'little nightmares 3': list(range(174, 183)),
    'lonarpg': list(range(1447, 1450)),
    'mafia 1': list(range(1241, 1244)),
    'mafia 2': list(range(942, 948)),
    'metro 2033': list(range(1051, 1057)),
    'metro last light redux': list(range(1606, 1612)),
    'minecraft': list(range(932, 936)),
    'my gaming club': list(range(811, 814)),
    'my summer car': list(range(1441, 1444)),
    'my winter car': list(range(1347, 1350)),
    'mysided': list(range(1057, 1060)),
    'nier: automata': list(range(164, 174)),
    'no im not a human': list(range(517, 521)),
    'one shot': list(range(1065, 1070)),
    'orion sandbox': list(range(814, 817)),
    'palworld': list(range(202, 217)),
    'payday: the heist': list(range(876, 880)),
    'people playground': list(range(1603, 1606)),
    'plants vs zombies': list(range(549, 552)),
    'portal knights': list(range(1237, 1240)),
    'postal 2': list(range(1615, 1618)),
    'project zomboid': list(range(1093, 1096)),
    'prototype 1': list(range(895, 902)),
    'prototype 2': list(range(1044, 1051)),
    'quasimorph': list(range(589, 592)),
    'red dead redemption': list(range(542, 549)),
    'red dead redemption 2': list(range(428, 486)),
    'resident evil revelations 2': list(range(788, 799)),
    'resident evil resistance': list(range(1330, 1347)),
    'resident evil village': list(range(826, 846)),
    'rimworld': list(range(1298, 1302)),
    'risk of rain 2': list(range(1612, 1615)),
    'rock star life simulator': list(range(184, 187)),
    'stalker anomaly': list(range(1628, 1635)),
    'stalker shadow of chernobyl': list(range(1326, 1330)),
    'sally face': list(range(628, 633)),
    'scorn': list(range(217, 228)),
    'slim rancher': list(range(853, 858)),
    'slime rancher 2': list(range(1323, 1326)),
    'spider man remastered': list(range(486, 517)),
    'stray': list(range(936, 942)),
    'streets of rogue 2': list(range(1041, 1044)),
    'system shock 2 remaster': list(range(187, 193)),
    'teardown': list(range(906, 913)),
    'terraria': list(range(1459, 1462)),
    'terraria 1.4.4.9': list(range(1350, 1353)),
    'the forest': list(range(633, 636)),
    'the last of us': list(range(1119, 1153)),
    'the long drive': list(range(1444, 1447)),
    'the spike': list(range(846, 853)),
    'third crisis': list(range(1302, 1306)),
    'tomb raider 2013': list(range(1487, 1497)),
    'uber soldier': list(range(197, 202)),
    'undertale': list(range(1376, 1379)),
    'watch dogs 2': list(range(1010, 1028)),
    'witcher 3': list(range(986, 1006)),
    'world box': list(range(1036, 1041)),
}


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
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'rank': None
        }
        save_all()

    text = """🔍 *Напиши название игры* — я пришлю, если есть.

📋 `/orders` — стол заказов  
📝 `/neworder` — новый заказ  
👤 `/myorders` — мои заказы  
📊 `/stats` — моя статистика  
🔥 `/top` — топ игр  
💎 `/premium` — премиум  
ℹ️ `/help` — помощь  
📚 `/info` — о боте  
🎲 `/randgame` — случайная игра  
🏆 `/toporders` — топ заказов  
✏️ `/editorder ID` — редактировать свой заказ"""

    if is_admin(message.from_user.id):
        text += "\n\n👑 `/moderator` — панель модератора"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="my_stats"),
        types.InlineKeyboardButton("🔥 Топ игр", callback_data="show_top"),
        types.InlineKeyboardButton("💎 Премиум", callback_data="show_premium"),
        types.InlineKeyboardButton("ℹ️ Помощь", callback_data="show_help")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА MODERATOR ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Нет прав")
        return

    if message.chat.type != 'private':
        return

    text = "👑 *Панель модератора*\n\n"
    text += "📊 `/stats` — статистика бота\n"
    text += "❌ `/delorder ID` — удалить заказ\n"
    text += "👑 `/addadmin ID` — добавить админа\n"
    text += "🔨 `/ban ID причина [тихий]` — заблокировать\n"
    text += "🔇 `/mute ID причина [часы]` — запретить заказы\n"
    text += "📢 `/broadcast текст` — рассылка\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА ADDADMIN ==========
@bot.message_handler(commands=['addadmin'])
def addadmin_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = str(message.text.split()[1])
        if user_id in admins:
            bot.reply_to(message, "⚠️ Уже админ")
        else:
            admins.append(user_id)
            save_all()
            bot.reply_to(message, f"✅ ID {user_id} теперь админ")
    except:
        bot.reply_to(message, "❌ Использование: /addadmin ID")


# ========== КОМАНДА BAN ==========
@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 3:
            bot.reply_to(message, "❌ /ban ID причина [тихий]")
            return

        user_id = parts[1]
        reason = parts[2]
        ban_type = 'normal'

        if len(parts) > 3 and parts[3].lower() == 'тихий':
            ban_type = 'silent'

        banned_users[user_id] = {
            'type': ban_type,
            'reason': reason,
            'banned_by': str(message.from_user.id),
            'banned_at': datetime.now().isoformat()
        }

        save_all()
        type_text = "тихий" if ban_type == 'silent' else "обычный"
        bot.reply_to(message, f"✅ Пользователь {user_id} забанен ({type_text})\nПричина: {reason}")
    except:
        bot.reply_to(message, "❌ Ошибка")


# ========== КОМАНДА MUTE ==========
@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 3:
            bot.reply_to(message, "❌ /mute ID причина [часы]")
            return

        user_id = parts[1]
        reason = parts[2]
        until = None

        if len(parts) > 3:
            try:
                hours = int(parts[3])
                until = datetime.now() + timedelta(hours=hours)
            except:
                pass

        muted_users[user_id] = {
            'reason': reason,
            'until': until.isoformat() if until else None,
            'muted_by': str(message.from_user.id),
            'muted_at': datetime.now().isoformat()
        }

        save_all()

        if until:
            until_str = until.strftime("%d.%m.%Y %H:%M")
            bot.reply_to(message, f"✅ Пользователь {user_id} замучен до {until_str}\nПричина: {reason}")
        else:
            bot.reply_to(message, f"✅ Пользователь {user_id} замучен навсегда\nПричина: {reason}")
    except:
        bot.reply_to(message, "❌ Ошибка")


# ========== КОМАНДА UNBAN ==========
@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = message.text.split()[1]
        if user_id in banned_users:
            del banned_users[user_id]
            save_all()
            bot.reply_to(message, f"✅ Пользователь {user_id} разбанен")
        else:
            bot.reply_to(message, f"❌ Пользователь {user_id} не в бане")
    except:
        bot.reply_to(message, "❌ Использование: /unban ID")


# ========== КОМАНДА UNMUTE ==========
@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = message.text.split()[1]
        if user_id in muted_users:
            del muted_users[user_id]
            save_all()
            bot.reply_to(message, f"✅ Мут снят с {user_id}")
        else:
            bot.reply_to(message, f"❌ Пользователь {user_id} не в муте")
    except:
        bot.reply_to(message, "❌ Использование: /unmute ID")


# ========== КОМАНДА DELORDER ==========
@bot.message_handler(commands=['delorder'])
def delorder_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        order_id = int(message.text.split()[1])
        for i, order in enumerate(orders):
            if order['id'] == order_id:
                del orders[i]
                save_all()
                bot.reply_to(message, f"✅ Заказ #{order_id} удален")
                return
        bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
    except:
        bot.reply_to(message, "❌ Использование: /delorder ID")


# ========== КОМАНДА BROADCAST ==========
@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        return

    try:
        text = message.text.split(' ', 1)[1]
        sent = 0
        failed = 0

        for user_id_str in user_stats.keys():
            try:
                bot.send_message(int(user_id_str), f"📢 *Объявление*\n\n{text}", parse_mode='Markdown')
                sent += 1
                time.sleep(0.05)
            except:
                failed += 1

        bot.reply_to(message, f"✅ Рассылка завершена\n📤 Отправлено: {sent}\n❌ Не отправлено: {failed}")
    except:
        bot.reply_to(message, "❌ Использование: /broadcast текст")


# ========== КОМАНДА HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private':
        return

    text = """ℹ️ *Справка команд*

📋 *Основные команды:*
• `/start` — главное меню 
• `/help` — эта справка
• `/info` — информация о боте

📦 *Заказы:*
• `/orders` — стол заказов
• `/neworder` — новый заказ
• `/myorders` — мои заказы
• `/editorder ID` — редактировать свой заказ

🎮 *Игры:*
• Напиши название игры — поиск
• `/top` — топ игр по скачиваниям
• `/randgame` — случайная игра
• `/stats` — моя статистика

🏆 *Рейтинги:*
• `/toporders` — топ заказов по лайкам

💎 *Премиум:*
• `/premium` — информация о премиум

👑 *Для админов:*
• `/moderator` — панель модератора

❓ *ТехПоддержка:*
• @sweacher
"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА INFO ==========
@bot.message_handler(commands=['info'])
def info_cmd(message):
    if message.chat.type != 'private':
        return

    total_users = len(user_stats)
    total_orders = len(orders)
    total_games = len(GAMES_DATABASE)
    total_downloads = sum(stats.get('downloads', 0) for stats in user_stats.values())
    total_likes = sum(order.get('likes', 0) for order in orders)

    today = datetime.now().strftime("%Y-%m-%d")
    active_today = 0
    for user_id, stats in user_stats.items():
        last_seen = stats.get('last_seen')
        if last_seen and last_seen.startswith(today):
            active_today += 1

    text = f"""📚 *Информация о боте Ferwes*

🤖 *Версия:* 1.8.3.8
📊 *Статистика:*
• 👥 Пользователей: {total_users}
• 📋 Заказов: {total_orders}
• 🎮 Игр в базе: {total_games}
• 📥 Всего скачиваний: {total_downloads}
• 📅 Активных сегодня: {active_today}

👑 *Администрация:*
• Владелец: @ferwesgames
• Контакт: {PREMIUM_CONTACT}

"""
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА PREMIUM ==========
@bot.message_handler(commands=['premium'])
def premium_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = str(message.from_user.id)

    if user_id in premium_users:
        prefix_info = premium_users[user_id]
        text = f"""💎 *У вас уже есть премиум!*

Ваш префикс: `[{prefix_info.get('prefix', '')}]`
Куплен: {prefix_info.get('purchased_date', 'неизвестно')}

📌 Префикс работает, пока вы в чате:  
{PREMIUM_CHAT_LINK}

📩 По вопросам: {PREMIUM_CONTACT}"""
    else:
        text = f"""💎 *Премиум — префикс в чате*

🔥 Префикс сохраняется навсегда!

**Что даёт премиум:**
• Уникальный префикс в чате
• Выделение среди других пользователей

💳 *Реквизиты для оплаты:*  
ЮMoney: `4100119022808101`  
Стоимость: **150 рублей**

После оплаты пришлите скриншот {PREMIUM_CONTACT}

📌 *Обязательно:* вступите в чат:  
{PREMIUM_CHAT_LINK}

⚠️ Не выходите из чата, чтобы префикс не сбился."""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Вступить в чат", url=PREMIUM_CHAT_LINK))
    markup.add(types.InlineKeyboardButton("✍️ Написать @sweacher", url="https://t.me/sweacher"))

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА RANDGAME ==========
@bot.message_handler(commands=['randgame'])
def randgame_cmd(message):
    if message.chat.type != 'private':
        return

    game_name = random.choice(list(GAMES_DATABASE.keys()))
    send_game_files(message.chat.id, game_name, message.from_user.id)


# ========== КОМАНДА STATS ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.chat.type != 'private':
        return

    user_id_str = str(message.from_user.id)

    if user_id_str not in user_stats:
        bot.reply_to(message, "📊 *Вы еще ничего не скачали*")
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
    total_likes_given = len([uid for uid in like_cooldowns if uid == user_id_str])

    user_games = {}
    for order in user_orders:
        game = order['game']
        user_games[game] = user_games.get(game, 0) + 1

    most_popular = max(user_games.items(), key=lambda x: x[1]) if user_games else ("нет", 0)
    avg_likes = total_likes_received / created_orders if created_orders > 0 else 0

    all_users_downloads = [u.get('downloads', 0) for u in user_stats.values()]
    better_than = sum(1 for d in all_users_downloads if d < downloads)
    total_users = len(user_stats)
    percentile = (better_than / total_users * 100) if total_users > 0 else 0

    # Определяем текущий ранг
    current_rank = None
    for threshold, rank_name in sorted(RANKS.items(), reverse=True):
        if downloads >= threshold:
            current_rank = rank_name
            break

    premium_status = "✅ Да" if is_premium(message.from_user.id) else "❌ Нет"

    text = f"👑 *ПОДРОБНАЯ СТАТИСТИКА* 👑\n\n"
    text += f"👤 *Пользователь:* {message.from_user.first_name or 'Неизвестно'}\n"
    text += f"🆔 *ID:* {message.from_user.id}\n"
    text += f"💎 *Премиум:* {premium_status}\n"
    if current_rank:
        text += f"🏅 *Ранг:* {current_rank}\n\n"
    else:
        text += f"\n"
    text += f"━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 *ОСНОВНАЯ СТАТИСТИКА*\n"
    text += f"━━━━━━━━━━━━━━━━━━\n"
    text += f"📥 *Скачано игр:* {downloads}\n"
    text += f"📋 *Создано заказов:* {created_orders}\n"
    text += f"❤️ *Получено лайков:* {total_likes_received}\n"
    text += f"👍 *Поставлено лайков:* {total_likes_given}\n"
    text += f"⭐ *Средний лайк:* {avg_likes:.1f}\n"
    text += f"📅 *Активен дней:* {days_active}\n\n"
    text += f"━━━━━━━━━━━━━━━━━━\n"
    text += f"🏆 *ДОСТИЖЕНИЯ*\n"
    text += f"━━━━━━━━━━━━━━━━━━\n"
    text += f"🎮 *Любимая игра:* {most_popular[0]} ({most_popular[1]} раз)\n"
    text += f"📊 *Вы лучше чем:* {percentile:.1f}% пользователей\n"

    # Достижения
    achievements = []
    if downloads >= 1000:
        achievements.append("👑 *GABEN* — 1000+ скачиваний")
    elif downloads >= 500:
        achievements.append("📦 *REPACKER* — 500+ скачиваний")
    elif downloads >= 100:
        achievements.append("🏴‍☠️ *PIRATE* — 100+ скачиваний")

    if total_likes_received >= 50:
        achievements.append("⭐ *Кумир* — 50+ лайков на заказах")

    if created_orders >= 20:
        achievements.append("📝 *Писатель* — 20+ созданных заказов")

    if achievements:
        text += "\n" + "\n".join(achievements) + "\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА TOPORDERS ==========
@bot.message_handler(commands=['toporders'])
def toporders_cmd(message):
    if message.chat.type != 'private':
        return

    if not orders:
        bot.send_message(message.chat.id, "📭 Нет заказов")
        return

    sorted_orders = sorted(orders, key=lambda x: x.get('likes', 0), reverse=True)[:10]

    text = "🏆 *Топ-10 заказов по лайкам*\n\n"

    for i, order in enumerate(sorted_orders, 1):
        text += f"{i}. 🎮 {order['game']} — ❤️ {order.get('likes', 0)} лайков\n"
        text += f"   👤 {order.get('username', 'User')} | 🆔 {order['id']}\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА EDITORDER ==========
@bot.message_handler(commands=['editorder'])
def editorder_cmd(message):
    if message.chat.type != 'private':
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Использование: /editorder ID")
            return

        order_id = int(parts[1])

        # Ищем заказ
        order = None
        for o in orders:
            if o['id'] == order_id:
                order = o
                break

        if not order:
            bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
            return

        # Проверяем, автор ли это
        if order['user_id'] != message.chat.id and not is_admin(message.from_user.id):
            bot.reply_to(message, "❌ Вы можете редактировать только свои заказы")
            return

        user_states[message.chat.id] = {
            'state': 'editing_order',
            'order_id': order_id,
            'order': order
        }

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎮 Изменить название", callback_data=f"edit_name_{order_id}"),
            types.InlineKeyboardButton("💾 Изменить размер", callback_data=f"edit_size_{order_id}"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="edit_cancel")
        )

        bot.send_message(
            message.chat.id,
            f"✏️ *Редактирование заказа #{order_id}*\n\n"
            f"Текущее название: {order['game']}\n"
            f"Текущий размер: {order.get('size', 'N/A')}\n\n"
            f"Что хотите изменить?",
            parse_mode='Markdown',
            reply_markup=markup
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# ========== КОМАНДА REPORT ==========
@bot.message_handler(commands=['report'])
def report_cmd(message):
    if message.chat.type != 'private':
        return

    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Использование: /report ID_заказа причина")
            return

        order_id = int(parts[1])
        reason = parts[2]

        # Ищем заказ
        order = None
        for o in orders:
            if o['id'] == order_id:
                order = o
                break

        if not order:
            bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
            return

        # Создаем жалобу
        report = {
            'order_id': order_id,
            'reporter_id': message.from_user.id,
            'reporter_name': message.from_user.first_name or str(message.from_user.id),
            'reason': reason,
            'time': datetime.now().isoformat()
        }
        reports.append(report)
        save_all()

        # Уведомляем всех админов
        admin_text = f"🚨 *Новая жалоба!*\n\n"
        admin_text += f"📋 Заказ #{order_id}: {order['game']}\n"
        admin_text += f"👤 Пожаловался: {message.from_user.first_name} (ID: {message.from_user.id})\n"
        admin_text += f"📝 Причина: {reason}"

        for admin_id in admins:
            try:
                bot.send_message(int(admin_id), admin_text, parse_mode='Markdown')
            except:
                pass

        bot.reply_to(message, f"✅ Жалоба на заказ #{order_id} отправлена администрации")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# ========== КОМАНДА TOP ==========
@bot.message_handler(commands=['top'])
def top_cmd(message):
    if message.chat.type != 'private':
        return

    if game_stats:
        sorted_games = sorted(game_stats.items(), key=lambda x: x[1]['downloads'], reverse=True)[:10]

        text = "🔥 *Топ игр по скачиваниям*\n\n"
        for i, (game, stats) in enumerate(sorted_games, 1):
            text += f"{i}. 🎮 {game} — {stats['downloads']} 📥\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "📊 Нет данных для топа")


# ========== КОМАНДА ORDERS ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return

    show_orders_page(message.chat.id, 0, message)


def show_orders_page(chat_id, page=0, original_message=None):
    if not orders:
        bot.send_message(chat_id, "📭 Нет заказов")
        return

    total_pages = (len(orders) + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0

    start_idx = page * ORDERS_PER_PAGE
    end_idx = min(start_idx + ORDERS_PER_PAGE, len(orders))
    page_orders = orders[start_idx:end_idx]

    text = f"📋 *Стол заказов* (Страница {page + 1}/{total_pages})\n\n"

    for order in page_orders:
        try:
            order_date = datetime.fromisoformat(order['date']).strftime("%d.%m.%Y")
        except:
            order_date = "неизвестно"

        user_display = get_user_display_name(
            order.get('user_id'),
            order.get('username'),
            None
        )

        edit_mark = " ✏️" if (original_message and order.get('user_id') == original_message.from_user.id) else ""

        text += f"🎮 *{order['game']}*{edit_mark}\n"
        text += f"👤 {user_display}\n"
        text += f"📅 {order_date} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} лайков\n"
        text += f"🆔 {order['id']}\n"
        text += "─\n"

    markup = types.InlineKeyboardMarkup(row_width=2)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Назад", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="current_page"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперед ➡️", callback_data=f"orders_page_{page + 1}"))
    if nav_buttons:
        markup.row(*nav_buttons)

    for order in page_orders:
        btn_text = f"❤️ {order['game'][:12]}"
        if len(order['game']) > 12:
            btn_text += "..."

        if original_message and order.get('user_id') == original_message.from_user.id:
            markup.row(
                types.InlineKeyboardButton(btn_text, callback_data=f"like_{order['id']}"),
                types.InlineKeyboardButton("⚠️ Жалоба", callback_data=f"report_{order['id']}"),
                types.InlineKeyboardButton("✏️ Ред.", callback_data=f"edit_{order['id']}"),
                types.InlineKeyboardButton("📤 Поделиться", callback_data=f"share_{order['id']}")
            )
        else:
            markup.row(
                types.InlineKeyboardButton(btn_text, callback_data=f"like_{order['id']}"),
                types.InlineKeyboardButton("⚠️ Жалоба", callback_data=f"report_{order['id']}"),
                types.InlineKeyboardButton("📤 Поделиться", callback_data=f"share_{order['id']}")
            )

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА NEWORDER ==========
@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = 'waiting_game'
    bot.reply_to(message, "📝 *Напиши название заказа:*", parse_mode='Markdown')


@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_game')
def get_game(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = {'game': message.text, 'state': 'waiting_size'}
    bot.reply_to(message, "💾 *Напиши размер игры:*", parse_mode='Markdown')


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
        'date': datetime.now().isoformat()
    })

    user_id_str = str(message.from_user.id)
    if user_id_str not in user_stats:
        user_stats[user_id_str] = {'downloads': 0, 'created_orders': 0}
    user_stats[user_id_str]['created_orders'] = user_stats[user_id_str].get('created_orders', 0) + 1

    save_all()
    del user_states[message.chat.id]
    bot.reply_to(message, f"✅ *Заказ создан и находится в столе заказов!*\n🆔 ID: {order_id}", parse_mode='Markdown')


# ========== КОМАНДА MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private':
        return

    user_id = message.chat.id
    user_orders = [o for o in orders if o.get('user_id') == user_id]

    if not user_orders:
        bot.send_message(message.chat.id, "📭 У вас нет заказов")
        return

    text = "👤 *Мои заказы*\n\n"
    for order in user_orders[-10:]:
        text += f"🎮 {order['game']}\n"
        text += f"🆔 {order['id']} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} лайков\n"
        text += "─\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== ФУНКЦИЯ ОТПРАВКИ ИГР ==========
def send_game_files(chat_id, game_name, user_id=None):
    sent_count = 0

    if game_name in GAMES_DATABASE:
        bot.send_message(chat_id, f"🎮 *{game_name.upper()}*\n📥 Отправляю...", parse_mode='Markdown')

        for file_id in GAMES_DATABASE[game_name]:
            try:
                bot.copy_message(chat_id, GAMES_CHANNEL_ID, file_id)
                sent_count += 1
                time.sleep(0.3)
            except:
                pass

        if user_id:
            user_id_str = str(user_id)
            old_downloads = user_stats[user_id_str].get('downloads', 0) if user_id_str in user_stats else 0

            if user_id_str not in user_stats:
                user_stats[user_id_str] = {'downloads': 0, 'created_orders': 0}

            user_stats[user_id_str]['downloads'] = user_stats[user_id_str].get('downloads', 0) + 1
            user_stats[user_id_str]['last_seen'] = datetime.now().isoformat()

            new_downloads = user_stats[user_id_str]['downloads']

            # Проверяем обновление ранга
            new_rank = check_rank_update(user_id_str, old_downloads, new_downloads)
            if new_rank:
                try:
                    bot.send_message(
                        int(user_id_str),
                        f"🏆 *Поздравляем!*\n\nВы достигли ранга *{new_rank}*!",
                        parse_mode='Markdown'
                    )
                except:
                    pass

            if game_name not in game_stats:
                game_stats[game_name] = {'downloads': 0, 'last_download': None}
            game_stats[game_name]['downloads'] += 1
            game_stats[game_name]['last_download'] = datetime.now().isoformat()

            save_all()

        bot.send_message(chat_id, f"✅ *Готово! Отправлено {sent_count} файлов*")
        return True

    return False


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
        text = f"❌ *'{message.text}' не найдено*\n\n"
        text += "🎯 Возможно вы искали:\n\n"

        markup = types.InlineKeyboardMarkup(row_width=1)

        for game in similar[:5]:
            markup.add(types.InlineKeyboardButton(
                f"🎮 {game.title()}",
                callback_data=f"play_{game}"
            ))

        text += "Нажмите на кнопку, чтобы скачать:"

        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)

    else:
        text = f"❌ *'{message.text}' не имеется, попробуйте написать по другому, если до сих пор нет закажите!*\n\n"
        text += "📝 *Создать заказ:* /neworder\n"
        text += "📋 *Посмотреть заказы:* /orders"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')


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
                    bot.answer_callback_query(call.id, "❌ Лайк уже был!")
                    return
                order['likes'] = order.get('likes', 0) + 1
                order['liked_by'].append(str(call.from_user.id))
                save_all()
                bot.answer_callback_query(call.id, "❤️ Лайк поставлен!")
                return

    elif call.data.startswith('report_'):
        order_id = int(call.data.split('_')[1])

        # Находим заказ
        order = None
        for o in orders:
            if o['id'] == order_id:
                order = o
                break

        if not order:
            bot.answer_callback_query(call.id, "❌ Заказ не найден")
            return

        # Запрашиваем причину
        user_states[call.from_user.id] = {
            'state': 'waiting_report_reason',
            'order_id': order_id
        }

        bot.edit_message_text(
            f"📝 *Напишите причину жалобы на заказ #{order_id}*",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith('share_'):
        order_id = int(call.data.split('_')[1])
        for order in orders:
            if order['id'] == order_id:
                text = f"📤 *Заказ #{order_id}*\n🎮 {order['game']}\n💾 {order.get('size', 'N/A')}"
                bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
                bot.answer_callback_query(call.id)
                return

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
            bot.edit_message_text(
                "❌ Редактирование отменено",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
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

        if order['user_id'] != call.from_user.id and not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Это не ваш заказ")
            return

        if action == 'name':
            user_states[call.from_user.id] = {
                'state': 'editing_name',
                'order_id': order_id
            }
            bot.edit_message_text(
                f"✏️ *Введите новое название для заказа #{order_id}*",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id)

        elif action == 'size':
            user_states[call.from_user.id] = {
                'state': 'editing_size',
                'order_id': order_id
            }
            bot.edit_message_text(
                f"✏️ *Введите новый размер для заказа #{order_id} (в ГБ)*",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
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
    elif call.data == "show_premium":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        premium_cmd(call.message)
    elif call.data == "show_help":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        help_cmd(call.message)


# ========== ОБРАБОТЧИК РЕДАКТИРОВАНИЯ НАЗВАНИЯ ==========
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
            save_all()
            bot.reply_to(message, f"✅ Название заказа #{order_id} изменено на '{new_name}'")
            break

    del user_states[message.chat.id]


# ========== ОБРАБОТЧИК РЕДАКТИРОВАНИЯ РАЗМЕРА ==========
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
            save_all()
            bot.reply_to(message, f"✅ Размер заказа #{order_id} изменён на '{new_size}'")
            break

    del user_states[message.chat.id]


# ========== ОБРАБОТЧИК ЖАЛОБЫ ==========
@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('state') == 'waiting_report_reason')
def process_report_reason(message):
    if message.chat.type != 'private':
        return

    data = user_states[message.chat.id]
    order_id = data['order_id']
    reason = message.text

    # Находим заказ
    order = None
    for o in orders:
        if o['id'] == order_id:
            order = o
            break

    if not order:
        bot.reply_to(message, f"❌ Заказ #{order_id} не найден")
        del user_states[message.chat.id]
        return

    # Создаем жалобу
    report = {
        'order_id': order_id,
        'reporter_id': message.from_user.id,
        'reporter_name': message.from_user.first_name or str(message.from_user.id),
        'reason': reason,
        'time': datetime.now().isoformat()
    }
    reports.append(report)
    save_all()

    # Уведомляем всех админов
    admin_text = f"🚨 *Новая жалоба!*\n\n"
    admin_text += f"📋 Заказ #{order_id}: {order['game']}\n"
    admin_text += f"👤 Пожаловался: {message.from_user.first_name} (ID: {message.from_user.id})\n"
    admin_text += f"📝 Причина: {reason}"

    for admin_id in admins:
        try:
            bot.send_message(int(admin_id), admin_text, parse_mode='Markdown')
        except:
            pass

    bot.reply_to(message, f"✅ Жалоба на заказ #{order_id} отправлена администрации")
    del user_states[message.chat.id]


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК FERWES GAMES БОТА")
    print("=" * 60)

    files_to_create = [
        ORDERS_FILE, LIKES_FILE, ADMINS_FILE,
        USER_STATS_FILE, LIKE_COOLDOWN_FILE,
        GAME_STATS_FILE, WEEKLY_STATS_FILE,
        PREMIUM_FILE, BANNED_FILE, MUTED_FILE,
        ORDER_STATS_FILE, REPORTS_FILE
    ]

    for file in files_to_create:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                if file.endswith('.json'):
                    json.dump([] if 'orders' in file or file == REPORTS_FILE else {}, f)

    load_all()

    print(f"🎮 Игр в базе: {len(GAMES_DATABASE)}")
    print(f"📋 Заказов: {len(orders)}")
    print(f"👥 Пользователей: {len(user_stats)}")
    print(f"👑 Админов: {len(admins)}")
    print("=" * 60)
    print("⚡ Бот запущен и готов!")
    print("=" * 60)

    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)