import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Your web app URL (where your FastAPI app is hosted)
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://your-app-url.com/game')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    # Create the web app button
    keyboard = [
        [InlineKeyboardButton("🎮 Play Tic-Tac-Toe", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = f"""
🎉 Welcome to Tic-Tac-Toe, {user.mention_html()}!

Ready to play the classic game right here in Telegram? 

Click the button below to start playing:
    """

    await update.message.reply_html(
        welcome_message,
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🎮 <b>Tic-Tac-Toe Bot Help</b>

<b>Commands:</b>
• /start - Start the bot and play the game
• /play - Open the game directly
• /help - Show this help message

<b>How to Play:</b>
1. Click the "Play Tic-Tac-Toe" button
2. The game will open in a mini app
3. Player X always goes first
4. Click on empty squares to make your move
5. Get 3 in a row to win!

<b>Features:</b>
• Real-time gameplay
• Beautiful interface
• New game anytime
• Works seamlessly in Telegram

Have fun playing! 🎯
    """

    await update.message.reply_html(help_text)


async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the game directly when /play is issued."""
    keyboard = [
        [InlineKeyboardButton("🎮 Play Tic-Tac-Toe", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎮 Ready to play Tic-Tac-Toe?",
        reply_markup=reply_markup
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("play", play_command))

    # Add error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
