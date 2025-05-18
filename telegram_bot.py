#!/usr/bin/env python3

import asyncio
import aiohttp
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, NUM_PROXIES_FOR_USER, SPONSOR_CHANNEL_ID
from proxy_utils import (
    fetch_proxies, load_stored_proxies, save_stored_proxies, clean_old_proxies,
    is_duplicate_proxy, add_timestamp_to_proxy, format_proxy_message,
    check_proxy_status, check_proxies_status, load_sent_proxies, 
    save_sent_proxies, is_recently_sent_proxy, add_sent_proxies
)

async def send_telegram_message(bot, channel_id, proxies_to_send):
    """Sends the details of the first N proxies to a Telegram channel."""
    if not bot or not channel_id:
        print("Telegram Bot Token or Channel ID not configured. Skipping notification.")
        return
    if not proxies_to_send:
        print("No proxies found to send.")
        return

    print(f"Sending details of {len(proxies_to_send)} proxies to Telegram channel {channel_id}...")
    
    message, _ = format_proxy_message(proxies_to_send)
    
    try:
        # Ensure message length is within Telegram limits (4096 chars)
        if len(message) > 4096:
             message = message[:4090] + "\n[...]" # Truncate if too long
        # Using parse_mode='HTML' for the links to work
        await bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML', disable_web_page_preview=True)
        print("Successfully sent notification to Telegram.")
    except TelegramError as e:
        print(f"Error sending Telegram message: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while sending Telegram message: {e}")

async def process_proxies():
    """Main function to fetch, process and send proxies."""
    # Basic check for required environment variables
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set in environment variables or .env file.")
        return

    # Load stored proxies
    stored_proxies = load_stored_proxies()
    
    # Clean old proxies
    stored_proxies = clean_old_proxies(stored_proxies)
    
    # Load sent proxies
    sent_proxies = load_sent_proxies()
    
    async with aiohttp.ClientSession() as session:
        # Fetch new proxies
        new_proxies = await fetch_proxies(session)
        if not new_proxies:
            print("No proxies fetched, exiting.")
            return
        
        # Find non-duplicate proxies
        non_duplicate_proxies = []
        for proxy in new_proxies:
            if not is_duplicate_proxy(proxy, stored_proxies):
                # Add timestamp to new proxy
                proxy_with_timestamp = add_timestamp_to_proxy(proxy)
                non_duplicate_proxies.append(proxy_with_timestamp)
                # Also add to stored proxies
                stored_proxies.append(proxy_with_timestamp)
        
        print(f"Found {len(non_duplicate_proxies)} new non-duplicate proxies.")
        
        # Save updated stored proxies
        save_stored_proxies(stored_proxies)
        
        # انتخاب پروکسی‌ها برای بررسی (اگر پروکسی جدید نداریم، از ذخیره شده‌ها استفاده کنیم)
        proxies_to_check = []
        if non_duplicate_proxies:
            # اگر پروکسی جدید داریم، حداکثر 50 تا را بررسی کنیم
            proxies_to_check = non_duplicate_proxies[:50]
        else:
            # اگر پروکسی جدید نداریم، از پروکسی‌های ذخیره شده استفاده کنیم
            # Sort stored proxies by timestamp (newest first)
            sorted_stored = sorted(stored_proxies, key=lambda x: x.get('timestamp', 0), reverse=True)
            # انتخاب 50 پروکسی از جدیدترین‌ها برای بررسی
            proxies_to_check = sorted_stored[:50]
        
        print(f"Checking status of {len(proxies_to_check)} proxies...")
        
        # بررسی وضعیت پروکسی‌های انتخاب شده
        active_proxies = await check_proxies_status(proxies_to_check)
        
        # حذف پروکسی‌های تکراری (پروکسی‌هایی که در ۳ پیام اخیر ارسال شده‌اند)
        non_recent_proxies = []
        for proxy in active_proxies:
            if not is_recently_sent_proxy(proxy, sent_proxies["channel"]):
                non_recent_proxies.append(proxy)
        
        print(f"Found {len(non_recent_proxies)} non-recent active proxies.")
        
        # Select proxies to send (prefer active proxies that haven't been sent recently)
        from config import NUM_PROXIES_TO_SEND
        proxies_to_send = non_recent_proxies[:NUM_PROXIES_TO_SEND]
        
        # If we don't have enough non-recent active proxies, use other active proxies
        if len(proxies_to_send) < NUM_PROXIES_TO_SEND and len(active_proxies) > len(proxies_to_send):
            print(f"Not enough non-recent active proxies, using other active proxies to reach {NUM_PROXIES_TO_SEND}...")
            for proxy in active_proxies:
                if proxy not in proxies_to_send and len(proxies_to_send) < NUM_PROXIES_TO_SEND:
                    proxies_to_send.append(proxy)
        
        # If we still don't have enough proxies, use the newest from stored
        if len(proxies_to_send) < NUM_PROXIES_TO_SEND:
            print(f"Not enough active proxies, using stored proxies to reach {NUM_PROXIES_TO_SEND}...")
            # Sort stored proxies by timestamp (newest first)
            sorted_stored = sorted(stored_proxies, key=lambda x: x.get('timestamp', 0), reverse=True)
            # Add more proxies until we reach NUM_PROXIES_TO_SEND
            for proxy in sorted_stored:
                if len(proxies_to_send) >= NUM_PROXIES_TO_SEND:
                    break
                if proxy not in proxies_to_send and not is_recently_sent_proxy(proxy, sent_proxies["channel"]):
                    proxies_to_send.append(proxy)
        
        if proxies_to_send:
            try:
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                # Pass the list of proxies directly
                await send_telegram_message(bot, TELEGRAM_CHANNEL_ID, proxies_to_send)
                
                # ذخیره پروکسی‌های ارسال شده
                add_sent_proxies(proxies_to_send)
                
                print(f"Successfully sent {len(proxies_to_send)} proxies to channel.")
            except Exception as e:
                print(f"Failed to initialize Telegram Bot or send message: {e}")
        else:
            print("No proxies to send.")
    
    return stored_proxies

