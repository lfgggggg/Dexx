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
from nadfun_sdk import Trade, Token, BuyParams, SellParams, calculate_slippage, parseMon

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
            # Create trade instance with dummy private key for quotes
            dummy_private_key = "0x" + "1" * 64
            trade = Trade(self.rpc_url, dummy_private_key)
            
            # Try to get quote - handle bonding curve vs DEX routing
            try:
                quote = await trade.get_amount_out(token_address, amount_in, is_buy=is_buy)
                
                return {
                    'token_address': token_address,
                    'amount_in': str(amount_in),
                    'amount_out': str(quote.amount),
                    'router': quote.router,
                    'is_buy': is_buy,
                    'success': True
                }
            except Exception as quote_error:
                # If bonding curve fails, this might be a regular ERC20 token
                if "BONDING_CURVE" in str(quote_error) or "INVALID_INPUTS" in str(quote_error):
                    return {
                        'success': False,
                        'error': 'This token may not be available on Nad.fun bonding curve. Try using a token that was launched on Nad.fun platform.',
                        'token_address': token_address,
                        'error_type': 'not_nadfun_token'
                    }
                else:
                    raise quote_error
                    
        except Exception as e:
            logger.error(f"Failed to get token price for {token_address}: {e}")
            return {
                'success': False,
                'error': str(e),
                'token_address': token_address
            }
    
    async def execute_buy_trade(self, private_key: str, token_address: str, 
                               amount_in_mon: str, slippage: float = 5.0) -> Dict[str, Any]:
        """Execute a buy trade"""
        try:
            # Initialize trade with user's private key
            trade = Trade(self.rpc_url, private_key)
            
            # Parse MON amount
            amount_in = parseMon(amount_in_mon)
            
            # Get quote
            quote = await trade.get_amount_out(token_address, amount_in, is_buy=True)
            
            # Calculate minimum tokens with slippage
            min_tokens = calculate_slippage(quote.amount, slippage)
            
            # Create buy parameters
            buy_params = BuyParams(
                token=token_address,
                amount_in=amount_in,
                amount_out_min=min_tokens,
                to=trade.address,
                deadline=None,
                nonce=None,
                gas=None,
                gas_price=None,
            )
            
            # Execute buy
            tx_hash = await trade.buy(buy_params, quote.router)
            
            return {
                'tx_hash': f"0x{tx_hash}",
                'amount_in': amount_in_mon,
                'expected_out': str(quote.amount),
                'min_amount_out': str(min_tokens),
                'router': quote.router,
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
    
    async def execute_sell_trade(self, private_key: str, token_address: str, 
                                amount_tokens: str, slippage: float = 5.0) -> Dict[str, Any]:
        """Execute a sell trade"""
        try:
            # Initialize trade and token with user's private key
            trade = Trade(self.rpc_url, private_key)
            token = Token(self.rpc_url, private_key)
            
            # Parse token amount
            amount_to_sell = parseMon(amount_tokens)
            
            # Check token balance
            balance = await token.get_balance(token_address)
            if balance == 0:
                return {
                    'success': False,
                    'error': 'No tokens to sell',
                    'trade_type': 'sell'
                }
            
            # Get quote
            quote = await trade.get_amount_out(token_address, amount_to_sell, is_buy=False)
            
            # Calculate minimum MON with slippage
            min_mon = calculate_slippage(quote.amount, slippage)
            
            # Check and approve if needed
            approval_tx = await token.check_and_approve(
                token_address,
                quote.router,
                amount_to_sell
            )
            
            if approval_tx:
                # Wait for approval
                await token.wait_for_transaction(approval_tx)
            
            # Create sell parameters
            sell_params = SellParams(
                token=token_address,
                amount_in=amount_to_sell,
                amount_out_min=min_mon,
                to=trade.address,
                deadline=None,
                nonce=None,
                gas=None,
                gas_price=None,
            )
            
            # Execute sell
            tx_hash = await trade.sell(sell_params, quote.router)
            
            return {
                'tx_hash': f"0x{tx_hash}",
                'amount_in': amount_tokens,
                'expected_out': str(quote.amount),
                'min_amount_out': str(min_mon),
                'router': quote.router,
                'approval_tx': approval_tx,
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
    
    async def get_wallet_balances(self, private_key: str, token_addresses: list = None) -> Dict[str, Any]:
        """Get wallet balances for MON and tokens"""
        try:
            # Initialize token with user's private key
            token = Token(self.rpc_url, private_key)
            account = Account.from_key(private_key)
            
            # Get MON balance
            mon_balance_wei = self.web3.eth.get_balance(account.address)
            mon_balance = self.web3.from_wei(mon_balance_wei, 'ether')
            
            balances = {
                'address': account.address,
                'mon_balance': float(mon_balance),
                'tokens': {},
                'success': True
            }
            
            # Get token balances if addresses provided
            if token_addresses:
                for token_addr in token_addresses:
                    try:
                        token_balance = await token.get_balance(token_addr)
                        balances['tokens'][token_addr] = str(token_balance)
                    except Exception as e:
                        logger.error(f"Failed to get balance for token {token_addr}: {e}")
                        balances['tokens'][token_addr] = '0'
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get wallet balances: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def wait_for_transaction(self, private_key: str, tx_hash: str, timeout: int = 60) -> Dict[str, Any]:
        """Wait for transaction confirmation"""
        try:
            trade = Trade(self.rpc_url, private_key)
            receipt = await trade.wait_for_transaction(tx_hash, timeout=timeout)
            
            return {
                'tx_hash': tx_hash,
                'status': receipt.get('status', 0),
                'gas_used': receipt.get('gasUsed', 0),
                'block_number': receipt.get('blockNumber', 0),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to wait for transaction {tx_hash}: {e}")
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