"""
Configuration settings for the Telegram DEX Bot
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class BotSettings:
    """Bot configuration settings"""
    
    # Default trading settings
    default_slippage: float = 5.0
    default_gas_limit: int = 500000
    max_slippage: float = 50.0
    min_slippage: float = 0.1
    
    # Transaction settings
    tx_timeout: int = 300  # 5 minutes
    max_retries: int = 3
    
    # Security settings
    max_wallets_per_user: int = 10
    
    # UI settings
    max_history_items: int = 20
    
    @classmethod
    def from_env(cls) -> 'BotSettings':
        """Create settings from environment variables"""
        return cls(
            default_slippage=float(os.getenv('DEFAULT_SLIPPAGE', '5.0')),
            default_gas_limit=int(os.getenv('DEFAULT_GAS_LIMIT', '500000')),
            max_slippage=float(os.getenv('MAX_SLIPPAGE', '50.0')),
            min_slippage=float(os.getenv('MIN_SLIPPAGE', '0.1')),
            tx_timeout=int(os.getenv('TX_TIMEOUT', '300')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            max_wallets_per_user=int(os.getenv('MAX_WALLETS_PER_USER', '10')),
            max_history_items=int(os.getenv('MAX_HISTORY_ITEMS', '20'))
        )