async def get_proxies_for_user(user_id, num_proxies=NUM_PROXIES_FOR_USER):
    """Get a list of proxies for a user request."""
    stored_proxies = load_stored_proxies()
    
    if not stored_proxies:
        # If no stored proxies, try to fetch new ones
        async with aiohttp.ClientSession() as session:
            new_proxies = await fetch_proxies(session)
            if new_proxies:
                for proxy in new_proxies:
                    stored_proxies.append(add_timestamp_to_proxy(proxy))
                save_stored_proxies(stored_proxies)
    
    # Sort by timestamp (newest first)
    sorted_proxies = sorted(stored_proxies, key=lambda x: x.get('timestamp', 0), reverse=True)
    
    # انتخاب تعدادی از پروکسی‌های جدید برای بررسی (حداکثر 20 پروکسی)
    proxies_to_check = sorted_proxies[:20]
    
    print(f"Checking status of {len(proxies_to_check)} proxies for user request...")
    
    # بررسی وضعیت پروکسی‌ها
    active_proxies = await check_proxies_status(proxies_to_check)
    
    # Load sent proxies
    sent_proxies = load_sent_proxies()
    
    # حذف پروکسی‌های تکراری (پروکسی‌هایی که در ۳ پیام اخیر ارسال شده‌اند)
    non_recent_proxies = []
    user_sent_proxies = sent_proxies["users"].get(str(user_id), [])
    
    for proxy in active_proxies:
        if not is_recently_sent_proxy(proxy, user_sent_proxies):
            non_recent_proxies.append(proxy)
    
    print(f"Found {len(non_recent_proxies)} non-recent active proxies for user.")
    
    # اگر پروکسی فعال غیرتکراری کافی نداریم، از پروکسی‌های فعال دیگر استفاده کنیم
    proxies_to_send = non_recent_proxies[:num_proxies]
    
    if len(proxies_to_send) < num_proxies and len(active_proxies) > len(proxies_to_send):
        print(f"Not enough non-recent active proxies for user, using other active proxies...")
        for proxy in active_proxies:
            if proxy not in proxies_to_send and len(proxies_to_send) < num_proxies:
                proxies_to_send.append(proxy)
    
    # اگر هنوز پروکسی کافی نداریم، از پروکسی‌های ذخیره شده استفاده کنیم
    if len(proxies_to_send) < num_proxies:
        print(f"Not enough active proxies for user, using stored proxies to reach {num_proxies}...")
        # اضافه کردن پروکسی‌های ذخیره شده تا رسیدن به تعداد مورد نیاز
        for proxy in sorted_proxies:
            if proxy not in proxies_to_send and len(proxies_to_send) < num_proxies and not is_recently_sent_proxy(proxy, user_sent_proxies):
                proxies_to_send.append(proxy)
    
    # ذخیره پروکسی‌های ارسال شده به کاربر
    if proxies_to_send:
        add_sent_proxies(proxies_to_send, user_id)
    
    # Return the proxies
    return proxies_to_send[:num_proxies]

