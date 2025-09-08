"""
Sell tokens example
"""

import asyncio
import os
from nadfun_sdk import Trade, Token, SellParams, calculate_slippage, parseMon
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configuration
    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    token_address = os.getenv("TOKEN")
    amount = os.getenv("AMOUNT")
    slippage = float(os.getenv("SLIPPAGE"))

    if not private_key or not token_address:
        print("Please set PRIVATE_KEY and TOKEN environment variables")
        return
    
    # Initialize Trade and Token
    trade = Trade(rpc_url, private_key)
    token = Token(rpc_url, private_key)
    
    # Get token balance
    balance = await token.get_balance(token_address)
    if balance == 0:
        print("No tokens to sell")
        return
    
    print(f"Selling {amount} tokens")
    print(f"Token: {token_address}")

    amount_to_sell = parseMon(amount)
    
    # Get quote
    quote = await trade.get_amount_out(token_address, amount_to_sell, is_buy=False)
    print(f"Router: {quote.router}")
    print(f"Expected MON: {quote.amount} MON")
    
    # Calculate minimum MON with slippage
    min_mon = calculate_slippage(quote.amount, slippage)
    print(f"Minimum MON ({slippage}% slippage): {min_mon} MON")
    
    # Check and approve if needed
    print("Checking allowance...")
    tx_hash = await token.check_and_approve(
        token_address,
        quote.router,
        amount_to_sell
    )
    
    if tx_hash:
        print(f"Approval tx: {tx_hash}")
        print("Waiting for approval confirmation...")
        await token.wait_for_transaction(tx_hash)
    
    # Execute sell
    sell_params = SellParams(
        token=token_address,
        amount_in=amount_to_sell,
        amount_out_min=min_mon,
        to=trade.address,
        deadline=None,
        nonce=None,
        gas=None,
        gas_price=None,
    )
    
    tx_hash = await trade.sell(sell_params, quote.router)
    print(f"Transaction submitted: 0x{tx_hash}")
    
    # Wait for confirmation
    print("Waiting for confirmation...")
    receipt = await trade.wait_for_transaction(tx_hash, timeout=60)
    
    if receipt["status"] == 1:
        print(f"Sell successful! Gas used: {receipt['gasUsed']}")
    else:
        print("Transaction failed")

if __name__ == "__main__":
    asyncio.run(main())