"""
Real-time bonding curve event monitoring
"""

import asyncio
import os
from nadfun_sdk import CurveStream, EventType
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configuration
    ws_url = os.getenv("WS_URL")
    tokens = os.getenv("TOKENS")
    
    if not ws_url:
        print("Please set WS_URL environment variable")
        return
    
    print("Bonding Curve Event Stream")
    print(f"WebSocket URL: {ws_url}")
    
    # Initialize stream
    stream = CurveStream(ws_url)
    
    # Subscribe with optional token filter
    if tokens:
        token_list = [t.strip() for t in tokens.split(',') if t.strip()]
        stream.subscribe([EventType.BUY, EventType.SELL], token_addresses=token_list)
    else:
        stream.subscribe([EventType.BUY, EventType.SELL])
    print(f"Subscribing to tokens: {stream.token_addresses}")
    
    print("-" * 50)
    print("Listening for events...")
    
    # Subscribe and process events
    async for event in stream.events():
        print(f"Event: {event['eventName']}")
        print(f"BlockNumber: {event['blockNumber']}")
        print(f"Token: {event['token']}")
        print(f"Amount In: {event['amountIn']}")
        print(f"Amount Out: {event['amountOut']}")
        print(f"Tx: {event['transactionHash']}")
        print("-" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStream stopped by user")