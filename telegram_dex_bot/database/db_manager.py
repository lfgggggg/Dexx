"""
Database Manager for Telegram DEX Bot
Handles SQLite database operations for users, wallets, transactions, and configurations
"""

import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the bot"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def initialize(self):
        """Initialize database and create tables if they don't exist"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await self._create_tables(db)
                await db.commit()
            logger.info(f"Database initialized successfully at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """Create all necessary tables"""
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                default_wallet_id INTEGER,
                password TEXT,
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Wallets table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wallet_name TEXT,
                address TEXT NOT NULL,
                encrypted_private_key TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Transactions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id INTEGER NOT NULL,
                tx_hash TEXT,
                tx_type TEXT NOT NULL,
                token_address TEXT,
                amount_in TEXT,
                amount_out TEXT,
                gas_used TEXT,
                gas_price TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_id) REFERENCES wallets (wallet_id)
            )
        """)
        
        # User configurations table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                config_type TEXT NOT NULL,
                config_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Stop loss and take profit orders
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_id INTEGER NOT NULL,
                token_address TEXT NOT NULL,
                order_type TEXT NOT NULL,
                trigger_price TEXT NOT NULL,
                amount TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_id) REFERENCES wallets (wallet_id)
            )
        """)
        
        # Create indexes for better performance
        await db.execute("CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_wallet_id ON transactions(wallet_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_wallet_token ON orders(wallet_id, token_address)")
    
    async def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Create a new user record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, first_name, last_name))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def create_wallet(self, user_id: int, wallet_name: str, address: str, encrypted_private_key: str) -> Optional[int]:
        """Create a new wallet for user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO wallets (user_id, wallet_name, address, encrypted_private_key)
                    VALUES (?, ?, ?, ?)
                """, (user_id, wallet_name, address, encrypted_private_key))
                wallet_id = cursor.lastrowid
                
                # Set as default wallet if user has no default
                user = await self.get_user(user_id)
                if user and not user.get('default_wallet_id'):
                    await db.execute("UPDATE users SET default_wallet_id = ? WHERE user_id = ?", 
                                   (wallet_id, user_id))
                
                await db.commit()
                return wallet_id
        except Exception as e:
            logger.error(f"Failed to create wallet for user {user_id}: {e}")
            return None
    
    async def get_user_wallets(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all wallets for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM wallets WHERE user_id = ? AND is_active = TRUE
                    ORDER BY created_at DESC
                """, (user_id,)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get wallets for user {user_id}: {e}")
            return []
    
    async def get_wallet(self, wallet_id: int) -> Optional[Dict[str, Any]]:
        """Get specific wallet information"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT * FROM wallets WHERE wallet_id = ?", (wallet_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get wallet {wallet_id}: {e}")
            return None
    
    async def record_transaction(self, wallet_id: int, tx_type: str, token_address: str = None,
                               amount_in: str = None, amount_out: str = None, tx_hash: str = None) -> Optional[int]:
        """Record a new transaction"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO transactions (wallet_id, tx_type, token_address, amount_in, amount_out, tx_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (wallet_id, tx_type, token_address, amount_in, amount_out, tx_hash))
                tx_id = cursor.lastrowid
                await db.commit()
                return tx_id
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")
            return None
    
    async def update_transaction_status(self, tx_id: int, status: str, tx_hash: str = None, error_message: str = None):
        """Update transaction status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if tx_hash:
                    await db.execute("""
                        UPDATE transactions SET status = ?, tx_hash = ?, error_message = ?
                        WHERE tx_id = ?
                    """, (status, tx_hash, error_message, tx_id))
                else:
                    await db.execute("""
                        UPDATE transactions SET status = ?, error_message = ?
                        WHERE tx_id = ?
                    """, (status, error_message, tx_id))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update transaction {tx_id}: {e}")
    
    async def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT t.*, w.address as wallet_address
                    FROM transactions t
                    JOIN wallets w ON t.wallet_id = w.wallet_id
                    WHERE w.user_id = ?
                    ORDER BY t.timestamp DESC
                    LIMIT ?
                """, (user_id, limit)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get transactions for user {user_id}: {e}")
            return []
    
    async def set_user_password(self, user_id: int, password: str) -> bool:
        """Set or update user password"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (password, user_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to set password for user {user_id}: {e}")
            return False
    
    async def set_default_wallet(self, user_id: int, wallet_id: int) -> bool:
        """Set user's default wallet"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE users SET default_wallet_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (wallet_id, user_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to set default wallet for user {user_id}: {e}")
            return False