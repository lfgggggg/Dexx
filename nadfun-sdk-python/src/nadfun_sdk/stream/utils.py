"""
Common utility functions for stream modules
"""

from typing import Any


def extract_address_from_topic(topic: Any) -> str:
    """Extract Ethereum address from event log topic
    
    Args:
        topic: Topic data (can be bytes, HexBytes, or string)
        
    Returns:
        Lowercase hex address string (without 0x prefix)
    """
    if hasattr(topic, 'hex'):
        topic_hex = topic.hex()
    elif isinstance(topic, bytes):
        topic_hex = topic.hex()
    elif isinstance(topic, str):
        topic_hex = topic[2:] if topic.startswith('0x') else topic
    else:
        topic_hex = str(topic)
    
    # Topics are 32 bytes, addresses are 20 bytes (last 40 hex chars)
    return topic_hex[-40:]


def parse_log_data(data: Any) -> bytes:
    """Convert log data from various formats to bytes
    
    Args:
        data: Log data (can be HexBytes, string, or bytes)
        
    Returns:
        Data as bytes
    """
    if not data:
        return b""
    
    # Handle HexBytes
    if hasattr(data, 'hex'):
        return data
    
    # Handle string
    if isinstance(data, str):
        return bytes.fromhex(data[2:] if data.startswith('0x') else data)
    
    # Already bytes
    if isinstance(data, bytes):
        return data
    
    return b""


def format_tx_hash(tx_hash: Any) -> str:
    """Format transaction hash to string
    
    Args:
        tx_hash: Transaction hash (can be HexBytes or string)
        
    Returns:
        Transaction hash as hex string with 0x prefix
    """
    if hasattr(tx_hash, 'hex'):
        return tx_hash.hex()
    elif isinstance(tx_hash, bytes):
        return '0x' + tx_hash.hex()
    elif isinstance(tx_hash, str):
        return tx_hash if tx_hash.startswith('0x') else '0x' + tx_hash
    else:
        return str(tx_hash)