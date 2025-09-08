"""
Trade Engine for Telegram DEX Bot
Handles trading operations using Nad.fun SDK
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from web3 import Web3
from eth_account import Account

# Import Nad.fun SDK
from nadfun_sdk import Trade, Token

logger = logging.getLogger(__name__)

class TradeEngine:
    """Handles all trading operations using Nad.fun SDK"""
    
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Verify connection
        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {rpc_url}")
        
        logger.info(f"Trade engine initialized with RPC: {rpc_url}")
    
    async def get_token_price(self, token_address: str, amount_in: int = 10**18, is_buy: bool = True) -> Dict[str, Any]:
        """Get token price quote from Nad.fun"""
        try:
            # Get amount out for the given input
            amount_out = await Trade.get_amount_out(
                token=token_address,
                amount_in=amount_in,
                is_buy=is_buy
            )
            
            return {
                'token_address': token_address,
                'amount_in': str(amount_in),
                'amount_out': str(amount_out),
                'is_buy': is_buy,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get token price for {token_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_buy_trade(self, account: Account, token_address: str, 
                               amount_in: int, slippage: float = 5.0) -> Dict[str, Any]:
        """Execute a buy trade"""
        try:
            # Get expected amount out
            quote = await self.get_token_price(token_address, amount_in, is_buy=True)
            if not quote['success']:
                return quote
            
            expected_out = int(quote['amount_out'])
            min_amount_out = int(expected_out * (100 - slippage) / 100)
            
            # Execute trade
            result = await Trade.buy(
                token=token_address,
                amount_in=amount_in,
                min_amount_out=min_amount_out,
                account=account
            )
            
            return {
                'tx_hash': result.tx_hash if hasattr(result, 'tx_hash') else None,
                'amount_in': str(amount_in),
                'expected_out': str(expected_out),
                'min_amount_out': str(min_amount_out),
                'slippage': slippage,
                'success': True,
                'trade_type': 'buy'
            }
            
        except Exception as e:
            logger.error(f"Failed to execute buy trade: {e}")
            return {
                'success': False,
                'error': str(e),
                'trade_type': 'buy'
            }
    
    async def execute_sell_trade(self, account: Account, token_address: str, 
                                amount_in: int, slippage: float = 5.0) -> Dict[str, Any]:
        """Execute a sell trade"""
        try:
            # Get expected amount out
            quote = await self.get_token_price(token_address, amount_in, is_buy=False)
            if not quote['success']:
                return quote
            
            expected_out = int(quote['amount_out'])
            min_amount_out = int(expected_out * (100 - slippage) / 100)
            
            # Execute trade
            result = await Trade.sell(
                token=token_address,
                amount_in=amount_in,
                min_amount_out=min_amount_out,
                account=account
            )
            
            return {
                'tx_hash': result.tx_hash if hasattr(result, 'tx_hash') else None,
                'amount_in': str(amount_in),
                'expected_out': str(expected_out),
                'min_amount_out': str(min_amount_out),
                'slippage': slippage,
                'success': True,
                'trade_type': 'sell'
            }
            
        except Exception as e:
            logger.error(f"Failed to execute sell trade: {e}")
            return {
                'success': False,
                'error': str(e),
                'trade_type': 'sell'
            }
    
    async def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Get token information"""
        try:
            # Get token details using Nad.fun SDK
            token_info = await Token.get_token_info(token_address)
            
            return {
                'address': token_address,
                'name': token_info.get('name', 'Unknown'),
                'symbol': token_info.get('symbol', 'UNKNOWN'),
                'decimals': token_info.get('decimals', 18),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get token info for {token_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_amount(self, amount_str: str, decimals: int = 18) -> Optional[int]:
        """Parse amount string to wei/smallest unit"""
        try:
            if amount_str.lower().endswith('eth'):
                amount_str = amount_str[:-3].strip()
                amount = Decimal(amount_str)
                return int(amount * (10 ** decimals))
            else:
                amount = Decimal(amount_str)
                return int(amount * (10 ** decimals))
        except Exception as e:
            logger.error(f"Failed to parse amount {amount_str}: {e}")
            return None
    
    def format_amount(self, amount: int, decimals: int = 18) -> str:
        """Format amount from wei to human readable"""
        try:
            amount_decimal = Decimal(amount) / (10 ** decimals)
            return f"{amount_decimal:.6f}".rstrip('0').rstrip('.')
        except Exception as e:
            logger.error(f"Failed to format amount {amount}: {e}")
            return str(amount)
    
    def validate_token_address(self, address: str) -> bool:
        """Validate token address format"""
        try:
            return self.web3.is_address(address)
        except:
            return False