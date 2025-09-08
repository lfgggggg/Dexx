"""
Type definitions for NADFUN SDK.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class BuyParams:
    """Parameters for buy transaction."""
    token: str
    amount_in: int
    amount_out_min: int
    to: str
    nonce: Optional[int] = None
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    deadline: Optional[int] = None

@dataclass
class SellParams:
    """Parameters for sell transaction."""
    token: str
    amount_in: int
    amount_out_min: int
    to: str
    nonce: Optional[int] = None
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    deadline: Optional[int] = None

@dataclass
class QuoteResult:
    """Result from quote functions."""
    router: str
    amount: int

@dataclass
class CurveData:
    """Bonding curve data."""
    reserve_mon: int
    reserve_token: int
    token_supply: int
    virtual_mon: int
    virtual_token: int
    k: int
    target_token_amount: int
    init_virtual_mon_reserve: int
    init_virtual_token_reserve: int

@dataclass
class TokenMetadata:
    """Token metadata information."""
    name: str
    symbol: str
    decimals: int
    total_supply: int
    address: str
