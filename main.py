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
CRACKED_GAMES_FILE = 'cracked_games.json'

# ========== ДАННЫЕ ==========
orders = []
user_stats = {}
admins = ["7885915159"]
user_states = {}
cracked_games = []
like_cooldowns = {}
game_stats = {}

# Константы
LIKE_COOLDOWN_DAYS = 1000
ORDERS_PER_PAGE = 5

# Новый баннер для игр
GAME_BANNER = """
🔥 БЕЗ ВСТРОЕННЫХ ПРОГРАММ ИЛИ ВИРУСОВ
🔥 FERWES / GAMES (https://t.me/FerwesGames)
🔥 FERWES / GRID (https://t.me/addlist/AW1LBTA9xa45NDIy)
"""

## ========== ПОЛНАЯ БАЗА ВСЕХ ИГР (ПО АЛФАВИТУ) ==========

GAMES_DATABASE = {

    # A
    'alan wake 2': list(range(1745, 1754)) + [1749],
    'antonblast': list(range(913, 915)) + [1749],
    'assassins creed': list(range(1028, 1033)) + [1749],
    'assassins creed mirage': list(range(1805, 1814)) + [1749],

    # B
    'bad cheese': list(range(1651, 1654)) + [1749],
    'badcheese': list(range(1651, 1654)) + [1749],
    'baldurs gate 3': list(range(1730, 1744)) + [1749],
    'beamng drive': list(range(861, 873)) + [1749],
    'beholder': list(range(823, 825)) + [1749],
    'bendy and the ink machine': list(range(652, 654)) + [1749],
    'bioshock remaster': list(range(1070, 1080)) + [1749],
    'blender': list(range(1306, 1310)) + [1749],
    'borderlands 2': list(range(776, 782)) + [1749],
    'borderlands 4': list(range(1702, 1711)) + [1749],  # Новая игра
    'bully': list(range(1639, 1642)) + [1749],

    # C
    'call of duty modern warfare 2': list(range(1212, 1221)) + [1749],
    'call of duty ww2': list(range(521, 541)) + [1749],
    'caves of qud': list(range(655, 657)) + [1749],
    'chesscraft': list(range(1655, 1657)) + [1749],
    'chess craft': list(range(1655, 1657)) + [1749],
    'clair obscur: expedition 33': list(range(1552, 1575)) + [1749],
    'construction simulator 4': list(range(1373, 1375)) + [1749],
    'counter strike 1.6': list(range(1453, 1455)) + [1749],
    'cry of fear': list(range(1481, 1486)) + [1749],
    'cry of fear 2012': list(range(1481, 1486)) + [1749],
    'cuphead': list(range(817, 821)) + [1749],
    'cyberpunk 2077': list(range(658, 704)) + [1749],
    'cyberpunk 2077 phantom liberty': list(range(1815, 1824)) + [1749],

    # D
    'dark souls 3': list(range(880, 894)) + [1749],
    'dead space': list(range(1576, 1580)) + [1749],
    'dead space remake': list(range(1581, 1599)) + [1749],
    'detroit': list(range(1407, 1436)) + [1749],
    'detroit become human': list(range(1407, 1436)) + [1749],
    'devil may cry 4': list(range(1244, 1258)) + [1749],
    'diablo 4': list(range(1765, 1774)) + [1749],
    'dispatch': list(range(1311, 1320)) + [1749],
    'distant worlds 2': list(range(1644, 1650)) + [1749],
    'doom the dark ages': list(range(1706, 1749)) + [1749],
    'doom dark ages': list(range(1706, 1749)) + [1749],
    'dying light': list(range(751, 775)) + [1749],
    'dying light: the beast': list(range(1502, 1525)) + [1749],

    # E
    'ea sports fc 25': list(range(1795, 1804)) + [1749],
    'elden ring': list(range(552, 587)) + [1749],

    # F
    'f1 24': list(range(1785, 1794)) + [1749],
    'fallout 3': list(range(1231, 1236)) + [1749],
    'fallout 4': list(range(1277, 1296)) + [1749],
    'far cry': list(range(1658, 1661)) + [1749],
    'far cry 1': list(range(1658, 1661)) + [1749],
    'far cry 2': list(range(1662, 1665)) + [1749],
    'far cry 3': list(range(783, 787)) + [1749],
    'far cry 4': list(range(1354, 1369)) + [1749],
    'far cry 5': list(range(242, 254)) + [1749],
    'far cry 6': list(range(242, 254)) + [1749],
    'farm frenzy': list(range(1456, 1458)) + [1749],
    'fifa 17': list(range(916, 931)) + [1749],
    'final fantasy vii rebirth': list(range(1855, 1864)) + [1749],
    'finding frankie': list(range(622, 626)) + [1749],
    'five nights at freddys': list(range(948, 950)) + [1749],
    'five nights at freddys secret of the mimic': list(range(1462, 1473)) + [1749],
    'fl studio 25': list(range(1153, 1156)) + [1749],
    'forza motorsport': list(range(1825, 1834)) + [1749],
    'friday night funkin': list(range(748, 750)) + [1749],
    'frostpunk': list(range(1222, 1228)) + [1749],
    'frostpunk 2': list(range(1619, 1627)) + [1749],

    # G
    'garrys mod': list(range(858, 860)) + [1749],
    'ghost of tsushima': list(range(1527, 1551)) + [1749],
    'ghostrunner': list(range(1692, 1701)) + [1749],
    'goat simulator': list(range(618, 621)) + [1749],
    'grand theft auto iii': list(range(1088, 1090)) + [1749],
    'grand theft auto iv': list(range(799, 810)) + [1749],
    'grand theft auto v': list(range(705, 742)) + [1749],
    'grand theft auto san andreas': list(range(1259, 1270)) + [1749],
    'grand theft auto vice city': list(range(1450, 1452)) + [1749],
    'grand theft auto liberty city stories': list(range(1082, 1084)) + [1749],
    'grand theft auto vice city stories': list(range(902, 904)) + [1749],
    'gta 3': list(range(1088, 1090)) + [1749],
    'gta iii': list(range(1088, 1090)) + [1749],
    'gta 4': list(range(799, 810)) + [1749],
    'gta iv': list(range(799, 810)) + [1749],
    'gta 5': list(range(705, 742)) + [1749],
    'gta v': list(range(705, 742)) + [1749],
    'gta san andreas': list(range(1259, 1270)) + [1749],
    'gta vice city': list(range(1450, 1452)) + [1749],
    'gta liberty city stories': list(range(1082, 1084)) + [1749],
    'gta vice city stories': list(range(902, 904)) + [1749],
    'гта 5': list(range(705, 742)) + [1749],

    # H
    'half life 2': list(range(1207, 1211)) + [1749],
    'hard time 3': list(range(1006, 1009)) + [1749],
    'hatred': list(range(1667, 1669)) + [1749],
    'hearts of iron 4': list(range(743, 747)) + [1749],
    'hearts of iron 4: ultimate bundle': list(range(1497, 1501)) + [1749],
    'helldivers 2': list(range(1875, 1884)) + [1749],
    'hitman': list(range(962, 985)) + [1749],
    'hitman blood money': list(range(951, 960)) + [1749],
    'hl2': list(range(1207, 1211)) + [1749],
    'hogwarts legacy': list(range(1720, 1729)) + [1749],
    'hoi4': list(range(743, 747)) + [1749],
    'hoi4 ultimate': list(range(1497, 1501)) + [1749],
    'hollow knight': list(range(1060, 1062)) + [1749],
    'hollow knight: silksong': list(range(1600, 1602)) + [1749],
    'hollow knight silksong': list(range(1600, 1602)) + [1749],
    'homeworld 3': list(range(1895, 1904)) + [1749],
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
    'like a dragon infinite wealth': list(range(1845, 1854)) + [1749],
    'little nightmares 3': list(range(174, 182)) + [1749],
    'little nightmares iii': list(range(174, 182)) + [1749],
    'lonarpg': list(range(1447, 1449)) + [1749],

    # M
    'mafia 1': list(range(1241, 1243)) + [1749],
    'mafia 2': list(range(942, 947)) + [1749],
    'mafia i': list(range(1241, 1243)) + [1749],
    'metro 2033': list(range(1051, 1056)) + [1749],
    'metro last light redux': list(range(1606, 1611)) + [1749],
    'minecraft': list(range(932, 935)) + [1749],
    'modern warfare 2': list(range(1212, 1221)) + [1749],
    'mortal kombat 1': list(range(1835, 1844)) + [1749],
    'my gaming club': list(range(811, 813)) + [1749],
    'my summer car': list(range(1441, 1443)) + [1749],
    'my winter car': list(range(1347, 1349)) + [1749],
    'mysided': list(range(1057, 1059)) + [1749],

    # N
    'nier automata': list(range(164, 173)) + [1749],
    'nier replicant': list(range(1670, 1682)) + [1749],
    'nier: automata': list(range(164, 173)) + [1749],
    'no im not a human': list(range(517, 520)) + [1749],

    # O
    'one shot': list(range(1065, 1069)) + [1749],
    'orion sandbox': list(range(814, 816)) + [1749],

    # P
    'palworld': list(range(202, 216)) + [1749],
    'payday the heist': list(range(876, 879)) + [1749],
    'people playground': list(range(1603, 1605)) + [1749],
    'persona 3 reload': list(range(1700, 1705)) + [1749],  # Новая игра
    'plants vs zombies': list(range(549, 551)) + [1749],
    'portal 2': list(range(1207, 1211)) + [1749],
    'portal knights': list(range(1237, 1239)) + [1749],
    'postal 2': list(range(1615, 1617)) + [1749],
    'prince of persia the lost crown': list(range(1865, 1874)) + [1749],
    'project zomboid': list(range(1093, 1095)) + [1749],
    'prototype 1': list(range(895, 901)) + [1749],
    'prototype 2': list(range(1044, 1050)) + [1749],

    # Q
    'quasimorph': list(range(589, 591)) + [1749],

    # R
    'rdr 1': list(range(542, 548)) + [1749],
    'rdr 2': list(range(428, 485)) + [1749],
    'rdr2': list(range(428, 485)) + [1749],
    'red dead redemption': list(range(542, 548)) + [1749],
    'red dead redemption 2': list(range(428, 485)) + [1749],
    'resident evil 8': list(range(826, 845)) + [1749],
    'resident evil revelations 2': list(range(788, 798)) + [1749],
    'resident evil resistance': list(range(1330, 1346)) + [1749],
    'resident evil village': list(range(826, 845)) + [1749],
    'rimworld': list(range(1298, 1301)) + [1749],
    'risk of rain 2': list(range(1612, 1614)) + [1749],
    'rock star life simulator': list(range(184, 186)) + [1749],

    # S
    's.t.a.l.k.e.r. shadow of chernobyl': list(range(1326, 1329)) + [1749],
    'sally face': list(range(628, 632)) + [1749],
    'scorn': list(range(217, 227)) + [1749],
    'shadow of chernobyl': list(range(1326, 1329)) + [1749],
    'silent hill 2 remake': list(range(1690, 1695)) + [1749],  # Новая игра
    'skull and bones': list(range(1885, 1894)) + [1749],
    'slim rancher': list(range(853, 857)) + [1749],
    'slime rancher 2': list(range(1323, 1325)) + [1749],
    'spider man remastered': list(range(486, 516)) + [1749],
    'spider man': list(range(486, 516)) + [1749],
    'stalker 2': list(range(1628, 1634)) + [1749],
    'stalker anomaly': list(range(1628, 1634)) + [1749],
    'stalker shadow of chernobyl': list(range(1326, 1329)) + [1749],
    'star wars jedi survivor': list(range(1710, 1719)) + [1749],
    'star wars outlaws': list(range(1905, 1914)) + [1749],
    'stray': list(range(936, 941)) + [1749],
    'street fighter 6': list(range(1775, 1784)) + [1749],
    'streets of rogue 2': list(range(1041, 1043)) + [1749],
    'system shock 2 remaster': list(range(187, 192)) + [1749],

    # T
    'teardown': list(range(906, 912)) + [1749],
    'team fortress 2': list(range(1453, 1455)) + [1749],
    'terraria': list(range(1459, 1461)) + [1749],
    'terraria 1.4.4.9': list(range(1350, 1352)) + [1749],
    'the forest': list(range(633, 635)) + [1749],
    'the last of us': list(range(1119, 1152)) + [1749],
    'the legend of zelda tears of the kingdom': list(range(1755, 1764)) + [1749],
    'the long drive': list(range(1444, 1446)) + [1749],
    'the spike': list(range(846, 852)) + [1749],
    'the witcher 3': list(range(986, 1005)) + [1749],
    'third crisis': list(range(1302, 1305)) + [1749],
    'tomb raider 2013': list(range(1487, 1496)) + [1749],
    'tomb raider': list(range(1487, 1496)) + [1749],

    # U
    'uber soldier': list(range(197, 201)) + [1749],
    'undertale': list(range(1376, 1378)) + [1749],

    # W
    'warhammer 40000 gladius relics of war': list(range(1702, 1705)) + [1749],
    'warhammer gladius': list(range(1702, 1705)) + [1749],
    'watch dogs 2': list(range(1010, 1027)) + [1749],
    'watch dogs': list(range(1010, 1027)) + [1749],
    'witcher 3': list(range(986, 1005)) + [1749],
    'witcher': list(range(986, 1005)) + [1749],
    'world box': list(range(1036, 1040)) + [1749],
    'worldbox': list(range(1036, 1040)) + [1749],

    # КИРИЛЛИЦА
    'андертейл': list(range(1376, 1378)) + [1749],
    'аномали': list(range(1628, 1634)) + [1749],
    'ассасин крид': list(range(1028, 1033)) + [1749],
    'бехолдер': list(range(823, 825)) + [1749],
    'биошок': list(range(1070, 1080)) + [1749],
    'блендер': list(range(1306, 1310)) + [1749],
    'бордерлендс 2': list(range(776, 782)) + [1749],
    'булли': list(range(1639, 1642)) + [1749],
    'ведьмак 3': list(range(986, 1005)) + [1749],
    'ведьмак': list(range(986, 1005)) + [1749],
    'гострайнер': list(range(1692, 1701)) + [1749],
    'гта 5': list(range(705, 742)) + [1749],
    'детройт': list(range(1407, 1436)) + [1749],
    'дед спейс': list(range(1576, 1580)) + [1749],
    'дмс 4': list(range(1244, 1258)) + [1749],
    'дум темные века': list(range(1706, 1749)) + [1749],
    'зомбоид': list(range(1093, 1095)) + [1749],
    'капхед': list(range(817, 821)) + [1749],
    'киберпанк 2077': list(range(658, 704)) + [1749],
    'киберпанк': list(range(658, 704)) + [1749],
    'кот': list(range(936, 941)) + [1749],
    'корсары 3': list(range(1370, 1372)) + [1749],
    'лара крофт': list(range(1487, 1496)) + [1749],
    'майнкрафт': list(range(932, 935)) + [1749],
    'мафия 1': list(range(1241, 1243)) + [1749],
    'мафия 2': list(range(942, 947)) + [1749],
    'метро 2033': list(range(1051, 1056)) + [1749],
    'метро last light': list(range(1606, 1611)) + [1749],
    'мой летний авто': list(range(1441, 1443)) + [1749],
    'мой зимний авто': list(range(1347, 1349)) + [1749],
    'ниер репликант': list(range(1670, 1682)) + [1749],
    'ниер': list(range(164, 173)) + [1749],
    'палворлд': list(range(202, 216)) + [1749],
    'пейдэй': list(range(876, 879)) + [1749],
    'призрак цусимы': list(range(1527, 1551)) + [1749],
    'прототип 2': list(range(1044, 1050)) + [1749],
    'прототип': list(range(895, 901)) + [1749],
    'растения против зомби': list(range(549, 551)) + [1749],
    'римворлд': list(range(1298, 1301)) + [1749],
    'симулятор козла': list(range(618, 621)) + [1749],
    'сталкер 2': list(range(1628, 1634)) + [1749],
    'сталкер аномали': list(range(1628, 1634)) + [1749],
    'сталкер': list(range(1326, 1329)) + [1749],
    'строительный симулятор 4': list(range(1373, 1375)) + [1749],
    'тень чернобыля': list(range(1326, 1329)) + [1749],
    'террария': list(range(1459, 1461)) + [1749],
    'фнаф': list(range(948, 950)) + [1749],
    'фоллаут 3': list(range(1231, 1236)) + [1749],
    'фоллаут 4': list(range(1277, 1296)) + [1749],
    'ферма': list(range(1456, 1458)) + [1749],
    'фифа 17': list(range(916, 931)) + [1749],
    'хаф лайф 2': list(range(1207, 1211)) + [1749],
    'хитман': list(range(962, 985)) + [1749],
    'холлоу найт': list(range(1060, 1062)) + [1749],
    'хотлайн майами 2': [1159, 1160] + [1749],
    'хотлайн майами': list(range(1085, 1087)) + [1749],
    'человек паук': list(range(486, 516)) + [1749],
    'элден ринг': list(range(552, 587)) + [1749],

}


