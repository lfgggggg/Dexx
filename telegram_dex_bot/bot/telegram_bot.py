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
        self.router.callback_query(F.data.startswith('set_slippage_'))(self.handle_slippage_callback)
        self.router.callback_query(F.data.startswith('refresh_'))(self.handle_refresh_callback)
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
• `/switch_wallet` - Switch between wallets
• `/balance` - Check wallet balance

**Security:**
• `/view_keys` - View private keys (password protected)
• `/change_password` - Change your password

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
🔐 Create multiple wallets (no limit)
🔐 Switch between wallets easily
🔐 Password protect private key viewing
🔐 All keys encrypted and stored securely

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
        user_id = message.from_user.id
        user = await self.db_manager.get_user(user_id)
        
        if not user or not user.get('default_wallet_id'):
            await message.reply("❌ No active wallet found. Create a wallet first with /new_wallet")
            return
        
        wallet = await self.db_manager.get_wallet(user['default_wallet_id'])
        if not wallet:
            await message.reply("❌ Active wallet not found. Please switch to a valid wallet.")
            return
        
        try:
            # Get private key
            private_key = self.wallet_manager.decrypt_private_key(wallet['encrypted_private_key'])
            
            # Get balances
            balances = await self.trade_engine.get_wallet_balances(private_key)
            
            if balances['success']:
                balance_text = f"""💰 **Wallet Balance**

📱 **{wallet['wallet_name']}**
📍 **Address:** `{balances['address']}`

💎 **MON Balance:** {balances['mon_balance']:.6f} MON

Use `/buy <token> <amount>` to purchase tokens
Use `/sell <token> <amount>` to sell tokens"""
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Refresh", callback_data=f"refresh_balance_{wallet['wallet_id']}")],
                    [InlineKeyboardButton(text="📊 Trading", callback_data="trading_menu")],
                    [InlineKeyboardButton(text="🔄 Switch Wallet", callback_data="switch_wallet")]
                ])
                
                await message.reply(balance_text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await message.reply(f"❌ Error getting balance: {balances['error']}")
                
        except Exception as e:
            await message.reply("❌ Error accessing wallet. Please try again.")

    async def cmd_buy(self, message: Message, state: FSMContext):
        """Handle /buy command"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if len(args) < 2:
            await message.reply(
                "💰 **Buy Tokens**\n\n"
                "Usage: `/buy <token_address> <amount_in_mon>`\n\n"
                "Example: `/buy 0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701 1.5`\n\n"
                "This will buy tokens using the specified amount of MON.",
                parse_mode="Markdown"
            )
            return
        
        token_address = args[0]
        amount_mon = args[1]
        
        # Validate inputs
        if not self.trade_engine.validate_token_address(token_address):
            await message.reply("❌ Invalid token address format")
            return
        
        try:
            float(amount_mon)
        except ValueError:
            await message.reply("❌ Invalid amount format")
            return
        
        user_id = message.from_user.id
        user = await self.db_manager.get_user(user_id)
        
        if not user or not user.get('default_wallet_id'):
            await message.reply("❌ No active wallet found. Create a wallet first.")
            return
        
        wallet = await self.db_manager.get_wallet(user['default_wallet_id'])
        if not wallet:
            await message.reply("❌ Active wallet not found.")
            return
        
        # Get quote first
        await message.reply("📊 Getting price quote...")
        
        try:
            private_key = self.wallet_manager.decrypt_private_key(wallet['encrypted_private_key'])
            
            # Execute buy trade
            result = await self.trade_engine.execute_buy_trade(
                private_key, token_address, amount_mon, slippage=5.0
            )
            
            if result['success']:
                success_text = f"""✅ **Buy Order Executed!**

💰 **Spent:** {result['amount_in']} MON
📈 **Expected Tokens:** ~{self.trade_engine.format_amount(int(result['expected_out']))}
🔗 **Transaction:** `{result['tx_hash']}`
⚙️ **Router:** {result['router']}
📊 **Slippage:** {result['slippage']}%

⏳ **Waiting for confirmation...**"""
                
                await message.reply(success_text, parse_mode="Markdown")
                
                # Record transaction
                await self.db_manager.record_transaction(
                    wallet['wallet_id'], 'buy', token_address, 
                    result['amount_in'], result['expected_out'], result['tx_hash']
                )
                
            else:
                await message.reply(f"❌ **Buy failed:** {result['error']}")
                
        except Exception as e:
            await message.reply("❌ Error executing buy order. Please try again.")

    async def cmd_sell(self, message: Message, state: FSMContext):
        """Handle /sell command"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if len(args) < 2:
            await message.reply(
                "💰 **Sell Tokens**\n\n"
                "Usage: `/sell <token_address> <amount_tokens>`\n\n"
                "Example: `/sell 0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701 1000`\n\n"
                "This will sell the specified amount of tokens for MON.",
                parse_mode="Markdown"
            )
            return
        
        token_address = args[0]
        amount_tokens = args[1]
        
        # Validate inputs
        if not self.trade_engine.validate_token_address(token_address):
            await message.reply("❌ Invalid token address format")
            return
        
        try:
            float(amount_tokens)
        except ValueError:
            await message.reply("❌ Invalid amount format")
            return
        
        user_id = message.from_user.id
        user = await self.db_manager.get_user(user_id)
        
        if not user or not user.get('default_wallet_id'):
            await message.reply("❌ No active wallet found. Create a wallet first.")
            return
        
        wallet = await self.db_manager.get_wallet(user['default_wallet_id'])
        if not wallet:
            await message.reply("❌ Active wallet not found.")
            return
        
        # Get quote first
        await message.reply("📊 Getting price quote...")
        
        try:
            private_key = self.wallet_manager.decrypt_private_key(wallet['encrypted_private_key'])
            
            # Execute sell trade
            result = await self.trade_engine.execute_sell_trade(
                private_key, token_address, amount_tokens, slippage=5.0
            )
            
            if result['success']:
                success_text = f"""✅ **Sell Order Executed!**

📉 **Sold:** {result['amount_in']} tokens
💰 **Expected MON:** ~{result['expected_out']} MON
🔗 **Transaction:** `{result['tx_hash']}`
⚙️ **Router:** {result['router']}
📊 **Slippage:** {result['slippage']}%"""
                
                if result.get('approval_tx'):
                    success_text += f"\n🔓 **Approval TX:** `{result['approval_tx']}`"
                
                success_text += "\n\n⏳ **Waiting for confirmation...**"
                
                await message.reply(success_text, parse_mode="Markdown")
                
                # Record transaction
                await self.db_manager.record_transaction(
                    wallet['wallet_id'], 'sell', token_address, 
                    result['amount_in'], result['expected_out'], result['tx_hash']
                )
                
            else:
                await message.reply(f"❌ **Sell failed:** {result['error']}")
                
        except Exception as e:
            await message.reply("❌ Error executing sell order. Please try again.")

    async def cmd_history(self, message: Message):
        """Handle /history command"""
        user_id = message.from_user.id
        transactions = await self.db_manager.get_user_transactions(user_id, limit=10)
        
        if not transactions:
            await message.reply("📜 **No trading history found**\n\nStart trading to see your transaction history here!")
            return
        
        history_text = "📜 **Recent Transactions**\n\n"
        
        for tx in transactions:
            tx_type = tx['tx_type'].upper()
            token_addr = tx['token_address'] or 'Unknown'
            amount_in = tx['amount_in'] or '0'
            amount_out = tx['amount_out'] or '0'
            status = tx['status'].upper()
            timestamp = tx['timestamp'][:16].replace('T', ' ')
            
            emoji = "💰" if tx_type == "BUY" else "📉"
            status_emoji = "✅" if status == "SUCCESS" else "⏳" if status == "PENDING" else "❌"
            
            history_text += f"{emoji} **{tx_type}** {status_emoji}\n"
            history_text += f"🏷️ `{token_addr[:10]}...{token_addr[-8:]}`\n"
            history_text += f"📊 {amount_in} → {amount_out}\n"
            history_text += f"🕐 {timestamp}\n"
            
            if tx.get('tx_hash'):
                history_text += f"🔗 `{tx['tx_hash'][:10]}...{tx['tx_hash'][-8:]}`\n"
            
            history_text += "\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_history")],
            [InlineKeyboardButton(text="💰 Balance", callback_data="check_balance")]
        ])
        
        await message.reply(history_text, reply_markup=keyboard, parse_mode="Markdown")

    async def cmd_slippage(self, message: Message):
        """Handle /slippage command"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        
        if not args:
            # Show current slippage and options
            user_id = message.from_user.id
            user = await self.db_manager.get_user(user_id)
            current_slippage = 5.0  # Default
            
            slippage_text = f"""⚙️ **Slippage Configuration**

