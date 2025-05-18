#!/usr/bin/env python3

import asyncio
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import TELEGRAM_BOT_TOKEN, CHECK_INTERVAL_HOURS
from telegram_bot import start, button_callback, process_proxies

def main():
    """Run the bot and the channel update task."""
    print("Starting Proxy Sender Script...")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the background task in a separate thread
    def run_background_updates():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def background_task():
            while True:
                try:
                    await process_proxies()
                except Exception as e:
                    print(f"Error in process_proxies: {e}")
                
                # Wait for the specified interval
                seconds = int(CHECK_INTERVAL_HOURS * 3600)
                print(f"Waiting {seconds} seconds before next check...")
                await asyncio.sleep(seconds)
        
        loop.run_until_complete(background_task())
    
    # Start the background thread
    update_thread = threading.Thread(target=run_background_updates)
    update_thread.daemon = True  # This makes the thread exit when the main program exits
    update_thread.start()
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()