print(f"✅ Загружено игр: {len(GAMES_DATABASE)}")


# ========== ЗАГРУЗКА ДАННЫХ ==========
def load_data():
    """Загружает все данные из файлов"""
    global orders, user_stats, admins, game_stats

    # Заказы
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders.extend(json.load(f))

    # Статистика пользователей
    if os.path.exists(USER_STATS_FILE):
        with open(USER_STATS_FILE, 'r', encoding='utf-8') as f:
            user_stats.update(json.load(f))

    # Админы
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            admins.clear()
            admins.extend(json.load(f))


def save_data():
    """Сохраняет все данные в файлы"""
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    with open(USER_STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_stats, f, ensure_ascii=False, indent=2)

    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins, f, ensure_ascii=False, indent=2)


# ========== ФУНКЦИЯ ОТПРАВКИ ИГР ==========
def send_game_files(chat_id, game_name, user_id=None):
    """Отправляет файлы игры и прикрепляет баннер к последнему"""
    if game_name not in GAMES_DATABASE:
        return False

    file_ids = GAMES_DATABASE[game_name]
    total_files = len(file_ids)
    sent_count = 0

    bot.send_message(chat_id, f"🎮 *{game_name.upper()}*\n📥 Отправляю...", parse_mode='Markdown')

    for i, file_id in enumerate(file_ids):
        try:
            if i == total_files - 1:
                bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=GAMES_CHANNEL_ID,
                    message_id=file_id,
                    caption=GAME_BANNER.strip(),
                    parse_mode='Markdown'
                )
            else:
                bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=GAMES_CHANNEL_ID,
                    message_id=file_id
                )
            sent_count += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"Ошибка отправки {file_id}: {e}")

    if user_id:
        uid = str(user_id)
        if uid not in user_stats:
            user_stats[uid] = {'downloads': 0, 'created_orders': 0}
        user_stats[uid]['downloads'] = user_stats[uid].get('downloads', 0) + 1
        save_data()

    bot.send_message(chat_id, f"✅ *Готово!* Отправлено {sent_count} файлов")
    return True


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
            'first_seen': datetime.now().isoformat()
        }
        save_data()

    text = """🎮 *Ferwes Games Bot*

🔍 *Напиши название игры* — я пришлю, если есть.

📋 `/orders` — стол заказов  
📝 `/neworder` — новый заказ  
👤 `/myorders` — мои заказы  
📊 `/stats` — моя статистика  
🔥 `/top` — топ игр  
👑 `/moderator` — админ-панель  
ℹ️ `/help` — помощь"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📝 Новый заказ", callback_data="new_order"),
        types.InlineKeyboardButton("👤 Мои заказы", callback_data="my_orders"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="my_stats"),
        types.InlineKeyboardButton("🔥 Топ игр", callback_data="show_top"),
        types.InlineKeyboardButton("👑 Админка", callback_data="show_mod")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА HELP ==========
@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.chat.type != 'private':
        return

    text = """ℹ️ *Справка по командам*

