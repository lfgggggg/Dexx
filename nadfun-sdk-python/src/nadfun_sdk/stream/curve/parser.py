"""
Common event parser for curve events
"""

from typing import Optional, Dict, Any
from web3 import Web3
from eth_abi import decode
from ..utils import extract_address_from_topic, parse_log_data, format_tx_hash


def parse_curve_event(log: Dict[str, Any], event_name: str) -> Optional[Dict[str, Any]]:
    """
    Parse Curve event log (BUY/SELL)
    
    Args:
        log: Web3 log dict
        event_name: Event name (e.g., "BUY", "SELL")
    
    Returns:
        Parsed event dict with CurveEvent structure
    """
    try:
        topics = log.get("topics", [])
        if len(topics) < 3:
            return None
        
        # Parse indexed parameters (topics)
        # topics[1] = trader, topics[2] = token
        trader = "0x" + extract_address_from_topic(topics[1])
        token = "0x" + extract_address_from_topic(topics[2])
        
        # Parse non-indexed parameters (data)
        data_bytes = parse_log_data(log.get("data"))
        
        # Decode amounts
        amount_in, amount_out = decode(["uint256", "uint256"], data_bytes)
        
        return {
            "eventName": event_name,
            "blockNumber": log.get("blockNumber"),
            "transactionHash": "0x"+format_tx_hash(log.get("transactionHash")),
            "trader": Web3.to_checksum_address(trader),
            "token": Web3.to_checksum_address(token),
            "amountIn": amount_in,
            "amountOut": amount_out,
        }
        
    except Exception:
        return None