"""
Historical event indexing for DEX swap events
"""

import asyncio
import os
from nadfun_sdk import DexIndexer
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configuration from environment
    rpc_url = os.getenv("RPC_URL")
    tokens = os.getenv("TOKENS")  # Comma-separated list of tokens
    
    if not rpc_url:
        print("Please set RPC_URL in .env file")
        return
    
    # Initialize indexer
    indexer = DexIndexer(rpc_url)
    print("DEX Indexer initialized")
    print("=" * 60)
    
    # Get current block
    latest_block = await indexer.get_block_number()
    
    # Define block range (last 1000 blocks)
    from_block = max(0, latest_block - 1000)
    to_block = latest_block
    
    print(f"Fetching swap events from block {from_block} to {to_block}")
    print("-" * 60)
    
    # Example 1: Fetch swap events for specific tokens
    if tokens:
        token_list = [t.strip() for t in tokens.split(',')]
        print(f"\n1. Fetching swap events for tokens: {token_list[:2]}...")  # Show first 2
        all_swaps = await indexer.fetch_events(
            from_block, 
            to_block, 
            tokens=token_list
        )
        print(f"Found {len(all_swaps)} swap events for these tokens")
    else:
        print("\n1. Fetching all swap events...")
        all_swaps = await indexer.fetch_events(from_block, to_block)
        print(f"Found {len(all_swaps)} total swap events")
    
    # Show sample swaps
    if all_swaps:
        print("\nSample swap events:")
        for swap in all_swaps[:3]:  # Show first 3
            print(f"\n  Swap at block {swap['blockNumber']}:")
            print(f"    Pool: {swap['pool']}")
            print(f"    Sender: {swap['sender']}")
            print(f"    Recipient: {swap['recipient']}")
            print(f"    Amount0: {swap['amount0']}")
            print(f"    Amount1: {swap['amount1']}")
            print(f"    Price (sqrt): {swap['sqrtPriceX96']}")
            print(f"    Liquidity: {swap['liquidity']}")
            print(f"    Tick: {swap['tick']}")
            print(f"    Timestamp: {swap['timestamp']}")
            print(f"    Tx: {swap['transactionHash'][:10]}...")
    
    # Example 2: Filter by specific pool
    if all_swaps and len(all_swaps) > 0:
        # Get a pool from the first swap
        sample_pool = all_swaps[0]['pool']
        print(f"\n2. Fetching swaps for pool {sample_pool}...")
        
        pool_swaps = await indexer.fetch_events(
            from_block,
            to_block,
            pools=sample_pool
        )
        print(f"Found {len(pool_swaps)} swaps for this pool")
    
    # Example 3: Get pools for tokens and fetch their events
    if tokens:
        token_list = [t.strip() for t in tokens.split(',')]
        print(f"\n3. Looking for pools for tokens: {token_list}")
        
        # Get pools for these tokens from V3 factory
        pools = await indexer.get_pools_for_tokens(token_list)
        
        if pools:
            print(f"Found {len(pools)} pools for these tokens:")
            for pool in pools:
                print(f"  - {pool}")
            
            # Fetch swaps for these specific pools
            print("\nFetching swaps for these specific pools...")
            multi_pool_swaps = await indexer.fetch_events(
                from_block,
                to_block,
                pools=pools
            )
            print(f"Found {len(multi_pool_swaps)} swaps across these pools")
        else:
            print("No pools found for these tokens")
    
    # Example 4: Analyze swap patterns
    if all_swaps:
        print("\n4. Swap analysis:")
        
        # Count unique pools
        unique_pools = set(swap['pool'] for swap in all_swaps)
        print(f"  Unique pools: {len(unique_pools)}")
        
        # Count unique traders
        unique_senders = set(swap['sender'] for swap in all_swaps)
        print(f"  Unique senders: {len(unique_senders)}")
        
        # Find most active pool
        pool_counts = {}
        for swap in all_swaps:
            pool = swap['pool']
            pool_counts[pool] = pool_counts.get(pool, 0) + 1
        
        if pool_counts:
            most_active = max(pool_counts.items(), key=lambda x: x[1])
            print(f"  Most active pool: {most_active[0]}")
            print(f"    Swap count: {most_active[1]}")
    
    print("\n" + "=" * 60)
    print("DEX indexing complete!")

if __name__ == "__main__":
    asyncio.run(main())