📋 *Заказы:*
/orders — стол заказов
/neworder — создать заказ
/myorders — мои заказы

🎮 *Игры:*
/stats — моя статистика
/top — топ игр

👑 *Админ-команды:*
/moderator — панель модератора
/delorder [ID] — удалить заказ
/broadcast [текст] — рассылка
/addadmin [ID] — добавить админа"""

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА MODERATOR ==========
@bot.message_handler(commands=['moderator'])
def moderator_cmd(message):
    if str(message.from_user.id) not in admins or message.chat.type != 'private':
        return

    # Статистика
    total_orders = len(orders)
    active_orders = sum(1 for o in orders if o.get('status', 'active') == 'active')

    text = f"""👑 *ПАНЕЛЬ МОДЕРАТОРА*

📊 *СТАТИСТИКА*
• Всего заказов: {total_orders}
• Активных: {active_orders}
• Пользователей: {len(user_stats)}
• Админов: {len(admins)}

━━━━━━━━━━━━━━━━━━
⚡ *КОМАНДЫ*

/delorder [ID] — удалить заказ
/broadcast [текст] — рассылка
/addadmin [ID] — добавить админа
"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 Заказы", callback_data="show_orders"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="mod_stats"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_mod")
    )

    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА DELORDER ==========
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


# ========== КОМАНДА ADDADMIN ==========
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


