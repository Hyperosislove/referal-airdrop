import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from telethon import TelegramClient, events
import pymongo
from datetime import datetime
from pymongo import MongoClient

# Fetching the MongoDB URI, Bot Token, API ID, and API Hash from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client['cryptocutie']
users = db['users']

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telethon Client for handling user-level interactions (optional if needed)
telethon_client = TelegramClient('session_name', API_ID, API_HASH)

# Helper function to check if wallet address is valid
def is_valid_wallet_address(address: str):
    return address.startswith("T")  # Example for Tron addresses

# Register new user and give them a starting balance
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    referrer = context.args[0] if len(context.args) > 0 else None
    
    # Check if user is already registered
    user = users.find_one({"user_id": user_id})
    
    if not user:
        # New user, add to the database and give them 0.5 USDT starting balance
        users.insert_one({
            "user_id": user_id,
            "user_name": user_name,
            "balance": 0.5,
            "points": 0,
            "referrals": 0,
            "referrer": referrer,
            "created_at": datetime.now()
        })
        
        # If they were referred by someone, give the referrer 0.5 USDT
        if referrer:
            referrer_user = users.find_one({"user_id": referrer})
            if referrer_user:
                users.update_one({"user_id": referrer}, {"$inc": {"balance": 0.5, "referrals": 1}})
        
        await update.message.reply_text(
            f"Welcome {user_name}! 🎉 You've been registered and received 0.5 USDT. \n\n"
            "Use /points to check your points, and /referral to get your referral link!"
        )
    else:
        await update.message.reply_text(f"Welcome back, {user_name}! 😊")

# Command to check points
async def points(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = users.find_one({"user_id": user_id})
    
    if user:
        await update.message.reply_text(f"Your current points: {user['points']} 🏅\nBalance: {user['balance']} USDT 💰")
    else:
        await update.message.reply_text("You need to register first by typing /start")

# Referral system: Display referral link
async def referral(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(f"Your referral link: {referral_link} 🔗\nInvite friends and earn rewards!")

# Handle withdrawal (Dummy system for now)
async def withdraw(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = users.find_one({"user_id": user_id})
    
    if user and user['balance'] >= 5:
        await update.message.reply_text(
            "Your withdrawal request has been processed! 💸 Please send your wallet address (USDT) for the transfer. 🔜"
        )
        await update.message.reply_text("Please send your wallet address below:")
    else:
        await update.message.reply_text(
            "You need to have at least 5 USDT to withdraw. Your current balance is: "
            f"{user['balance']} USDT 💰"
        )

# Handling wallet address submission for withdrawal (for now just log it)
async def handle_wallet(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    wallet_address = update.message.text

    # Ensure the wallet address is valid
    if is_valid_wallet_address(wallet_address):
        users.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": -5}}  # Decrease 5 USDT for withdrawal (Dummy)
        )
        await update.message.reply_text(
            f"Your withdrawal of 5 USDT has been processed. 🚀 Your wallet address is: {wallet_address} 💼"
        )
    else:
        await update.message.reply_text("Invalid wallet address! Please provide a valid USDT wallet address.")

# Admin commands (for future use)
async def admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    # Replace with the admin's user ID
    ADMIN_ID = 123456789  
    if user_id == ADMIN_ID:
        await update.message.reply_text("You are an admin! Here you can manage user data.")
    else:
        await update.message.reply_text("You are not authorized to access the admin panel.")

# Start Telethon Client to listen for events (optional)
async def start_telethon():
    await telethon_client.start()
    print("Telethon client is running...")

# Main function to handle Telegram Bot commands
async def main():
    # Create application with bot token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("points", points))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))
    application.add_handler(CommandHandler("admin", admin))  # Admin panel (future)

    # Run the bot
    await application.run_polling()

# Run the bot and the Telethon client asynchronously
if __name__ == '__main__':
    asyncio.run(main())
    asyncio.run(start_telethon())
