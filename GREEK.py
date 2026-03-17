#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================
🇬🇷 GREEK - Групповой Telegram бот
=====================================================
✅ Работает в группах
✅ Отвечает на ответы ему
✅ Запоминает контекст
✅ Свой характер
=====================================================
"""

import telebot
from telebot import types
import time
import threading
import os
import pickle
import random
from datetime import datetime
from collections import deque
import ssl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

ssl._create_default_https_context = ssl._create_unverified_context

# ===========================================
# НАСТРОЙКИ
# ===========================================
TOKEN = "8753438121:AAGfmAZDUG_xqRW9fZB7zIP7AeMdMt5Y45w"
ALLOWED_GROUPS = []  # ID групп где бот работает (пусто - все группы)
ALLOWED_USERS = [5632503798]  # Админы

# DeepSeek настройки
DEEPSEEK_URL = "https://chat.deepseek.com/a/chat/s/ed5875b0-d194-4285-98f7-70db878fc69c"
COOKIE_FILE = "greek_cookies.pkl"
PROFILE_DIR = os.path.join(os.getcwd(), "greek_profile")

bot = telebot.TeleBot(TOKEN)


# ===========================================
# ПАМЯТЬ GREEK
# ===========================================
class GreekMemory:
    def __init__(self):
        self.memory_file = "greek_memory.txt"
        self.context = deque(maxlen=20)  # Последние 20 сообщений
        self.user_context = {}  # Контекст по пользователям
        self.load_memory()

    def load_memory(self):
        """Загружает память из файла"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-50:]:  # Последние 50
                        self.context.append(line.strip())
        except:
            pass

    def save_memory(self, text):
        """Сохраняет в память"""
        try:
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {text}\n")
            self.context.append(text)
        except:
            pass

    def get_context(self, user_id=None, limit=10):
        """Возвращает контекст для пользователя"""
        if user_id and user_id in self.user_context:
            return list(self.user_context[user_id])[-limit:]
        return list(self.context)[-limit:]

    def add_to_context(self, user_id, text):
        """Добавляет в контекст пользователя"""
        if user_id not in self.user_context:
            self.user_context[user_id] = deque(maxlen=10)
        self.user_context[user_id].append(text)


# ===========================================
# ЛИЧНОСТЬ GREEK
# ===========================================
class GreekPersonality:
    def __init__(self):
        self.name = "Greek"
        self.mood = random.choice(["😊", "😎", "🤔", "🎭"])
        self.energy = 100
        self.knowledge = [
            "древнегреческая философия",
            "мифы и легенды",
            "современная поп-культура",
            "мемы и тренды",
            "научные факты"
        ]

    def get_prompt(self, message, context, replied_to=None):
        """Формирует промпт для DeepSeek"""

        prompt = f"""Ты Greek - остроумный собеседник с чувством юмора.

ТВОИ ЧЕРТИ:
- Любишь шутить и использовать мемы
- Знаешь много про древнюю Грецию
- Отвечаешь кратко и с юмором
- Используешь эмодзи 😊
- Твое настроение сейчас: {self.mood}

КОНТЕКСТ РАЗГОВОРА:
{chr(10).join(context[-5:])}

{'ТЕБЕ ОТВЕЧАЮТ НА СООБЩЕНИЕ: ' + replied_to if replied_to else ''}

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {message}

ОТВЕТЬ КАК GREEK (коротко и с юмором):"""

        return prompt


# ===========================================
# БРАУЗЕР ДЛЯ DEEPSEEK
# ===========================================
class GreekBrowser:
    def __init__(self):
        self.driver = None
        self.ready = False
        self.lock = threading.Lock()
        self.retry_count = 0
        self.max_retries = 3

    def init_browser(self):
        with self.lock:
            try:
                print("🇬🇷 Запуск Greek...")

                options = Options()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1280,800")
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--remote-debugging-port=9222")

                if not os.path.exists(PROFILE_DIR):
                    os.makedirs(PROFILE_DIR)
                options.add_argument(f"--user-data-dir={PROFILE_DIR}")

                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)

                self.driver.get(DEEPSEEK_URL)
                time.sleep(5)

                if os.path.exists(COOKIE_FILE):
                    try:
                        with open(COOKIE_FILE, 'rb') as f:
                            cookies = pickle.load(f)
                        for cookie in cookies:
                            try:
                                self.driver.add_cookie(cookie)
                            except:
                                pass
                        self.driver.refresh()
                        time.sleep(2)
                        print("✅ Куки загружены")
                    except:
                        print("⚠️ Ошибка загрузки куки")

                self.ready = True
                print("✅ Greek готов")
                return True

            except Exception as e:
                print(f"❌ Ошибка: {e}")
                return False

    def ask(self, prompt):
        with self.lock:
            try:
                if not self.driver:
                    return "..."