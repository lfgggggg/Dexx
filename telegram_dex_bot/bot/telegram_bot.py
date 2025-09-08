"""
Telegram Bot for DEX Trading
Main bot class that handles Telegram interactions and coordinates trading operations
"""

import logging
from typing import Optional, Dict, Any
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database.db_manager import DatabaseManager
from wallet.wallet_manager import WalletManager
from trade.trade_engine import TradeEngine
from config.settings import BotSettings

logger = logging.getLogger(__name__)

class WalletStates(StatesGroup):
    """States for wallet import workflow"""
    waiting_for_private_key = State()
    waiting_for_wallet_name = State()
    waiting_for_password = State()
    waiting_for_new_password = State()
    waiting_for_password_confirmation = State()

class TradeStates(StatesGroup):
    """States for trading workflows"""
    waiting_for_token_address = State()
    waiting_for_amount = State()
    waiting_for_confirmation = State()

class TelegramDEXBot:
    """Main Telegram bot class for DEX trading"""
    
    def __init__(self, bot_token: str, rpc_url: str, db_manager: DatabaseManager):
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db_manager = db_manager
        self.wallet_manager = WalletManager()
        self.trade_engine = TradeEngine(rpc_url)
        self.settings = BotSettings()
        
        # Setup router and handlers
        self.router = Router()
        self._setup_handlers()
        self.dp.include_router(self.router)
        
        logger.info("Telegram DEX Bot initialized")
    
    def _setup_handlers(self):
        """Setup all message and callback handlers"""
        
        # Command handlers
        self.router.message(Command('start'))(self.cmd_start)
        self.router.message(Command('help'))(self.cmd_help)
        self.router.message(Command('wallet'))(self.cmd_wallet)
        self.router.message(Command('new_wallet'))(self.cmd_new_wallet)
        self.router.message(Command('import'))(self.cmd_import)
        self.router.message(Command('balance'))(self.cmd_balance)
        self.router.message(Command('buy'))(self.cmd_buy)
        self.router.message(Command('sell'))(self.cmd_sell)
        self.router.message(Command('price'))(self.cmd_price)
        self.router.message(Command('history'))(self.cmd_history)
        self.router.message(Command('slippage'))(self.cmd_slippage)
        self.router.message(Command('switch_wallet'))(self.cmd_switch_wallet)
        self.router.message(Command('view_keys'))(self.cmd_view_keys)
        self.router.message(Command('change_password'))(self.cmd_change_password)
        
        # State handlers
        self.router.message(WalletStates.waiting_for_private_key)(self.process_private_key)
        self.router.message(WalletStates.waiting_for_wallet_name)(self.process_wallet_name)
        self.router.message(WalletStates.waiting_for_password)(self.process_password)
        self.router.message(WalletStates.waiting_for_new_password)(self.process_new_password)
        self.router.message(WalletStates.waiting_for_password_confirmation)(self.process_password_confirmation)
        
        # Callback handlers
        self.router.callback_query(F.data.startswith('wallet_'))(self.handle_wallet_callback)
        self.router.callback_query(F.data.startswith('switch_to_'))(self.handle_switch_callback)
        self.router.callback_query(F.data.startswith('trade_'))(self.handle_trade_callback)
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Handle /start command"""
        await state.clear()
        
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        # Create user record
        await self.db_manager.create_user(user_id, username, first_name, last_name)
        
        welcome_text = f"""🚀 **Welcome to DEX Trading Bot!**
        
Hi {first_name}! I'm your personal trading assistant for Nad.fun DEX on Monad.

**What I can do:**
🔹 Create and manage wallets securely
🔹 Buy and sell tokens instantly
🔹 Get real-time price quotes
🔹 Track your trading history
🔹 Set custom slippage and risk management

**Get started:**
• `/wallet` - Manage your wallets
• `/price <token>` - Get token price
• `/buy <token> <amount>` - Buy tokens
• `/sell <token> <amount>` - Sell tokens

**Security:** Your private keys are encrypted and stored securely. I never have access to your funds.

