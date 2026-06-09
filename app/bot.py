# ==========================================
# MODULE: TELEGRAM BOT HANDLERS
# PURPOSE: Handle bot commands and user interactions
# ==========================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError
from sqlalchemy.orm import Session
import logging
from typing import List, Optional
from datetime import datetime

from app.config import get_settings
from app.database import SessionLocal
from app.services import (
    UserService, ButtonService, ChannelService, SupportService
)
from app.repositories import UserRepository

# ========== Settings ==========
settings = get_settings()

# ========== Logging Configuration ==========
logger = logging.getLogger(__name__)


# ==========================================
# BOT COMMAND HANDLERS
# PURPOSE: Handle /start and other commands
# ==========================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    Creates user if new, shows main menu.
    """
    db = SessionLocal()
    try:
        user = update.effective_user
        user_service = UserService(db)
        channel_service = ChannelService(db)
        
        # Get or create user
        db_user = user_service.get_or_create_user(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        
        logger.info(f"✅ User started: {user.id} - {user.first_name}")
        
        # Check forced join requirement
        if not channel_service.can_user_access_bot(db_user.id):
            await show_forced_join_message(update, context, channel_service, db_user.id)
            return
        
        # Show main menu
        await show_main_menu(update, context, db_user.id)
    
    except Exception as e:
        logger.error(f"Error in start_command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again.")
    
    finally:
        db.close()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = """
📖 **Help**

Available commands:
/start - Start the bot and show menu
/help - Show this help message
/support - Contact support
/referral - Get your referral link

**Points System:**
Earn points by completing actions. Use points to unlock premium content.

**Forced Join:**
You must join required channels to use this bot.

**Support:**
Having issues? Use /support to contact us.
    """
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /support command"""
    db = SessionLocal()
    try:
        user_id = update.effective_user.id
        
        # Store state for multi-step support ticket creation
        context.user_data['support_step'] = 'awaiting_subject'
        context.user_data['support_user_id'] = user_id
        
        await update.message.reply_text(
            "📝 Support System\n\n"
            "Please describe your issue. Start with a subject line."
        )
    
    finally:
        db.close()


async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /referral command"""
    db = SessionLocal()
    try:
        user_id = update.effective_user.id
        user_repo = UserRepository(db)
        user = user_repo.get_by_telegram_id(user_id)
        
        if user:
            referral_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={user.referral_code}"
            referral_text = f"""
🎁 **Your Referral Link**

Share this link to earn {settings.REFERRAL_POINTS_PER_USER} points per referral:

`{referral_link}`

**Referrals:** {user.referral_count}
**Earned Points:** {user.referral_count * settings.REFERRAL_POINTS_PER_USER}
            """
            
            await update.message.reply_text(referral_text, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ User not found.")
    
    finally:
        db.close()


# ==========================================
# MENU DISPLAY HANDLERS
# PURPOSE: Show interactive menus
# ==========================================

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """
    Show main menu with available buttons.
    """
    db = SessionLocal()
    try:
        button_service = ButtonService(db)
        user_repo = UserRepository(db)
        
        user = user_repo.get_by_id(user_id)
        buttons = button_service.get_accessible_buttons(user_id)
        
        # Create inline keyboard
        keyboard = []
        for button in buttons:
            keyboard.append([
                InlineKeyboardButton(button.name, callback_data=f"button_{button.id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = f"""
👋 **Welcome {user.first_name}!**

📊 **Your Stats:**
🎯 Points: {user.points}
👥 Referrals: {user.referral_count}

Select an option:
        """
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Error in show_main_menu: {str(e)}")
        await update.message.reply_text("❌ Error loading menu.")
    
    finally:
        db.close()


async def show_forced_join_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    channel_service: ChannelService,
    user_id: int
) -> None:
    """
    Show message about required channel joins.
    """
    channels = channel_service.get_required_channels()
    
    if not channels:
        return
    
    keyboard = []
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"Join {channel.name}",
                url=f"https://t.me/{channel.channel_username}"
            )
        ])
    
    # Add verify button
    keyboard.append([
        InlineKeyboardButton("✅ I've Joined", callback_data="verify_channels")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    join_text = """
🔒 **Required Action**

