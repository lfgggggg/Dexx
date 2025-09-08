"""
Basic token operations example
"""

import asyncio
import os
from nadfun_sdk import Token
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configuration
    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    token_address = os.getenv("TOKEN")
    recipient = os.getenv("RECIPIENT")
    
    if not all([rpc_url, private_key, token_address]):
        print("Please set RPC_URL, PRIVATE_KEY and TOKEN environment variables")
        return
    
    # Initialize Token helper
    token = Token(rpc_url, private_key)
    
    print(f"Token Operations Demo")
    print(f"Token: {token_address}")
    print(f"Wallet: {token.wallet_address}")
    print("-" * 50)
    
    # Get token metadata
    print("\n1. Token Metadata")
    metadata = await token.get_metadata(token_address)
    print(f"   Name: {metadata.name}")
    print(f"   Symbol: {metadata.symbol}")
    print(f"   Decimals: {metadata.decimals}")
    print(f"   Total Supply: {metadata.total_supply / (10 ** metadata.decimals):.2f}")
    
    # Get balance
    print("\n2. Balance Check")
    balance = await token.get_balance(token_address)
    formatted_balance = balance / (10 ** metadata.decimals)
    print(f"   Balance: {formatted_balance:.4f} {metadata.symbol}")
    
    # Check allowance (if recipient provided)
    if recipient:
        print("\n3. Allowance Check")
        allowance = await token.get_allowance(token_address, recipient)
        formatted_allowance = allowance / (10 ** metadata.decimals)
        print(f"   Allowance to {recipient[:10]}...: {formatted_allowance:.4f} {metadata.symbol}")
        
        # Transfer example (small amount)
        if balance > 0:
            print("\n4. Transfer Example")
            transfer_amount = min(balance // 100, 10 ** metadata.decimals)  # 1% or 1 token
            formatted_transfer = transfer_amount / (10 ** metadata.decimals)
            
            print(f"   Transferring {formatted_transfer:.4f} {metadata.symbol} to {recipient[:10]}...")
            
            tx_hash = await token.transfer(token_address, recipient, transfer_amount)
            print(f"   Transaction: {tx_hash}")
            
            print("   Waiting for confirmation...")
            receipt = await token.wait_for_transaction(tx_hash)
            
            if receipt["status"] == 1:
                print(f"   Transfer successful! Gas used: {receipt['gasUsed']}")
                
                # Check new balance
                new_balance = await token.get_balance(token_address)
                new_formatted = new_balance / (10 ** metadata.decimals)
                print(f"   New balance: {new_formatted:.4f} {metadata.symbol}")
            else:
                print("   Transfer failed")
        else:
            print("\n   No balance to transfer")
    else:
        print("\n   ℹ️ Set RECIPIENT environment variable to test transfers and allowances")
    
    # Get formatted balance
    print("\n5. Formatted Balance")
    raw_balance, formatted_str = await token.get_balance_formatted(token_address)
    print(f"   Raw: {raw_balance}")
    print(f"   Formatted: {formatted_str} {metadata.symbol}")

if __name__ == "__main__":
    asyncio.run(main())