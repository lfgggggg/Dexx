"""
Curve event stream with async iterator pattern
"""

from typing import List, AsyncIterator, Optional, Dict, Any
from web3 import AsyncWeb3, WebSocketProvider, Web3
from ...constants import CONTRACTS
from ...stream.types import EventType
from .parser import parse_curve_event

class CurveStream:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.event_types: List[EventType] = []
        self.token_addresses: List[str] = []
        self._subscription_id: Optional[str] = None
        self._w3: Optional[AsyncWeb3] = None
        self._topic_map: Dict[bytes, str] = {}  # topic -> event name mapping
        
    def subscribe(self, event_types: List[EventType] = None, token_addresses: List[str] = None):
        """Set which events to subscribe to"""
        if event_types is None:
            event_types = [EventType.BUY, EventType.SELL]
        self.event_types = event_types

        if token_addresses is not None:
            if isinstance(token_addresses, str):
                token_addresses = [token_addresses]
            # Filter out None and empty strings
            valid_addresses = [addr for addr in token_addresses if addr and addr.strip()]
            self.token_addresses = [Web3.to_checksum_address(addr) for addr in valid_addresses]
        
        
    async def events(self) -> AsyncIterator[Dict[str, Any]]:
        """Async iterator that yields parsed events"""
        # Create topics and mapping
        topics = []
        for event_type in self.event_types:
            topic = AsyncWeb3.keccak(text=event_type.value)
            topics.append(topic)
            self._topic_map[topic] = event_type.name
        
        if not topics:
            return
            
        # Connect and subscribe
        async with AsyncWeb3(WebSocketProvider(self.ws_url)) as w3:
            self._w3 = w3
            
            # Create filter
            filter_params = {
                "address": CONTRACTS["curve"],
                "topics": [topics]  # [[buy, sell]] for OR filter
            }
            
            # Subscribe
            self._subscription_id = await w3.eth.subscribe("logs", filter_params)
            
            
            # Process events
            async for payload in w3.socket.process_subscriptions():
                if payload.get("subscription") != self._subscription_id:
                    continue
                    
                log = payload.get("result")
                if not log:
                    continue
                
                # Determine event type from topic0
                topic0 = log.get("topics", [])[0] if log.get("topics") else None
                if not topic0:
                    continue
                    
                # Convert to bytes if needed
                if hasattr(topic0, 'hex'):
                    topic0_bytes = topic0
                else:
                    topic0_bytes = bytes.fromhex(topic0.replace('0x', ''))
                
                # Get event name from topic
                event_name = self._topic_map.get(topic0_bytes)
                if not event_name:
                    continue
                
                # Parse and yield event
                event = parse_curve_event(log, event_name)
                if event:
                    # Filter by token address if specified
                    if self.token_addresses:
                        event_token = event.get('token', '').lower()
                        if not any(addr.lower() == event_token for addr in self.token_addresses):
                            continue
                    yield event
    
