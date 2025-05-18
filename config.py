#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
PROXY_LIST_URL = "https://raw.githubusercontent.com/hookzof/socks5_list/master/tg/mtproto.json"
NUM_PROXIES_TO_SEND = 9  # تعداد پروکسی‌های ارسالی
NUM_PROXIES_FOR_USER = 3  # تعداد پروکسی‌های ارسالی به کاربر
STORAGE_FILE = "stored_proxies.json"  # فایل ذخیره پروکسی‌ها
MAX_PROXY_AGE_HOURS = 48  # حداکثر عمر پروکسی‌ها (ساعت)
CHECK_INTERVAL_HOURS = 0.00833  # فاصله زمانی بررسی پروکسی‌های جدید (30 ثانیه)
TELEGRAM_BOT_TOKEN = "7063996040:AAHr3hIzfqg_AJ0X-mglakYyASboRyMOlqE"
# تنظیم کانال تلگرام برای ارسال پروکسی‌ها
TELEGRAM_CHANNEL_ID = "@server_proxy0"  # کانال جدید برای ارسال پروکسی‌ها
SPONSOR_CHANNEL_ID = os.getenv("SPONSOR_CHANNEL_ID", "@server_proxy0")  # کانال اسپانسر - مقدار پیش‌فرض در صورت عدم تعریف در فایل .env


# تنظیمات API تلگرام برای دریافت پروکسی‌ها از کانال
TELEGRAM_API_ID = '1139980'  # API ID خود را اینجا قرار دهید
TELEGRAM_API_HASH = '2aa840c0a7b4a0df0170b17bd01d66d4'  # API Hash خود را اینجا قرار دهید
TELEGRAM_SESSION_STRING = '1BJWap1wBu4dmSnSQLiOUtUfg7qYGVbwYjaUcGuW2TrdqllgXH8eIa4tz3v9DWw__WWXpQA1FbGugbPwvPTZZuBISDEUcdvuV3pFd4Dv2u-2N6DIVqJa0gsRFWyIAQTEL9IRb_4gWlyuLRD6VjPt_psUGz2XKxKyVGxrl5CUCaU12KlyPMXWzwDzVo4ib-aD4n_HT_0rBOfXiu-YlVvjJBaFOFKeEkCpLbsf8m4mqm8FRe_B-v-GFJ0830l2PWAOlRZjGHeuKx7i64VQPFyvJTsLyZAj1hA7M6GUMkJImBJ7WJkBclhcWOHHZNqBJVB6gniKWTCxUKZxZn31QNe6VFSF11vI5-W8='  # رشته نشست تلگرام را اینجا قرار دهید (می‌توانید با اجرای اسکریپت جداگانه‌ای آن را ایجاد کنید)