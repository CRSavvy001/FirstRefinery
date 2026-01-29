import os
import re
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Solana address pattern (base58, typically 32-44 characters)
SOLANA_ADDRESS_PATTERN = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
SOURCE_CHAT_ID = os.getenv('SOURCE_CHAT_ID')  # The group/channel to monitor
DESTINATION_CHAT_ID = os.getenv('DESTINATION_CHAT_ID')  # Where to send modified messages

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and detect Solana addresses"""
    
    logger.info("A new message received")
    
    message_text = update.message.text or update.message.caption or ""
    
    # Ignore messages from the bot itself
    if update.message.from_user.is_bot:
        logger.info(f"❌ IGNORED: Message from bot")
        return
    
    # Only process messages from the source chat
    if str(update.effective_chat.id) != SOURCE_CHAT_ID:
        logger.info(f"❌ IGNORED: Not from source chat")
        return
    
    # Ignore messages that start with /nar or /soc (our own commands)
    if message_text.strip().startswith('/nar ') or message_text.strip().startswith('/soc '):
        logger.info(f"❌ IGNORED: Our own command message")
        return
    
    # Find all Solana addresses in the message
    solana_addresses = re.findall(SOLANA_ADDRESS_PATTERN, message_text)
    
    if solana_addresses:
        # Remove duplicates while preserving order
        unique_addresses = list(dict.fromkeys(solana_addresses))
        
        logger.info(f"✅ Found {len(unique_addresses)} unique address(es)")
        
        # Process each unique address
        for idx, address in enumerate(unique_addresses, 1):
            
            try:
                # Send /nar message
                nar_message = f"/nar {address}"
                
                nar_result = await context.bot.send_message(
                    chat_id=DESTINATION_CHAT_ID,
                    text=nar_message
                )
                logger.info(f"✅ Sent /nar (message_id: {nar_result.message_id})")
                
                # Delay
                await asyncio.sleep(1)
                
                # Send /soc message
                soc_message = f"/soc {address}"
                
                soc_result = await context.bot.send_message(
                    chat_id=DESTINATION_CHAT_ID,
                    text=soc_message
                )
                logger.info(f"✅ Sent /soc (message_id: {soc_result.message_id})")
                
                # Delay between addresses
                if idx < len(unique_addresses):
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ ERROR: {e}")
    else:
        logger.info(f"❌ No Solana addresses found")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    
    # Validate environment variables
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    if not SOURCE_CHAT_ID:
        logger.error("SOURCE_CHAT_ID not found in environment variables")
        return
    
    if not DESTINATION_CHAT_ID:
        logger.error("DESTINATION_CHAT_ID not found in environment variables")
        return
    
    logger.info("Starting Solana Address Forwarder Bot...")
    logger.info(f"Monitoring chat: {SOURCE_CHAT_ID}")
    logger.info(f"Forwarding to: {DESTINATION_CHAT_ID}")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add message handler
    application.add_handler(MessageHandler(
        filters.TEXT | filters.CAPTION,
        handle_message
    ))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
