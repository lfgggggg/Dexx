"""
Event types and data structures for streaming
"""

from enum import Enum
from typing import TypedDict, Optional, Union


class EventType(Enum):
    """Event types for streaming"""
    # Bonding Curve events
    CREATE = "CurveCreate(address,address,address,string,string,string,uint256,uint256,uint256)"
    BUY = "CurveBuy(address,address,uint256,uint256)"
    SELL = "CurveSell(address,address,uint256,uint256)"

    SWAP = "Swap(address,address,int256,int256,uint160,uint128,int24)"
    MINT = "Mint(address,address,int24,int24,uint128,uint256,uint256)"
    BURN = "Burn(address,int24,int24,uint128,uint256,uint256)"


class CurveEvent(TypedDict):
    """Bonding Curve event structure"""
    eventName: str          # "BUY" or "SELL"
    blockNumber: int        # Block number
    transactionHash: str    # Transaction hash
    trader: str            # Buyer/Seller address
    token: str             # Token address
    amountIn: int          # Amount in (MON for buy, tokens for sell)
    amountOut: int         # Amount out (tokens for buy, MON for sell)


class DexSwapEvent(TypedDict):
    """DEX Swap event structure"""
    eventName: str          # "Swap"
    blockNumber: int        # Block number
    transactionHash: str    # Transaction hash
    pool: str              # Pool address
    sender: str            # Sender address
    recipient: str         # Recipient address
    amount0: int           # Token0 amount (can be negative)
    amount1: int           # Token1 amount (can be negative)
    sqrtPriceX96: int      # Square root price
    liquidity: int         # Liquidity
    tick: int              # Price tick


