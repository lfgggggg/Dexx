"""
Historical event indexing for bonding curve events
"""

import asyncio
import os
from nadfun_sdk import CurveIndexer, EventType
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configuration from environment
    rpc_url = os.getenv("RPC_URL")
    token = os.getenv("TOKEN")
    
    if not rpc_url:
        print("Please set RPC_URL in .env file")
        return
    
    # Initialize indexer
    indexer = CurveIndexer(rpc_url)
    print("Curve Indexer initialized")
    print("=" * 60)
    
    # Get current block
    latest_block = await indexer.get_block_number()
    
    # Define block range (last 1000 blocks)
    from_block = max(0, latest_block - 100)
    to_block = latest_block
    
    print(f"Fetching events from block {from_block} to {to_block}")
    print("-" * 60)
    
    # Example 1: Fetch all event types
    print("\n1. Fetching all curve events...")
    all_events = await indexer.fetch_events(from_block, to_block, token_filter=token)   
    print(f"Found {len(all_events)} total events")
    
    # Count by event type
    event_counts = {}
    for event in all_events:
        event_name = event['eventName']
        event_counts[event_name] = event_counts.get(event_name, 0) + 1
    
    if event_counts:
        print("\nEvent counts by type:")
        for event_type, count in event_counts.items():
            print(f"  {event_type}: {count}")
    
    # Example 2: Fetch only BUY and SELL events
    print("\n2. Fetching only BUY and SELL events...")
    trade_events = await indexer.fetch_events(
        from_block,
        to_block,
        event_types=[EventType.BUY, EventType.SELL]
    )
    print(f"Found {len(trade_events)} trade events")
    
    # Show sample events
    if trade_events and len(trade_events) > 0:
        print("\nSample trade events:")
        for event in trade_events[:3]:  # Show first 3
            print(f"\n  {event['eventName']} Event:")
            print(f"    Block: {event['blockNumber']}")
            print(f"    Trader: {event['trader']}")
            print(f"    Token: {event['token']}")
            print(f"    Amount In: {event['amountIn']}")
            print(f"    Amount Out: {event['amountOut']}")
            print(f"    Timestamp: {event['timestamp']}")
            print(f"    Tx: {event['transactionHash'][:10]}...")
    
    # Example 3: Filter by token if provided
    if token:
        print(f"\n3. Fetching events for token {token}...")
        token_events = await indexer.fetch_events(
            from_block,
            to_block,
            token_filter=token
        )
        print(f"Found {len(token_events)} events for this token")
        
        if token_events:
            print("\nLatest event for this token:")
            latest = token_events[-1]
            print(f"  Type: {latest['eventName']}")
            print(f"  Block: {latest['blockNumber']}")
            print(f"  Timestamp: {latest['timestamp']}")
    
    # Example 4: Fetch specific event types
    print("\n4. Fetching CREATE events only...")
    create_events = await indexer.fetch_events(
        from_block,
        to_block,
        event_types=[EventType.CREATE]
    )
    print(f"Found {len(create_events)} new curve creations")
    
    if create_events:
        print("\nRecent curve creations:")
        for event in create_events[:3]:
            print(f"  Token: {event['token']} at block {event['blockNumber']}")
    
    print("\n" + "=" * 60)
    print("Indexing complete!")

if __name__ == "__main__":
    asyncio.run(main())