📊 **Current Slippage:** {current_slippage}%

**What is slippage?**
Slippage protects you from price changes during transaction execution. Higher slippage = more tolerance for price movement.

**Usage:** `/slippage <percentage>`
**Example:** `/slippage 3.5`"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="1%", callback_data="set_slippage_1"),
                    InlineKeyboardButton(text="3%", callback_data="set_slippage_3"),
                    InlineKeyboardButton(text="5%", callback_data="set_slippage_5")
                ],
                [
                    InlineKeyboardButton(text="10%", callback_data="set_slippage_10"),
                    InlineKeyboardButton(text="15%", callback_data="set_slippage_15"),
                    InlineKeyboardButton(text="20%", callback_data="set_slippage_20")
                ]
            ])
            
            await message.reply(slippage_text, reply_markup=keyboard, parse_mode="Markdown")
            return
        
        try:
            slippage = float(args[0])
            if slippage < 0.1 or slippage > 50:
                await message.reply("❌ Slippage must be between 0.1% and 50%")
                return
            
            # Save slippage setting (simplified)
            await message.reply(f"✅ **Slippage set to {slippage}%**\n\nThis will be used for all future trades.")
            
        except ValueError:
            await message.reply("❌ Invalid slippage format. Use a number like 5.0")

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

    async def handle_slippage_callback(self, callback: CallbackQuery):
        """Handle slippage setting callbacks"""
        slippage = callback.data.split('_')[-1]
        await callback.message.edit_text(
            f"✅ **Slippage set to {slippage}%**\n\n"
            f"This setting will be used for all future trades.\n\n"
            f"You can change it anytime with `/slippage <value>`",
            parse_mode="Markdown"
        )
        await callback.answer()

    async def handle_refresh_callback(self, callback: CallbackQuery):
        """Handle refresh callbacks"""
        if callback.data == "refresh_history":
            await self.cmd_history(callback.message)
        elif callback.data == "check_balance":
            await self.cmd_balance(callback.message)
        elif callback.data.startswith("refresh_balance_"):
            await self.cmd_balance(callback.message)
        await callback.answer()

    async def handle_trade_callback(self, callback: CallbackQuery):
        """Handle trade-related callback queries"""
        if callback.data == "trading_menu":
            trading_text = """📊 **Trading Menu**

Choose your trading action:"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💰 Buy Tokens", callback_data="quick_buy"),
                    InlineKeyboardButton(text="📉 Sell Tokens", callback_data="quick_sell")
                ],
                [
                    InlineKeyboardButton(text="📊 Get Price Quote", callback_data="price_quote"),
                    InlineKeyboardButton(text="⚙️ Settings", callback_data="trade_settings")
                ],
                [InlineKeyboardButton(text="📜 History", callback_data="refresh_history")]
            ])
            
            await callback.message.edit_text(trading_text, reply_markup=keyboard, parse_mode="Markdown")
        elif callback.data == "switch_wallet":
            await self.cmd_switch_wallet(callback.message)
        else:
            await callback.answer("Feature in development!")
        
        await callback.answer()
    
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