Type `/help` for detailed commands."""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Create Wallet", callback_data="wallet_create")],
            [InlineKeyboardButton(text="📥 Import Wallet", callback_data="wallet_import")],
            [InlineKeyboardButton(text="📊 View Wallets", callback_data="wallet_list")]
        ])
        
        await message.reply(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    
    async def cmd_help(self, message: Message):
        """Handle /help command"""
        help_text = """📚 **Bot Commands Help**

**Wallet Management:**
• `/wallet` - View and manage wallets
• `/new_wallet` - Create a new wallet
• `/import` - Import wallet from private key
• `/balance` - Check wallet balance

**Trading:**
• `/buy <token> <amount>` - Buy tokens
• `/sell <token> <amount>` - Sell tokens  
• `/price <token>` - Get token price quote

**Configuration:**
• `/slippage <percent>` - Set slippage tolerance
• `/history` - View trading history

**Examples:**
• `/price 0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701`
• `/buy 0x760...701 1`
• `/sell 0x760...701 0.5`
• `/slippage 3.0`

**Security Notes:**
🔐 Private keys are encrypted locally
🔐 Never share your private keys with anyone
🔐 Always verify contract addresses before trading

Need help? Just type your question!"""
        
        await message.reply(help_text, parse_mode="Markdown")
    
    async def cmd_wallet(self, message: Message):
        """Handle /wallet command"""
        user_id = message.from_user.id
        wallets = await self.db_manager.get_user_wallets(user_id)
        
        if not wallets:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Create Wallet", callback_data="wallet_create")],
                [InlineKeyboardButton(text="📥 Import Wallet", callback_data="wallet_import")]
            ])
            
            await message.reply(
                "💼 **No wallets found**\n\nCreate your first wallet to start trading!",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        wallet_text = "💼 **Your Wallets:**\n\n"
        keyboard_buttons = []
        
        for i, wallet in enumerate(wallets):
            wallet_text += f"{i+1}. **{wallet['wallet_name']}**\n"
            wallet_text += f"   `{wallet['address'][:10]}...{wallet['address'][-8:]}`\n"
            wallet_text += f"   Created: {wallet['created_at'][:10]}\n\n"
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📱 {wallet['wallet_name']}", 
                    callback_data=f"wallet_select_{wallet['wallet_id']}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🆕 New Wallet", callback_data="wallet_create"),
            InlineKeyboardButton(text="📥 Import", callback_data="wallet_import")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.reply(wallet_text, reply_markup=keyboard, parse_mode="Markdown")
    
    async def cmd_new_wallet(self, message: Message):
        """Handle /new_wallet command"""
        user_id = message.from_user.id
        
        # Create new wallet
        wallet_result = self.wallet_manager.create_wallet()
        
        if not wallet_result['success']:
            await message.reply(f"❌ Failed to create wallet: {wallet_result['error']}")
            return
        
        # Save to database
        wallet_id = await self.db_manager.create_wallet(
            user_id,
            wallet_result['wallet_name'],
            wallet_result['address'],
            wallet_result['encrypted_private_key']
        )
        
        if wallet_id:
            await message.reply(
                f"""✅ **Wallet Created Successfully!**

💼 **Wallet:** {wallet_result['wallet_name']}
📍 **Address:** `{wallet_result['address']}`

⚠️ **Important:** Your wallet has been encrypted and stored securely. Make sure to fund it with some ETH for gas fees before trading.

Use `/balance` to check your wallet balance.""",
                parse_mode="Markdown"
            )
        else:
            await message.reply("❌ Failed to save wallet to database.")
    
    async def cmd_price(self, message: Message):
        """Handle /price command"""
        try:
            # Extract token address from command
            args = message.text.split()[1:] if len(message.text.split()) > 1 else []
            
            if not args:
                await message.reply("❌ Please provide a token address\n\nExample: `/price 0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701`", parse_mode="Markdown")
                return
            
            token_address = args[0]
            
            if not self.trade_engine.validate_token_address(token_address):
                await message.reply("❌ Invalid token address format")
                return
            
            # Get price quote
            quote = await self.trade_engine.get_token_price(token_address)
            
            if not quote['success']:
                await message.reply(f"❌ Failed to get price: {quote['error']}")
                return
            
            # Format response
            amount_in_eth = self.trade_engine.format_amount(int(quote['amount_in']))
            amount_out = self.trade_engine.format_amount(int(quote['amount_out']))
            
            price_text = f"""📊 **Token Price Quote**

