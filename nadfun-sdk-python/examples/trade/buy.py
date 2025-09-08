"""
Buy tokens example with gas comparison
"""

import asyncio
import os
from nadfun_sdk import Trade, BuyParams, calculate_slippage, parseMon
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configuration
    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    token_address = os.getenv("TOKEN")
    amount = os.getenv("AMOUNT")
    slippage = float(os.getenv("SLIPPAGE"))
    
    if not all([rpc_url, private_key, token_address, amount, slippage]):
        print("Please set RPC_URL, PRIVATE_KEY, TOKEN, AMOUNT, and SLIPPAGE environment variables")
        return
    
    # Initialize Trade
    trade = Trade(rpc_url, private_key)
    
    print(f"Buying tokens with {amount} MON")
    print(f"Token: {token_address}")

    # Amount to spend
    amount_in = parseMon(amount)
    
    # Get quote
    
    quote = await trade.get_amount_out(token_address, amount_in, is_buy=True)
    print(f"Router: {quote.router}")
    print(f"Expected tokens: {quote.amount}")
    
    # Calculate minimum tokens with slippage
    min_tokens = calculate_slippage(quote.amount, slippage)
    print(f"Minimum tokens ({slippage}% slippage): {min_tokens}")
    
    # Execute buy
    buy_params = BuyParams(
        token=token_address,
        amount_in=amount_in,
        amount_out_min=min_tokens,
        to=trade.address,
        deadline=None,
        nonce=None,
        gas=None,
        gas_price=None,
    )
    
    tx_hash = await trade.buy(buy_params, quote.router)
    print(f"Transaction submitted: 0x{tx_hash}")
    
    # Wait for confirmation
    print("Waiting for confirmation...")
    receipt = await trade.wait_for_transaction(tx_hash, timeout=60)
    
    if receipt["status"] == 1:
        print(f"Buy successful! Gas used: {receipt['gasUsed']}")
    else:
        print("Transaction failed")

if __name__ == "__main__":
    asyncio.run(main())