# ========== КОМАНДА BROADCAST ==========
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
                bot.send_message(int(uid), f"📢 *Объявление*\n\n{broadcast_text}", parse_mode='Markdown')
                sent += 1
                time.sleep(0.1)
            except:
                failed += 1

        bot.reply_to(message, f"✅ Рассылка завершена\n📤 Отправлено: {sent}\n❌ Не отправлено: {failed}")
    except:
        bot.reply_to(message, "❌ Использование: /broadcast [текст]")


# ========== КОМАНДА ORDERS ==========
@bot.message_handler(commands=['orders'])
def orders_cmd(message):
    if message.chat.type != 'private':
        return

    show_orders_page(message.chat.id, 0, message)


def show_orders_page(chat_id, page=0, original_message=None):
    if not orders:
        bot.send_message(chat_id, "📭 *Нет заказов*")
        return

    # Сортируем по дате (новые сверху)
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

    text = f"📋 *Стол заказов* (Страница {page + 1}/{total_pages})\n\n"

    for order in page_orders:
        try:
            order_date = datetime.fromisoformat(order['date']).strftime("%d.%m.%Y")
        except:
            order_date = "неизвестно"

        text += f"🎮 *{order['game']}*\n"
        text += f"👤 {order.get('username', 'Пользователь')}\n"
        text += f"📅 {order_date} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} лайков\n"
        text += f"🆔 {order['id']}\n"
        text += "─\n"

    markup = types.InlineKeyboardMarkup(row_width=3)

    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️", callback_data=f"orders_page_{page - 1}"))
    nav_buttons.append(types.InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="current"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("➡️", callback_data=f"orders_page_{page + 1}"))
    markup.row(*nav_buttons)

    # Кнопки для заказов
    for order in page_orders:
        btn_text = f"❤️ {order['game'][:12]}"
        markup.add(
            types.InlineKeyboardButton(btn_text, callback_data=f"like_{order['id']}"),
            types.InlineKeyboardButton("📤", callback_data=f"share_{order['id']}")
        )

    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)


