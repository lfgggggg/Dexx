"""
Uniswap V3 DEX event stream with async iterator pattern
"""

import asyncio
import json

from typing import List, AsyncIterator, Optional, Dict, Any
from pathlib import Path
from web3 import AsyncWeb3, WebSocketProvider, Web3

from ...constants import CONTRACTS, NADS_FEE_TIER
from ...stream.types import EventType
from .parser import parse_swap_event

class DexStream:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.token_addresses: List[str] = []
        self.pool_addresses: List[str] = []
        self._subscription_id: Optional[str] = None
        self.event_types: List[EventType] = []
        
    def subscribe_tokens(self, token_addresses, event_types: List[EventType] = None):
        """Set which tokens to monitor (will find pools automatically)"""
        # Handle both single string and list of strings
        if isinstance(token_addresses, str):
            token_addresses = [token_addresses]
        self.token_addresses = [Web3.to_checksum_address(addr) for addr in token_addresses]
        if event_types is None:
            event_types = [EventType.SWAP, EventType.MINT, EventType.BURN]
        self.event_types = event_types
        
    async def _discover_pools(self, w3: AsyncWeb3) -> List[str]:
        """Discover V3 pools for configured tokens"""
        if not self.token_addresses:
            return []
            
        # Load factory ABI
        sdk_root = Path(__file__).parent.parent.parent
        abi_path = sdk_root / "abis" / "v3factory.json"
        
        with open(abi_path) as f:
            factory_abi = json.load(f)
        
        factory = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACTS["v3_factory"]),
            abi=factory_abi
        )
        
        wmon = Web3.to_checksum_address(CONTRACTS["wmon"])
        pools = []
        
        for token in self.token_addresses:
            if token.lower() == wmon.lower():
                continue
            
            try:
                # Sort tokens for pool address calculation
                token0, token1 = (token, wmon) if token.lower() < wmon.lower() else (wmon, token)
                
                # Get pool address for 1% fee tier
                pool_address = await factory.functions.getPool(
                    token0,
                    token1,
                    NADS_FEE_TIER
                ).call()
                
                if pool_address and pool_address != "0x0000000000000000000000000000000000000000":
                    pools.append(pool_address)
                    pass
            except Exception as e:
                pass
        
        return pools
    
    async def events(self) -> AsyncIterator[Dict[str, Any]]:
        """Async iterator that yields parsed swap events"""
        # Connect
        async with AsyncWeb3(WebSocketProvider(self.ws_url)) as w3:
            
            # Discover pools
            self.pool_addresses = await self._discover_pools(w3)
            
            if not self.pool_addresses:
                return
            
            # Swap event signature
            swap_topic = Web3.keccak(text="Swap(address,address,int256,int256,uint160,uint128,int24)")
            
            # Create filter
            filter_params = {
                "address": self.pool_addresses,  # Multiple pool addresses
                "topics": [[swap_topic]]  # Just swap events
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
                
                # Parse and yield event
                event = parse_swap_event(log)
                if event:
                    yield event
