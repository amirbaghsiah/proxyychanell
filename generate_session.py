from telethon import TelegramClient
from telethon.sessions import StringSession

# اطلاعات API خود را اینجا وارد کنید
api_id = input("API ID خود را وارد کنید: ")
api_hash = input("API Hash خود را وارد کنید: ")

# ایجاد کلاینت
with TelegramClient(StringSession(), api_id, api_hash) as client:
    # ورود به حساب کاربری
    client.start()
    
    # چاپ رشته نشست
    print("\nرشته نشست شما:\n")
    print(client.session.save())
    print("\nاین رشته را در فایل config.py در متغیر TELEGRAM_SESSION_STRING قرار دهید.")