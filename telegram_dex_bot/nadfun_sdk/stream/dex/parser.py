"""
Common event parser for DEX swap events
"""

from typing import Optional, Dict, Any
from web3 import Web3
from eth_abi import decode
from ..utils import extract_address_from_topic, parse_log_data, format_tx_hash


def parse_swap_event(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse DEX Swap event log
    
    Args:
        log: Web3 log dict
    
    Returns:
        Parsed event dict with DexSwapEvent structure
    """
    try:
        topics = log.get("topics", [])
        if len(topics) < 3:
            return None
        
        # Parse indexed parameters (topics)
        # topics[1] = sender, topics[2] = recipient
        sender = "0x" + extract_address_from_topic(topics[1])
        recipient = "0x" + extract_address_from_topic(topics[2])
        
        # Parse non-indexed parameters (data)
        data_bytes = parse_log_data(log.get("data"))
        
        # Decode: [amount0, amount1, sqrtPriceX96, liquidity, tick]
        amount0, amount1, sqrt_price_x96, liquidity, tick = decode(
            ["int256", "int256", "uint160", "uint128", "int24"],
            data_bytes
        )
        
        # Get pool address
        pool_address = log.get("address")
        if hasattr(pool_address, 'hex'):
            pool_address = pool_address.hex()
        elif not pool_address.startswith('0x'):
            pool_address = '0x' + pool_address
        
        return {
            "eventName": "Swap",
            "blockNumber": log.get("blockNumber"),
            "transactionHash": "0x"+format_tx_hash(log.get("transactionHash")),
            "pool": Web3.to_checksum_address(pool_address),
            "sender": Web3.to_checksum_address(sender),
            "recipient": Web3.to_checksum_address(recipient),
            "amount0": amount0,
            "amount1": amount1,
            "sqrtPriceX96": sqrt_price_x96,
            "liquidity": liquidity,
            "tick": tick,
        }
        
    except Exception:
        return None