You must join the following channels to use this bot:
    """
    
    for channel in channels:
        join_text += f"\n✓ {channel.name}"
    
    join_text += "\n\nClick the buttons below to join, then click 'I've Joined'."
    
    await update.message.reply_text(join_text, reply_markup=reply_markup, parse_mode="Markdown")


# ==========================================
# CALLBACK QUERY HANDLERS
# PURPOSE: Handle button clicks
# ==========================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle button press callbacks.
    """
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    try:
        callback_data = query.data
        user_id = update.effective_user.id
        
        if callback_data.startswith("button_"):
            # Handle menu button click
            button_id = int(callback_data.split("_")[1])
            await show_button_content(query, context, button_id, user_id, db)
        
        elif callback_data == "verify_channels":
            # Handle channel verification
            await verify_channels(query, context, user_id, db)
        
        elif callback_data == "back":
            # Go back to main menu
            await show_main_menu(query.message, context, user_id)
    
    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        await query.edit_message_text("❌ An error occurred.")
    
    finally:
        db.close()


async def show_button_content(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    button_id: int,
    user_id: int,
    db: Session
) -> None:
    """
    Show content for button.
    """
    button_service = ButtonService(db)
    user_repo = UserRepository(db)
    
    button = button_service.button_repo.get_by_id(button_id)
    user = user_repo.get_by_id(user_id)
    
    if not button:
        await query.edit_message_text("❌ Button not found.")
        return
    
    # Check if user has enough points
    if user.points < button.required_points:
        await query.edit_message_text(
            f"❌ You need {button.required_points} points to access this.\n"
            f"Your points: {user.points}"
        )
        return
    
    # Show content based on button type
    content_text = f"**{button.name}**\n\n"
    
    if button.button_type == "TEXT":
        content_text += button.content_text or "No content"
    
    elif button.button_type == "LINK":
        content_text += f"[Open Link]({button.content_url})"
    
    # Add back button
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        content_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Log activity
    user_service = UserService(db)
    user_service.update_activity(user_id)


async def verify_channels(query, context: ContextTypes.DEFAULT_TYPE, user_id: int, db: Session) -> None:
    """
    Verify user has joined required channels.
    """
    channel_service = ChannelService(db)
    
    if channel_service.can_user_access_bot(user_id):
        await query.edit_message_text("✅ Thank you for joining! Enjoy the bot.")
        await show_main_menu(query.message, context, user_id)
    else:
        await query.edit_message_text(
            "⏳ Please join all channels first, then try again."
        )


# ==========================================
# MESSAGE HANDLERS
# PURPOSE: Handle regular messages
# ==========================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle regular text messages.
    """
    db = SessionLocal()
    try:
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if user is in support flow
        if context.user_data.get('support_step') == 'awaiting_subject':
            context.user_data['support_subject'] = text
            context.user_data['support_step'] = 'awaiting_description'
            
            await update.message.reply_text(
                "📝 Please describe your issue in detail:"
            )
            return
        
        elif context.user_data.get('support_step') == 'awaiting_description':
            support_service = SupportService(db)
            ticket = support_service.create_ticket(
                user_id=user_id,
                subject=context.user_data.get('support_subject', 'Support Request'),
                description=text
            )
            
            context.user_data.pop('support_step', None)
            context.user_data.pop('support_subject', None)
            
            await update.message.reply_text(
                f"✅ Support ticket created!\n"
                f"Ticket #: {ticket.ticket_number}\n\n"
                f"We'll respond to you shortly."
            )
            return
        
        # Default response
        await update.message.reply_text(
            "👋 I didn't understand that. Use /help for available commands."
        )
    
    except Exception as e:
        logger.error(f"Error in message_handler: {str(e)}")
        await update.message.reply_text("❌ An error occurred.")
    
    finally:
        db.close()


# ==========================================
# ERROR HANDLER
# PURPOSE: Handle errors
# ==========================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors in handlers.
    """
    logger.error(f"Update {update} caused error {context.error}")


# ==========================================
# CREATE AND START BOT
# PURPOSE: Initialize telegram bot
# ==========================================

async def setup_bot() -> Application:
    """
    Setup telegram bot with all handlers.
    
    Returns:
        Configured Application instance
    """
    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("referral", referral_command))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    logger.info("✅ Telegram bot handlers configured")
    
    return application


async def run_bot() -> None:
    """
    Run telegram bot polling.
    """
    app = await setup_bot()
    
    logger.info("🤖 Starting Telegram bot polling...")
    
    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("✅ Bot is polling...")
        await app.updater.idle()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())