# ========== КОМАНДА NEWORDER ==========
@bot.message_handler(commands=['neworder'])
def neworder_cmd(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = 'waiting_game'
    bot.send_message(message.chat.id, "📝 *Напиши название игры:*", parse_mode='Markdown')


@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == 'waiting_game')
def get_game(message):
    if message.chat.type != 'private':
        return

    user_states[message.chat.id] = {'game': message.text, 'state': 'waiting_size'}
    bot.send_message(message.chat.id, "💾 *Напиши размер в ГБ:*", parse_mode='Markdown')


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

    save_data()
    del user_states[message.chat.id]
    bot.send_message(message.chat.id, f"✅ *Заказ создан!*\n🆔 ID: {order_id}", parse_mode='Markdown')


# ========== КОМАНДА MYORDERS ==========
@bot.message_handler(commands=['myorders'])
def myorders_cmd(message):
    if message.chat.type != 'private':
        return

    user_orders = [o for o in orders if o.get('user_id') == message.chat.id]
    if not user_orders:
        bot.send_message(message.chat.id, "📭 *У вас нет заказов*")
        return

    text = "👤 *Мои заказы*\n\n"
    for order in user_orders[-10:]:
        text += f"🎮 {order['game']}\n"
        text += f"🆔 {order['id']} | 💾 {order.get('size', 'N/A')}\n"
        text += f"❤️ {order.get('likes', 0)} лайков\n"
        text += "─\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА STATS ==========
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.chat.type != 'private':
        return

    user_id_str = str(message.from_user.id)
    if user_id_str not in user_stats:
        bot.send_message(message.chat.id, "📊 *Вы еще ничего не скачали*")
        return

    stats = user_stats[user_id_str]
    downloads = stats.get('downloads', 0)
    created_orders = stats.get('created_orders', 0)

    # Заказы пользователя
    user_orders = [o for o in orders if o.get('user_id') == message.chat.id]
    total_likes = sum(o.get('likes', 0) for o in user_orders)

    text = f"👤 *Ваша статистика*\n\n"
    text += f"📥 Скачано игр: {downloads}\n"
    text += f"📋 Создано заказов: {created_orders}\n"
    text += f"❤️ Получено лайков: {total_likes}\n"

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ========== КОМАНДА TOP ==========
@bot.message_handler(commands=['top'])
def top_cmd(message):
    if message.chat.type != 'private':
        return

    # Сортируем игры по скачиваниям (если есть статистика)
    if game_stats:
        sorted_games = sorted(game_stats.items(), key=lambda x: x[1]['downloads'], reverse=True)[:10]

        text = "🔥 *Топ игр по скачиваниям*\n\n"
        for i, (game, stats) in enumerate(sorted_games, 1):
            text += f"{i}. 🎮 {game} — {stats['downloads']} 📥\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "📊 *Нет данных для топа*")


