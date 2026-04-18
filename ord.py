import sqlite3
import os

DB_FILE = 'bot_database.db'

if not os.path.exists(DB_FILE):
    print(f"❌ Файл {DB_FILE} не найден!")
    exit()

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Проверяем количество заказов
cursor.execute("SELECT COUNT(*) FROM orders")
count = cursor.fetchone()[0]
print(f"📋 Всего заказов в базе: {count}")

if count > 0:
    print("\n📋 ПОСЛЕДНИЕ ЗАКАЗЫ:\n")
    cursor.execute("""
        SELECT order_id, game_name, size, likes, status, created_date, anonymous 
        FROM orders 
        ORDER BY created_date DESC 
        LIMIT 10
    """)

    for order in cursor.fetchall():
        order_id, game_name, size, likes, status, created_date, anonymous = order
        anon = "👻" if anonymous else "👤"
        print(f"#{order_id} | {anon} | {game_name} | {size} | ❤️ {likes} | {status} | {created_date[:10]}")
else:
    print("\n📭 База пуста. Заказов нет.")

conn.close()