🔗 **Token:** `{token_address[:10]}...{token_address[-8:]}`
💰 **Price:** {amount_in_eth} ETH = {amount_out} tokens

**Trading:**
• `/buy {token_address[:10]}... <amount>` - Buy tokens
• `/sell {token_address[:10]}... <amount>` - Sell tokens"""
            
            await message.reply(price_text, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in price command: {e}")
            await message.reply("❌ Error getting price quote")
    
    async def cmd_import(self, message: Message, state: FSMContext):
        """Handle /import command"""
        await message.reply("🔐 **Import Wallet**\n\nPlease send your private key (it will be encrypted and stored securely):")
        await state.set_state(WalletStates.waiting_for_private_key)

    async def cmd_balance(self, message: Message):
        """Handle /balance command"""
        await message.reply("Balance checking feature coming soon!")

    async def cmd_buy(self, message: Message):
        """Handle /buy command"""
        await message.reply("Buy feature coming soon!")

    async def cmd_sell(self, message: Message):
        """Handle /sell command"""
        await message.reply("Sell feature coming soon!")

    async def cmd_history(self, message: Message):
        """Handle /history command"""
        await message.reply("History feature coming soon!")

    async def cmd_slippage(self, message: Message):
        """Handle /slippage command"""
        await message.reply("Slippage configuration coming soon!")

    async def cmd_switch_wallet(self, message: Message):
        """Handle /switch_wallet command"""
        user_id = message.from_user.id
        wallets = await self.db_manager.get_user_wallets(user_id)
        
        if not wallets:
            await message.reply("❌ No wallets found. Create a wallet first with /new_wallet")
            return
        
        if len(wallets) == 1:
            await message.reply("ℹ️ You only have one wallet. Create more wallets to switch between them.")
            return
        
        # Create inline keyboard with wallet options
        keyboard_buttons = []
        for wallet in wallets:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📱 {wallet['wallet_name']} ({wallet['address'][:10]}...)",
                    callback_data=f"switch_to_{wallet['wallet_id']}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.reply("🔄 **Choose wallet to switch to:**", reply_markup=keyboard, parse_mode="Markdown")

    async def cmd_view_keys(self, message: Message, state: FSMContext):
        """Handle /view_keys command - requires password"""
        await message.reply("🔐 **Enter your password to view private keys:**")
        await state.set_state(WalletStates.waiting_for_password)

    async def cmd_change_password(self, message: Message, state: FSMContext):
        """Handle /change_password command"""
        await message.reply("🔒 **Enter your current password:**")
        await state.set_state(WalletStates.waiting_for_new_password)

    # State processing methods
    async def process_private_key(self, message: Message, state: FSMContext):
        """Process private key input for wallet import"""
        try:
            private_key = message.text.strip()
            
            # Import wallet
            wallet_result = self.wallet_manager.import_wallet_from_private_key(private_key)
            
            if not wallet_result['success']:
                await message.reply(f"❌ Failed to import wallet: {wallet_result['error']}")
                await state.clear()
                return
            
            # Save to database
            user_id = message.from_user.id
            wallet_id = await self.db_manager.create_wallet(
                user_id,
                wallet_result['wallet_name'],
                wallet_result['address'],
                wallet_result['encrypted_private_key']
            )
            
            if wallet_id:
                await message.reply(
                    f"""✅ **Wallet Imported Successfully!**

💼 **Wallet:** {wallet_result['wallet_name']}
📍 **Address:** `{wallet_result['address']}`

