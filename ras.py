#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 БОТ РАСПИСАНИЯ ГРУППЫ ОС-301
"""

import requests
import time
import sys
import json
import re
import os
from datetime import datetime, timedelta
import telebot
from telebot import types
import threading

import logging
logging.getLogger('telebot').setLevel(logging.CRITICAL)


class Config:
    GROUP_NAME = "ОС-301"
    OWNER_ID = 1488923831
    
    # 📚 Сокращённые названия предметов
    SUBJECT_SHORTCUTS = {
        "Осуществление анализа решений для выбора программного обеспечения в целях разработки и тестирования модели элементов систем автоматизации на основе технического задания": "Выбор ПО",
        "Разработка, организация и контроль качества работ по монтажу, наладке и техническому обслуживанию систем и средств автоматизации": "Монтаж",
        "Тестирование разработанной модели элементов систем автоматизации с формированием пакета технической документации": "Тестирование",
        "Планирование материально-технического обеспечения работ по монтажу, наладке и техническому обслуживанию систем и средств автоматизации": "Планирование",
        "Осуществление выбора оборудования, элементной базы, монтажа и наладки модели элементов систем автоматизации на основе разработанной технической документации": "Выбор оборудования",
        "САПР технологических процессов и информационные технологии в профессиональной деятельности": "САПР",
        "Программирование ЧПУ для автоматизированного оборудования": "ЧПУ",
        "Основы проектирования технологической оснастки": "Проектирование оснастки",
        "Английский язык в профессиональной деятельности": "Английский язык",
        "Экономика организации": "Экономика",
        "Охрана труда": "Охрана труда",
    }
    
    WEEKDAYS = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье"
    }
    
    BASE_URL = "https://poo.edu-74.ru"
    STUDENT_ID = "8506"
    SCHEDULE_PAGE = "/services/students/{student_id}/lessons/{start_date}/{end_date}"
    
    COOKIES = {
        "_ym_uid": "1772043215400769936",
        "_ym_d": "1772043215",
        "_ym_isad": "2",
        ".AspNetCore.Session": "CfDJ8F1SoIh0xwxApynwZKLIqRq5wYt0mjM76fG3koFXuAE8ZAy5MW3Tt9lkplb5O%2BetCFj8BQUPj74fo%2BAzk%2FnRSGq7iJXemyvWxkVLCUteWI2PL2%2FkjOwL5tK%2FZRDIlSvfCvpbmnUyQZw6pxonHf21SSGRO%2B43QXfIsLNGMNSSxQKU",
        ".AspNetCore.Culture": "c%3Dru%7Cuic%3Dru",
        "UID": "CfDJ8F1SoIh0xwxApynwZKLIqRp7CeqzhgYpcEOFJzjcCb0bsXdHcyYRS%2BO0T6FPqEG1NzOOqP8CV6EmvQpU41HnzkFsU1FDcdPM9KeDP5872gOAl%2BSjhkRCP3vZUp9r2IG%2FvdPnfXYjr2bx%2FaUphaYSx%2Fc%3D",
        ".AspNetCore.Cookies": "CfDJ8F1SoIh0xwxApynwZKLIqRqk_u5Aojx9Cey3Z0BN_syzXZzlfjdhyRCg2nksK1Bri9Sy0VerW6CK436GEneVo4caQIM0R_6Y3b8KvBnKB72UrSESfVMnYJ3j9tM0eytxqnxBofvSEPnzbmEean-Etj1zXZqxm-adg_D0wV68f1roKvBWJ8uKcK9Q7F72IbZG42mu4ISy9SL42V9kaaw9-rWKtgMVwvCoziUH8gIprNWbYlbwb21X0qJjeFb-x3sm9W4UxKlKNKp6OqKCXAUl1kUuppLL9hnctctWKsg9fZvpNmbVg2yljEGQC8fHbuta_s2u3ltRbdS56SEH8gMpNju6Iy8bCj_mLSyet4-mtJJ63dFN8HooBkeeCElCsZ8Smw"
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Referer": "https://poo.edu-74.ru/services/students/8506/lessons",
        "Connection": "keep-alive"
    }
    
    TELEGRAM_BOT_TOKEN = "8402362799:AAFfihskVF0MyDfkZhNq4EJrnj8DJYnr5LA"
    AUTO_CHECK_INTERVAL = 1200
    CHECK_DAYS_AHEAD = 7
    TELEGRAM_TIMEOUT = 60
    CACHE_FILE = "schedule_cache.json"
    USERS_FILE = "users.json"
    LOG_FILE = "bot_log.txt"


def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📅 Сегодня", callback_data="today"),
        types.InlineKeyboardButton("📅 Завтра", callback_data="tomorrow")
    )
    markup.add(
        types.InlineKeyboardButton("📆 Текущая неделя", callback_data="current_week"),
        types.InlineKeyboardButton("📆 Следующая неделя", callback_data="next_week")
    )
    markup.add(types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"))
    return markup


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] [{level}] {message}"
    print(full_message)
    try:
        with open(Config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_message + "\n")
    except:
        pass


def shorten_subject_name(name):
    """Сокращает длинные названия предметов"""
    if not name:
        return "Предмет не указан"
    
    # Очищаем название
    name = name.replace("\\n", " ").replace("\n", " ").strip()
    
    # Ищем точное совпадение
    if name in Config.SUBJECT_SHORTCUTS:
        return Config.SUBJECT_SHORTCUTS[name]
    
    # Ищем частичное совпадение (если название содержит ключевую фразу)
    for full_name, short_name in Config.SUBJECT_SHORTCUTS.items():
        if full_name in name or name in full_name:
            return short_name
    
    # Если не нашли сокращение — возвращаем как есть (обрезаем если слишком длинное)
    if len(name) > 50:
        return name[:47] + "..."
    return name


class ScheduleAPI:
    def __init__(self):
        self.session = requests.Session()
        for key, value in Config.HEADERS.items():
            self.session.headers[key] = value
        self.session.cookies.update(Config.COOKIES)
        log("✅ ScheduleAPI создан")
    
    def get_schedule_data(self, start_date, end_date):
        url = Config.BASE_URL + Config.SCHEDULE_PAGE.format(
            student_id=Config.STUDENT_ID,
            start_date=start_date,
            end_date=end_date
        )
        try:
            log(f"📡 Запрос: {start_date} -> {end_date}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            content = response.text
            data = self._extract_json(content)
            if data:
                log(f"✅ Получено {len(data)} дней")
                return data
            else:
                log("⚠️ JSON не найден", "WARNING")
                return None
        except Exception as e:
            log(f"❌ Ошибка: {e}", "ERROR")
            return None
    
    def _extract_json(self, content):
        if content.strip().startswith('['):
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
            except:
                pass
        json_pattern = r'\[\s*\{[^{}]*"date"[^{}]*\}(?:\s*,\s*\{[^{}]*\})*\s*\]'
        matches = re.findall(json_pattern, content, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list) and len(data) > 0 and "date" in data[0]:
                    return data
            except:
                continue
        return None
    
    def get_day_schedule(self, date_str):
        data = self.get_schedule_data(date_str, date_str)
        if data:
            for day in data:
                day_date = day.get("date", "")
                if "T" in day_date:
                    day_date = day_date.split("T")[0]
                if day_date == date_str:
                    return day
        return None
    
    def get_current_week_schedule(self):
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        monday_str = monday.strftime("%Y-%m-%d")
        sunday_str = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        return self.get_schedule_data(monday_str, sunday_str)
    
    def get_next_week_schedule(self):
        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        monday_str = next_monday.strftime("%Y-%m-%d")
        sunday_str = (next_monday + timedelta(days=6)).strftime("%Y-%m-%d")
        return self.get_schedule_data(monday_str, sunday_str)
    
    def get_week_schedule(self, start_date):
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
        return self.get_schedule_data(start_date, end_date)


def format_lesson(lesson, number):
    start = lesson.get("startTime", "??:??")
    end = lesson.get("endTime", "??:??")
    name = lesson.get("name", "Предмет не указан")
    
    # 📚 Применяем сокращение названия
    name = shorten_subject_name(name)
    
    result = f"{number}. *{start} - {end}*: {name}"
    
    timetable = lesson.get("timetable", {})
    if timetable:
        classroom = timetable.get("classroom", {})
        if classroom:
            room = classroom.get("name", "")
            if room:
                result += f"\n   🏫 Каб. {room}"
        teacher = timetable.get("teacher", {})
        if teacher:
            last = teacher.get("lastName", "")
            first = teacher.get("firstName", "")
            middle = teacher.get("middleName", "")
            if last and first:
                result += f"\n   👨‍🏫 {last} {first} {middle}"
    
    gradebook = lesson.get("gradebook", {})
    if gradebook:
        tasks = gradebook.get("tasks", [])
        homework = [t for t in tasks if t.get("type") == "Home"]
        if homework:
            dz = homework[0].get("topic", "Нет")
            if dz:
                result += f"\n   📝 *ДЗ:* {dz}"
    
    return result


def get_weekday_russian(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday_en = date_obj.strftime("%A")
        return Config.WEEKDAYS.get(weekday_en, weekday_en)
    except:
        return ""


def format_day_schedule(day_data):
    if not day_data:
        return "❌ Данные не найдены"
    date_str = day_data.get("date", "")
    if "T" in date_str:
        date_str = date_str.split("T")[0]
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = date_obj.strftime("%d.%m.%Y")
        weekday = get_weekday_russian(date_str)
    except:
        date_formatted = date_str
        weekday = ""
    lines = []
    lines.append(f"🗓️ *Расписание на {date_formatted} ({weekday})*")
    if day_data.get("isHoliday"):
        lines.append("\n☕ Выходной нах")
        return "\n".join(lines)
    lessons = day_data.get("lessons", [])
    if not lessons:
        lines.append("\nВыходной нах")
        return "\n".join(lines)
    lines.append(f"\n📚 *Всего пар: {len(lessons)}*\n")
    for i, lesson in enumerate(lessons, 1):
        lines.append(format_lesson(lesson, i))
        lines.append("")
    total_min = 0
    for lesson in lessons:
        try:
            s = lesson.get("startTime", "00:00")
            e = lesson.get("endTime", "00:00")
            sh, sm = map(int, s.split(":"))
            eh, em = map(int, e.split(":"))
            total_min += (eh * 60 + em) - (sh * 60 + sm)
        except:
            pass
    hours = total_min // 60
    mins = total_min % 60
    lines.append(f"⏱️ *Общее время:* {hours}ч {mins}мин")
    return "\n".join(lines)


def format_week_schedule(week_data, week_name="неделю"):
    if not week_data:
        return "❌ Данные не найдены"
    lines = []
    lines.append(f"📅 *Расписание на {week_name}*\n")
    for day in week_data:
        date_str = day.get("date", "")
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%d.%m.%Y")
            weekday = get_weekday_russian(date_str)
        except:
            date_formatted = date_str
            weekday = ""
        lessons = day.get("lessons", [])
        is_holiday = day.get("isHoliday", False)
        if is_holiday:
            lines.append(f"🏖️ *{date_formatted} ({weekday})* — Выходной нах\n")
        elif lessons:
            lines.append(f"📚 *{date_formatted} ({weekday})* ({len(lessons)} пар)")
            for i, lesson in enumerate(lessons, 1):
                start = lesson.get("startTime", "??:??")
                end = lesson.get("endTime", "??:??")
                name = shorten_subject_name(lesson.get("name", "???"))
                lines.append(f"  {i}. {start}-{end} {name}")
            lines.append("")
        else:
            lines.append(f"📋 *{date_formatted} ({weekday})* — Выходной нах\n")
    return "\n".join(lines)


class CacheManager:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"⚠️ Ошибка сохранения кэша: {e}", "WARNING")
    
    def get(self, date_str):
        return self.data.get(date_str)
    
    def set(self, date_str, schedule_hash):
        self.data[date_str] = {"hash": schedule_hash, "updated": datetime.now().isoformat()}
        self._save()
    
    def has_changed(self, date_str, new_hash):
        cached = self.get(date_str)
        if not cached:
            return True
        return cached.get("hash") != new_hash


def get_schedule_hash(day_data):
    if not day_data:
        return "empty"
    lessons = day_data.get("lessons", [])
    hash_parts = []
    for lesson in lessons:
        part = f"{lesson.get('startTime')}-{lesson.get('endTime')}-{lesson.get('name', '')}"
        hash_parts.append(part)
    return "|".join(hash_parts)


class UserManager:
    def __init__(self, users_file):
        self.users_file = users_file
        self.users = self._load()
    
    def _load(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save(self):
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_user(self, chat_id):
        chat_id = str(chat_id)
        if chat_id not in self.users:
            self.users[chat_id] = {"added": datetime.now().isoformat(), "last_seen": datetime.now().isoformat()}
            self._save()
            log(f"✅ Новый пользователь: {chat_id}")
            return True
        return False
    
    def update_user(self, chat_id):
        chat_id = str(chat_id)
        if chat_id in self.users:
            self.users[chat_id]["last_seen"] = datetime.now().isoformat()
            self._save()
        else:
            self.add_user(chat_id)
    
    def get_all_users(self):
        return list(self.users.keys())
    
    def get_users_count(self):
        return len(self.users)


class ScheduleBot:
    def __init__(self):
        self.bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)
        self.api = ScheduleAPI()
        self.cache = CacheManager(Config.CACHE_FILE)
        self.users = UserManager(Config.USERS_FILE)
        self.auto_check_enabled = True
        self._setup_commands()
        log("✅ Telegram бот создан")
        log(f"👥 Всего пользователей: {self.users.get_users_count()}")
    
    def _setup_commands(self):
        @self.bot.message_handler(commands=['start'])
        def cmd_start(message):
            is_new = self.users.add_user(message.chat.id)
            if is_new:
                help_text = f"╔══════════════════════════════════════╗\n     🎓 РАСПИСАНИЕ ГРУППЫ {Config.GROUP_NAME}\n╚══════════════════════════════════════╝\n\nВыберите нужный пункт в меню 👇"
            else:
                help_text = f"👋 С возвращением!\n\n╔══════════════════════════════════════╗\n     🎓 РАСПИСАНИЕ ГРУППЫ {Config.GROUP_NAME}\n╚══════════════════════════════════════╝\n\nВыберите нужный пункт в меню 👇"
            self.bot.send_message(message.chat.id, help_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        
        @self.bot.message_handler(commands=['help'])
        def cmd_help(message):
            self.users.update_user(message.chat.id)
            help_text = f"╔══════════════════════════════════════╗\n     🎓 РАСПИСАНИЕ ГРУППЫ {Config.GROUP_NAME}\n╚══════════════════════════════════════╝\n\n*📌 Доступные команды:*\n\n📅 */today* — расписание на сегодня\n📅 */tomorrow* — расписание на завтра\n📅 */week* — расписание на неделю\n📅 */date YYYY-MM-DD* — на конкретную дату\n\n⚙️ */status* — статус бота\n🔔 */on* — включить уведомления\n🔕 */off* — отключить уведомления"
            self.bot.reply_to(message, help_text, parse_mode="Markdown")
        
        @self.bot.message_handler(commands=['broadcast'])
        def cmd_broadcast(message):
            if str(message.chat.id) != str(Config.OWNER_ID):
                return
            text = message.text.replace("/broadcast", "").strip()
            if not text:
                self.bot.reply_to(message, "📝 Использование: /broadcast Ваш текст")
                return
            users = self.users.get_all_users()
            sent = 0
            failed = 0
            for chat_id in users:
                try:
                    self.bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=True)
                    sent += 1
                    time.sleep(0.5)
                except Exception as e:
                    failed += 1
                    log(f"❌ Не отправлено {chat_id}: {e}", "ERROR")
            report = f"✅ Рассылка: {sent} доставлено, {failed} ошибок\n👥 Всего пользователей: {len(users)}"
            self.bot.send_message(message.chat.id, report)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            if call.data == "today":
                self.users.update_user(call.message.chat.id)
                today = datetime.now().strftime("%Y-%m-%d")
                day_data = self.api.get_day_schedule(today)
                text = format_day_schedule(day_data)
                self.bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
            elif call.data == "tomorrow":
                self.users.update_user(call.message.chat.id)
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                day_data = self.api.get_day_schedule(tomorrow)
                text = format_day_schedule(day_data)
                self.bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
            elif call.data == "current_week":
                self.users.update_user(call.message.chat.id)
                week_data = self.api.get_current_week_schedule()
                text = format_week_schedule(week_data, "текущую неделю (с понедельника)")
                self.bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
            elif call.data == "next_week":
                self.users.update_user(call.message.chat.id)
                week_data = self.api.get_next_week_schedule()
                text = format_week_schedule(week_data, "следующую неделю (с понедельника)")
                self.bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
            elif call.data == "settings":
                self.users.update_user(call.message.chat.id)
                settings_text = f"⚙️ *НАСТРОЙКИ БОТА*\n\n🤖 *Статус:*\n• Автопроверка: каждые 20 мин\n• Сегодня: {datetime.now().strftime('%d.%m.%Y')}\n• Пользователей: {self.users.get_users_count()}\n\n🔔 *Уведомления:*\n{'✅ Включены' if self.auto_check_enabled else '❌ Выключены'}"
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(types.InlineKeyboardButton("🔔 Включить", callback_data="notify_on"), types.InlineKeyboardButton("🔕 Выключить", callback_data="notify_off"))
                markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
                self.bot.edit_message_text(settings_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)
            elif call.data == "notify_on":
                self.auto_check_enabled = True
                self.bot.answer_callback_query(call.id, "✅ Уведомления включены!")
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="⚙️ *НАСТРОЙКИ*\n\n🔔 Уведомления: *ВКЛЮЧЕНЫ*", parse_mode="Markdown", reply_markup=get_main_keyboard())
            elif call.data == "notify_off":
                self.auto_check_enabled = False
                self.bot.answer_callback_query(call.id, "❌ Уведомления выключены!")
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="⚙️ *НАСТРОЙКИ*\n\n🔕 Уведомления: *ВЫКЛЮЧЕНЫ*", parse_mode="Markdown", reply_markup=get_main_keyboard())
            elif call.data == "back_main":
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"╔══════════════════════════════════════╗\n     🎓 РАСПИСАНИЕ ГРУППЫ {Config.GROUP_NAME}\n╚══════════════════════════════════════╝\n\nВыберите нужный пункт в меню 👇", parse_mode="Markdown", reply_markup=get_main_keyboard())
        @self.bot.message_handler(commands=['today'])
        def cmd_today(message):
            self.users.update_user(message.chat.id)
            today = datetime.now().strftime("%Y-%m-%d")
            day_data = self.api.get_day_schedule(today)
            text = format_day_schedule(day_data)
            self.bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        
        @self.bot.message_handler(commands=['tomorrow'])
        def cmd_tomorrow(message):
            self.users.update_user(message.chat.id)
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_data = self.api.get_day_schedule(tomorrow)
            text = format_day_schedule(day_data)
            self.bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        
        @self.bot.message_handler(commands=['week'])
        def cmd_week(message):
            self.users.update_user(message.chat.id)
            week_data = self.api.get_current_week_schedule()
            text = format_week_schedule(week_data, "текущую неделю (с понедельника)")
            self.bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        
        @self.bot.message_handler(commands=['date'])
        def cmd_date(message):
            self.users.update_user(message.chat.id)
            try:
                args = message.text.split()
                if len(args) < 2:
                    self.bot.reply_to(message, "📅 Используйте: /date YYYY-MM-DD\nПример: /date 2026-02-25")
                    return
                date_str = args[1]
                datetime.strptime(date_str, "%Y-%m-%d")
                day_data = self.api.get_day_schedule(date_str)
                text = format_day_schedule(day_data)
                self.bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
            except ValueError:
                self.bot.reply_to(message, "❌ Неверный формат даты!")
        
        @self.bot.message_handler(commands=['status'])
        def cmd_status(message):
            self.users.update_user(message.chat.id)
            status = f"🤖 *Статус бота*\n\n⏱️ Автопроверка: каждые 20 мин\n📅 Сегодня: {datetime.now().strftime('%d.%m.%Y')}\n💾 Кэш дней: {len(self.cache.data)}\n👥 Пользователей: {self.users.get_users_count()}\n✅ Статус: Работает"
            self.bot.send_message(message.chat.id, status, reply_markup=get_main_keyboard(), parse_mode="Markdown")
        
        @self.bot.message_handler(commands=['off'])
        def cmd_off(message):
            self.users.update_user(message.chat.id)
            self.auto_check_enabled = False
            self.bot.send_message(message.chat.id, "🔕 Уведомления отключены", reply_markup=get_main_keyboard())
        
        @self.bot.message_handler(commands=['on'])
        def cmd_on(message):
            self.users.update_user(message.chat.id)
            self.auto_check_enabled = True
            self.bot.send_message(message.chat.id, "🔔 Уведомления включены", reply_markup=get_main_keyboard())
    
    def send_change_notification(self, changed_dates):
        text = f"🔔 *Обновление расписания!*\n\nИзменения обнаружены в {len(changed_dates)} дн(я/ей):\n\n"
        for date_str in changed_dates:
            day_data = self.api.get_day_schedule(date_str)
            text += format_day_schedule(day_data) + "\n" + "-" * 40 + "\n"
        users = self.users.get_all_users()
        log(f"📩 Отправка уведомления {len(users)} пользователям")
        for chat_id in users:
            try:
                self.bot.send_message(chat_id, text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
                time.sleep(0.5)
            except Exception as e:
                log(f"❌ Ошибка отправки {chat_id}: {e}", "ERROR")
    
    def auto_check(self):
        if not self.auto_check_enabled:
            return
        log("🔄 Запуск автопроверки...")
        today = datetime.now()
        changed_dates = []
        for i in range(Config.CHECK_DAYS_AHEAD):
            check_date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            day_data = self.api.get_day_schedule(check_date)
            new_hash = get_schedule_hash(day_data)
            if self.cache.has_changed(check_date, new_hash):
                log(f"📢 Изменения на {check_date}!")
                changed_dates.append(check_date)
                self.cache.set(check_date, new_hash)
            else:
                log(f"✅ Без изменений: {check_date}")
        if changed_dates:
            self.send_change_notification(changed_dates)
        else:
            log("ℹ️ Изменений нет")
    
    def run_auto_check_loop(self):
        log("=" * 50)
        log("🤖 ЗАПУСК АВТОПРОВЕРКИ")
        log(f"⏱️ Интервал: {Config.AUTO_CHECK_INTERVAL // 60} мин")
        log(f"📅 Проверка дней: {Config.CHECK_DAYS_AHEAD}")
        log(f"👥 Пользователей: {self.users.get_users_count()}")
        log("=" * 50)
        while True:
            try:
                self.auto_check()
                log(f"⏳ Следующая проверка через {Config.AUTO_CHECK_INTERVAL // 60} мин...")
                time.sleep(Config.AUTO_CHECK_INTERVAL)
            except KeyboardInterrupt:
                log("\n👋 Автопроверка остановлена")
                break
            except Exception as e:
                log(f"❌ Ошибка в автопроверке: {e}", "ERROR")
                time.sleep(60)
    
    def run(self):
        log("=" * 50)
        log("🤖 ЗАПУСК TELEGRAM БОТА")
        log(f"🔑 Токен: {Config.TELEGRAM_BOT_TOKEN[:20]}...")
        log(f"🎓 Группа: {Config.GROUP_NAME}")
        log(f"👥 Пользователей: {self.users.get_users_count()}")
        log("=" * 50)
        auto_thread = threading.Thread(target=self.run_auto_check_loop, daemon=True)
        auto_thread.start()
        self.bot.infinity_polling(timeout=Config.TELEGRAM_TIMEOUT, long_polling_timeout=Config.TELEGRAM_TIMEOUT)


if __name__ == "__main__":
    try:
        import requests
        import telebot
    except ImportError as e:
        print(f"❌ Библиотека не установлена: {e}")
        print("\n📋 Выполните команду:\n")
        print("   pip install requests pyTelegramBotAPI\n")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎓 БОТ РАСПИСАНИЯ v5.0")
    print(f"   Группа: {Config.GROUP_NAME}")
    print(f"   Owner ID: {Config.OWNER_ID}")
    print(f"   Неделя: с понедельника")
    print(f"   Сокращения: ✅")
    print("=" * 50 + "\n")
    
    bot = ScheduleBot()
    bot.run()