async def check_user_membership(bot, user_id, channel_id):
    """بررسی عضویت کاربر در کانال اسپانسر"""
    try:
        # حذف @ از ابتدایی آیدی کانال اگر وجود داشته باشد
        if channel_id.startswith('@'):
            channel_username = channel_id
        else:
            channel_username = '@' + channel_id
            
        chat_member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        status = chat_member.status
        
        # بررسی وضعیت عضویت کاربر
        if status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"خطا در بررسی عضویت کاربر: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    
    # بررسی عضویت کاربر در کانال اسپانسر
    is_member = await check_user_membership(context.bot, user_id, SPONSOR_CHANNEL_ID)
    
    if not is_member:
        # کاربر عضو کانال اسپانسر نیست
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{SPONSOR_CHANNEL_ID.replace('@', '')}")],
            [InlineKeyboardButton("بررسی مجدد عضویت", callback_data='check_membership')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f'سلام! 👋\n\n'
            f'برای استفاده از ربات، لطفا ابتدا در کانال ما عضو شوید. 🌟\n\n'
            f'پس از عضویت، روی دکمه «بررسی مجدد عضویت» کلیک کنید. ✅',
            reply_markup=reply_markup
        )
    else:
        # کاربر عضو کانال اسپانسر است
        keyboard = [
            [InlineKeyboardButton("دریافت پروکسی", callback_data='get_proxy')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f'سلام! 🎉\n\n'
            f'تبریک! ربات برای شما فعال شد. ✨\n\n'
            f'برای دریافت پروکسی روی دکمه زیر کلیک کنید:',
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'check_membership':
        # بررسی مجدد عضویت کاربر
        user_id = update.effective_user.id
        is_member = await check_user_membership(context.bot, user_id, SPONSOR_CHANNEL_ID)
        
        if not is_member:
            # کاربر هنوز عضو کانال نیست
            keyboard = [
                [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{SPONSOR_CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton("بررسی مجدد عضویت", callback_data='check_membership')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f'شما هنوز عضو کانال ما نیستید. 😕\n\n'
                f'لطفا ابتدا در کانال عضو شوید و سپس روی دکمه «بررسی مجدد عضویت» کلیک کنید. 🔄',
                reply_markup=reply_markup
            )
        else:
            # کاربر عضو کانال است
            keyboard = [
                [InlineKeyboardButton("دریافت پروکسی", callback_data='get_proxy')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f'تبریک! 🎊\n\n'
                f'عضویت شما در کانال تأیید شد و ربات برای شما فعال شد. ✅\n\n'
                f'برای دریافت پروکسی روی دکمه زیر کلیک کنید:',
                reply_markup=reply_markup
            )
    
    elif query.data == 'get_proxy':
        # بررسی مجدد عضویت کاربر قبل از ارسال پروکسی
        user_id = update.effective_user.id
        is_member = await check_user_membership(context.bot, user_id, SPONSOR_CHANNEL_ID)
        
        if not is_member:
            # کاربر دیگر عضو کانال نیست
            keyboard = [
                [InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{SPONSOR_CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton("بررسی مجدد عضویت", callback_data='check_membership')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f'متأسفانه شما از کانال ما خارج شده‌اید. 😢\n\n'
                f'برای استفاده از ربات، لطفا مجدداً در کانال عضو شوید. 🔄',
                reply_markup=reply_markup
            )
        else:
            # دریافت پروکسی‌ها
            proxies = await get_proxies_for_user(user_id)
            
            if proxies:
                message, _ = format_proxy_message(proxies)
                await query.message.reply_html(
                    text=message,
                    disable_web_page_preview=True
                )
            else:
                await query.message.reply_text("متأسفانه در حال حاضر پروکسی در دسترس نیست. لطفاً بعداً دوباره امتحان کنید. 😔")