# ========== ОБРАБОТЧИК ПОИСКА ИГР ==========
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def search_handler(message):
    if message.chat.type != 'private':
        return

    query = message.text.strip().lower()

    if query in GAMES_DATABASE:
        send_game_files(message.chat.id, query, message.from_user.id)
        return

    # Поиск похожих
    similar = []
    for game in GAMES_DATABASE.keys():
        if query in game or game in query:
            similar.append(game)

    if similar:
        text = f"❌ *'{message.text}' не найдено*\n\n"
        text += "🎯 *Возможно вы искали:*\n\n"

        markup = types.InlineKeyboardMarkup(row_width=1)
        for game in similar[:5]:
            markup.add(types.InlineKeyboardButton(
                f"🎮 {game.title()}",
                callback_data=f"play_{game}"
            ))

        text += "Нажмите на кнопку, чтобы скачать:"
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
    else:
        text = f"❌ *'{message.text}' не найдено*\n\n"
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
                    bot.answer_callback_query(call.id, "❌ Уже лайкали")
                    return
                order['likes'] = order.get('likes', 0) + 1
                order['liked_by'].append(str(call.from_user.id))
                save_data()
                bot.answer_callback_query(call.id, "❤️ Лайк поставлен!")
                return

    elif call.data.startswith('share_'):
        order_id = int(call.data.split('_')[1])
        for order in orders:
            if order['id'] == order_id:
                share_text = f"📤 *Заказ #{order_id}*\n🎮 {order['game']}\n💾 {order.get('size', 'N/A')}"
                bot.send_message(call.message.chat.id, share_text, parse_mode='Markdown')
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
    elif call.data == "show_mod":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        moderator_cmd(call.message)
    elif call.data == "mod_stats":
        text = f"📊 *Статистика*\n\nЗаказов: {len(orders)}\nПользователей: {len(user_stats)}"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    elif call.data == "refresh_mod":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        moderator_cmd(call.message)
    elif call.data == "current":
        bot.answer_callback_query(call.id)


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 ЗАПУСК FERWES GAMES БОТА")
    print("=" * 60)

    # Создаём файлы
    files_to_create = [ORDERS_FILE, USER_STATS_FILE, ADMINS_FILE]
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

    # Запуск
    try:
        bot.polling(none_stop=True, skip_pending=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(5)