Your wallet has been encrypted and stored securely.""",
                    parse_mode="Markdown"
                )
            else:
                await message.reply("❌ Failed to save wallet to database.")
            
            await state.clear()
            
        except Exception as e:
            await message.reply("❌ Error processing private key. Please try again.")
            await state.clear()

    async def process_wallet_name(self, message: Message, state: FSMContext):
        """Process wallet name input"""
        # This can be used for custom wallet naming
        await message.reply("Wallet naming feature coming soon!")
        await state.clear()

    async def process_password(self, message: Message, state: FSMContext):
        """Process password for viewing private keys"""
        password = message.text.strip()
        user_id = message.from_user.id
        
        # Check if user has set a password (simplified - in real app use proper password hashing)
        user = await self.db_manager.get_user(user_id)
        stored_password = user.get('password') if user else None
        
        if not stored_password:
            # First time setting password
            await self.db_manager.set_user_password(user_id, password)
            await message.reply("🔐 **Password set successfully!**\n\nNow showing your private keys:")
            await self.show_private_keys(message)
        elif stored_password == password:
            await self.show_private_keys(message)
        else:
            await message.reply("❌ **Incorrect password!**")
        
        await state.clear()

    async def process_new_password(self, message: Message, state: FSMContext):
        """Process new password setup"""
        await state.update_data(new_password=message.text.strip())
        await message.reply("🔒 **Confirm your new password:**")
        await state.set_state(WalletStates.waiting_for_password_confirmation)

    async def process_password_confirmation(self, message: Message, state: FSMContext):
        """Process password confirmation"""
        data = await state.get_data()
        new_password = data.get('new_password')
        confirmation = message.text.strip()
        
        if new_password == confirmation:
            user_id = message.from_user.id
            await self.db_manager.set_user_password(user_id, new_password)
            await message.reply("✅ **Password changed successfully!**")
        else:
            await message.reply("❌ **Passwords don't match. Please try again.**")
        
        await state.clear()

    async def show_private_keys(self, message: Message):
        """Show user's private keys (password protected)"""
        user_id = message.from_user.id
        wallets = await self.db_manager.get_user_wallets(user_id)
        
        if not wallets:
            await message.reply("❌ No wallets found.")
            return
        
        keys_text = "🔐 **Your Private Keys:**\n\n"
        for i, wallet in enumerate(wallets):
            try:
                decrypted_key = self.wallet_manager.decrypt_private_key(wallet['encrypted_private_key'])
                keys_text += f"{i+1}. **{wallet['wallet_name']}**\n"
                keys_text += f"   Address: `{wallet['address']}`\n"
                keys_text += f"   Private Key: `{decrypted_key}`\n\n"
            except Exception as e:
                keys_text += f"{i+1}. **{wallet['wallet_name']}** - ❌ Error decrypting\n\n"
        
        keys_text += "⚠️ **Security Warning:** Never share your private keys with anyone!"
        
        await message.reply(keys_text, parse_mode="Markdown")

    async def handle_wallet_callback(self, callback: CallbackQuery):
        """Handle wallet-related callback queries"""
        data = callback.data
        
        if data == "wallet_create":
            await self.cmd_new_wallet(callback.message)
        elif data == "wallet_import":
            await self.cmd_import(callback.message)
        elif data == "wallet_list":
            await self.cmd_wallet(callback.message)
        
        await callback.answer()
    
    async def handle_switch_callback(self, callback: CallbackQuery):
        """Handle wallet switching callbacks"""
        data = callback.data
        wallet_id = int(data.split('_')[-1])
        user_id = callback.from_user.id
        
        # Set as default wallet
        success = await self.db_manager.set_default_wallet(user_id, wallet_id)
        
        if success:
            wallet = await self.db_manager.get_wallet(wallet_id)
            if wallet:
                await callback.message.edit_text(
                    f"✅ **Switched to wallet:**\n\n"
                    f"📱 **{wallet['wallet_name']}**\n"
                    f"📍 `{wallet['address']}`\n\n"
                    f"This wallet is now your active trading wallet.",
                    parse_mode="Markdown"
                )
            else:
                await callback.message.edit_text("❌ Error switching wallet.")
        else:
            await callback.message.edit_text("❌ Failed to switch wallet.")
        
        await callback.answer()

    async def handle_trade_callback(self, callback: CallbackQuery):
        """Handle trade-related callback queries"""
        # Implement trade callbacks
        await callback.answer("Trade feature coming soon!")
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("Starting Telegram bot...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.bot.session.close()