#!/usr/bin/env python3

import json
import time
import asyncio
import aiohttp
from config import PROXY_LIST_URL, STORAGE_FILE, MAX_PROXY_AGE_HOURS

import os
import json

# فایل ذخیره‌سازی پروکسی‌های ارسال شده
SENT_PROXIES_FILE = "sent_proxies.json"

def load_sent_proxies():
    """Load previously sent proxies from file"""
    if not os.path.exists(SENT_PROXIES_FILE):
        return {"channel": [], "users": {}}
    
    try:
        with open(SENT_PROXIES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading sent proxies: {e}")
        return {"channel": [], "users": {}}

def save_sent_proxies(sent_proxies):
    """Save sent proxies to file"""
    try:
        with open(SENT_PROXIES_FILE, 'w') as f:
            json.dump(sent_proxies, f)
    except Exception as e:
        print(f"Error saving sent proxies: {e}")

def is_recently_sent_proxy(proxy, sent_proxies_list):
    """Check if a proxy was recently sent (exists in the last 3 batches)"""
    # اگر لیست خالی است، پروکسی تکراری نیست
    if not sent_proxies_list:
        return False
    
    # بررسی آخرین ۳ دسته پروکسی ارسال شده (یا کمتر اگر کمتر از ۳ دسته وجود دارد)
    recent_batches = sent_proxies_list[-3:] if len(sent_proxies_list) >= 3 else sent_proxies_list
    
    # بررسی وجود پروکسی در دسته‌های اخیر
    for batch in recent_batches:
        for sent_proxy in batch:
            if proxy.get('host') == sent_proxy.get('host') and proxy.get('port') == sent_proxy.get('port'):
                return True
    
    return False

def add_sent_proxies(proxies, user_id=None):
    """Add proxies to the sent proxies list"""
    sent_proxies = load_sent_proxies()
    
    if user_id:
        # اضافه کردن به لیست پروکسی‌های ارسال شده به کاربر
        if str(user_id) not in sent_proxies["users"]:
            sent_proxies["users"][str(user_id)] = []
        
        # اضافه کردن دسته جدید پروکسی‌ها
        sent_proxies["users"][str(user_id)].append(proxies)
        
        # نگه داشتن فقط ۳ دسته آخر
        if len(sent_proxies["users"][str(user_id)]) > 3:
            sent_proxies["users"][str(user_id)] = sent_proxies["users"][str(user_id)][-3:]
    else:
        # اضافه کردن به لیست پروکسی‌های ارسال شده به کانال
        sent_proxies["channel"].append(proxies)
        
        # نگه داشتن فقط ۳ دسته آخر
        if len(sent_proxies["channel"]) > 3:
            sent_proxies["channel"] = sent_proxies["channel"][-3:]
    
    save_sent_proxies(sent_proxies)

async def fetch_proxies(session):
    """Fetches the list of proxies from the specified URL."""
    print(f"Fetching proxy list from {PROXY_LIST_URL}...")
    try:
        async with session.get(PROXY_LIST_URL) as response:
            response.raise_for_status()  # Raise an exception for bad status codes
            # Tell aiohttp to ignore the content type and parse as JSON
            proxies = await response.json(content_type=None)
            print(f"Successfully fetched {len(proxies)} proxies.")
            return proxies
    except aiohttp.ClientError as e:
        print(f"Error fetching proxy list: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from proxy list: {e}")
        return []

def load_stored_proxies():
    """Load previously stored proxies from file."""
    import os
    if not os.path.exists(STORAGE_FILE):
        return []
    
    try:
        with open(STORAGE_FILE, 'r') as f:
            stored_proxies = json.load(f)
            print(f"Loaded {len(stored_proxies)} stored proxies.")
            return stored_proxies
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading stored proxies: {e}")
        return []

def save_stored_proxies(proxies):
    """Save proxies to storage file."""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(proxies, f, indent=2)
            print(f"Saved {len(proxies)} proxies to storage.")
    except IOError as e:
        print(f"Error saving proxies to file: {e}")

def clean_old_proxies(stored_proxies):
    """Remove proxies older than MAX_PROXY_AGE_HOURS."""
    current_time = time.time()
    max_age_seconds = MAX_PROXY_AGE_HOURS * 3600
    
    new_stored_proxies = []
    removed_count = 0
    
    for proxy in stored_proxies:
        # Check if the proxy has a timestamp and is not too old
        if 'timestamp' in proxy and (current_time - proxy['timestamp']) <= max_age_seconds:
            new_stored_proxies.append(proxy)
        else:
            removed_count += 1
    
    print(f"Removed {removed_count} proxies older than {MAX_PROXY_AGE_HOURS} hours.")
    return new_stored_proxies

def is_duplicate_proxy(proxy, stored_proxies):
    """Check if a proxy is already in the stored list."""
    for stored_proxy in stored_proxies:
        if (proxy.get('host') == stored_proxy.get('host') and 
            proxy.get('port') == stored_proxy.get('port') and 
            proxy.get('secret') == stored_proxy.get('secret')):
            return True
    return False

def add_timestamp_to_proxy(proxy):
    """Add current timestamp to proxy."""
    proxy_with_timestamp = proxy.copy()
    proxy_with_timestamp['timestamp'] = time.time()
    return proxy_with_timestamp

def format_proxy_message(proxies_to_send):
    """Format proxies for sending in a message."""
    # Create a list to hold valid proxies
    valid_proxies = []
    
    # Filter valid proxies
    for proxy in proxies_to_send:
        server = proxy.get('host')
        port = proxy.get('port')
        secret = proxy.get('secret')
        
        if server and port and secret:
            # ایجاد لینک پروکسی بدون کاراکترهای اضافی
            proxy_link = f"https://t.me/proxy?server={server}&port={port}&secret={secret}"
            valid_proxies.append(proxy_link)
        else:
            print(f"Skipping invalid proxy entry: {proxy}")
    
    # Format message in rows of 3 proxies
    message_lines = []
    
    # Process proxies in groups of 3
    for i in range(0, len(valid_proxies), 3):
        row_proxies = valid_proxies[i:i+3]
        # Create HTML links with "پروکسی" as the text
        row_text = " | ".join([f"<a href=\"{link}\">پروکسی</a>" for link in row_proxies])
        message_lines.append(row_text)
    
    # Add channel ID at the end with a clickable link
    message_lines.append("\n🆔 <a href=\"https://t.me/proxy_finde\">proxyfinder</a>")
    
    # Join all lines with double newlines for better readability
    message = "\n".join(message_lines)
    
    return message, valid_proxies


async def check_proxy_status(session, proxy, timeout=10):
    """Check if a proxy is active"""
    try:
        # Extract proxy details
        server = proxy.get('host')
        port = proxy.get('port')
        secret = proxy.get('secret')
        
        if not server or not port:
            return False
        
        # For MTProto proxies, we can't directly test them with HTTP requests
        # Instead, we'll check if the server is reachable
        try:
            # Try to establish a TCP connection to the proxy server
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(server, port),
                timeout=timeout
            )
            
            # If we can connect, close the connection and return success
            writer.close()
            await writer.wait_closed()
            
            print(f"Proxy {server}:{port} is reachable")
            return True
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            print(f"Proxy {server}:{port} is not reachable")
            return False
            
    except Exception as e:
        print(f"Error checking proxy status: {e}")
        return False

async def check_proxies_status(proxies, max_concurrent=10):
    """Check status of multiple proxies concurrently"""
    active_proxies = []
    
    # Create semaphore to limit concurrent connections
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_with_semaphore(proxy):
        async with semaphore:
            is_active = await check_proxy_status(None, proxy)
            if is_active:
                active_proxies.append(proxy)
    
    # Create tasks for checking proxies
    tasks = [check_with_semaphore(proxy) for proxy in proxies]
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    print(f"Found {len(active_proxies)} active proxies out of {len(proxies)} checked")
    return active_proxies
    
    # ایجاد یک نشست HTTP
    connector = aiohttp.TCPConnector(ssl=False, limit=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        # ایجاد تسک‌های بررسی پروکسی
        tasks = []
        for proxy in proxies:
            task = asyncio.create_task(check_proxy_status(session, proxy))
            tasks.append((proxy, task))
        
        # انتظار برای تکمیل تسک‌ها
        for proxy, task in tasks:
            try:
                is_active = await task
                if is_active:
                    active_proxies.append(proxy)
                    print(f"پروکسی فعال یافت شد: {proxy.get('host')}:{proxy.get('port')}")
            except Exception as e:
                print(f"خطا در بررسی پروکسی: {e}")
    
    print(f"از {len(proxies)} پروکسی، {len(active_proxies)} پروکسی فعال یافت شد.")
    return active_proxies


async def fetch_proxies_from_telegram(session=None):
    """دریافت پروکسی‌ها از کانال تلگرام @darkproxy"""
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    import re
    from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING
    
    proxies = []
    
    try:
        # اتصال به تلگرام با استفاده از telethon
        client = TelegramClient(StringSession(TELEGRAM_SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.start()
        
        # دریافت ۵ پیام اخیر از کانال @darkproxy
        channel_username = 'darkproxy'
        messages = await client.get_messages(channel_username, limit=10)
        
        # الگوهای regex بهبود یافته برای استخراج پروکسی‌ها
        # این الگو هم لینک‌های کامل و هم لینک‌های با کاراکتر | در انتها را تشخیص می‌دهد
        mtproto_pattern = r'https?://t\.me/proxy\?server=([^&\s]+)&port=([^&\s]+)&secret=([^&\s\|\)]+)(?:\||\))?'
        
        # بررسی هر پیام
        for message in messages:
            if message.text:
                # استخراج پروکسی‌های MTProto
                mtproto_matches = re.findall(mtproto_pattern, message.text)
                
                for match in mtproto_matches:
                    server, port, secret = match
                    
                    # پاکسازی secret از کاراکترهای اضافی
                    secret = secret.strip()
                    
                    # اضافه کردن پروکسی به لیست
                    proxy = {
                        'type': 'mtproto',
                        'host': server,
                        'port': port,
                        'secret': secret,
                        'source': 'telegram_channel'
                    }
                    
                    # بررسی تکراری نبودن پروکسی در لیست
                    if not any(p.get('host') == server and p.get('port') == port and p.get('secret') == secret for p in proxies):
                        proxies.append(proxy)
        
        # بستن اتصال
        await client.disconnect()
        
        print(f"Found {len(proxies)} proxies from Telegram channel @darkproxy")
        
    except Exception as e:
        print(f"Error fetching proxies from Telegram: {e}")
    
    return proxies

# جایگزینی تابع fetch_proxies قبلی
async def fetch_proxies(session=None):
    """دریافت پروکسی‌ها از منابع مختلف"""
    # استفاده از تابع جدید برای دریافت پروکسی‌ها از کانال تلگرام
    return await fetch_proxies_from_telegram(session)