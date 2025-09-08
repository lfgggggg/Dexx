# Nad.fun Python SDK

A comprehensive Python SDK for interacting with Nad.fun ecosystem contracts on Monad blockchain, including bonding curves, DEX trading, and real-time event monitoring.

## Features

- 🚀 **Trading**: Execute buy/sell operations on bonding curves with slippage protection
- 💰 **Token Operations**: ERC-20 token interactions (balance, approve, transfer)
- 📊 **Bonding Curves**: Query curve parameters and check listing status
- 🔄 **Real-time Streaming**: Monitor bonding curve and DEX events via WebSocket with token filtering
- 📚 **Historical Indexing**: Fetch and analyze past events with CurveIndexer and DexIndexer
- ⚡ **Async/Await**: Fully asynchronous design for high performance
- 🔐 **Type Safety**: Full type hints for better IDE support

## Installation

```bash
pip install nadfun-sdk
```

Or install from source:

```bash
git clone https://github.com/naddotfun/nadfun-sdk-python.git
cd nadfun-sdk-python
pip install -e .
```

## Quick Start

```python
import asyncio
from nadfun_sdk import Trade, BuyParams, calculate_slippage, parseMon

async def main():
    # Initialize trade client
    trade = Trade(rpc_url="https://monad-testnet.rpc.url", private_key="your_private_key")

    # Get quote for buying tokens
    token = "0x1957d1BED06c69f479f564E9Dc163e3Cf4E3eF03"
    amount_in = parseMon(1)  # 1 MON
    quote = await trade.get_amount_out(token, amount_in, is_buy=True)

    # Execute buy with slippage protection
    params = BuyParams(
        token=token,
        to=trade.address,
        amount_in=amount_in,
        amount_out_min=calculate_slippage(quote.amount, 5)  # 5% slippage tolerance
    )
    tx_hash = await trade.buy(params, quote.router)
    print(f"Transaction: {tx_hash}")

asyncio.run(main())
```

## Core Modules

### 🚀 Trading

Execute trades on bonding curves with automatic routing:

```python
from nadfun_sdk import Trade, BuyParams, SellParams, calculate_slippage

trade = Trade(rpc_url, private_key)

# Get quotes
buy_quote = await trade.get_amount_out(token, mon_amount, is_buy=True)
sell_quote = await trade.get_amount_out(token, token_amount, is_buy=False)

# Buy tokens
buy_params = BuyParams(
    token=token,
    to=wallet_address,
    amount_in=mon_amount,
    amount_out_min=calculate_slippage(buy_quote.amount, 5),
    deadline=None  # Auto-sets to now + 120 seconds
)
tx = await trade.buy(buy_params, buy_quote.router)

# Sell tokens
sell_params = SellParams(
    token=token,
    to=wallet_address,
    amount_in=token_amount,
    amount_out_min=calculate_slippage(sell_quote.amount, 5),
    deadline=None
)
tx = await trade.sell(sell_params, sell_quote.router)

# Wait for transaction
receipt = await trade.wait_for_transaction(tx, timeout=60)
```

### 💰 Token Operations

Interact with ERC-20 tokens:

```python
from nadfun_sdk import Token

token = Token(rpc_url, private_key)

# Get token metadata
metadata = await token.get_metadata(token_address)
print(f"Token: {metadata['name']} ({metadata['symbol']})")
print(f"Decimals: {metadata['decimals']}")
print(f"Total Supply: {metadata['totalSupply']}")

# Check balances
balance = await token.get_balance(token_address)
balance = await token.get_balance(token_address, owner_address)  # Check other address

# Check allowance
allowance = await token.get_allowance(token_address, spender_address)

# Approve tokens
tx = await token.approve(token_address, spender_address, amount)

# Transfer tokens
tx = await token.transfer(token_address, recipient_address, amount)

# Smart approval (only approves if needed)
tx = await token.check_and_approve(token_address, spender_address, required_amount)
```

### 📊 Bonding Curve Data

Query bonding curve information:

```python
# Check if token is listed on curve
is_listed = await trade.is_listed(token_address)

# Get curve reserves
curve_data = await trade.get_curves(token_address)
print(f"Reserve MON: {curve_data.reserve_mon}")
print(f"Reserve Token: {curve_data.reserve_token}")

# Get amount needed for specific output
quote = await trade.get_amount_in(token_address, desired_output, is_buy=True)
```

### 🔄 Real-time Event Streaming

Monitor events in real-time using WebSocket connections:

#### Curve Events Stream

```python
from nadfun_sdk import CurveStream, EventType, CurveEvent

# Initialize stream
stream = CurveStream(ws_url)

# Subscribe to specific events
stream.subscribe([EventType.BUY])  # Only BUY events
stream.subscribe([EventType.SELL])  # Only SELL events
stream.subscribe([EventType.BUY, EventType.SELL])  # Both
stream.subscribe()  # All events (default)

# Filter by token addresses (optional)
stream.subscribe(
    [EventType.BUY, EventType.SELL],
    token_addresses=["0x1234...", "0x5678..."]  # Only events from these tokens
)

# Process events with typed async iterator
event: CurveEvent
async for event in stream.events():
    print(f"Event: {event['eventName']}")      # "BUY" or "SELL"
    print(f"Trader: {event['trader']}")        # Buyer/Seller address
    print(f"Token: {event['token']}")          # Token address
    print(f"Amount In: {event['amountIn']}")   # MON for buy, tokens for sell
    print(f"Amount Out: {event['amountOut']}") # Tokens for buy, MON for sell
    print(f"Block: {event['blockNumber']}")
    print(f"Tx: {event['transactionHash']}")
```

#### DEX Swap Events Stream

```python
from nadfun_sdk import DexStream, DexSwapEvent

# Initialize stream
stream = DexStream(ws_url)

# Subscribe to tokens (automatically finds pools)
stream.subscribe_tokens("0x1234...")  # Single token
stream.subscribe_tokens(["0x1234...", "0x5678..."])  # Multiple tokens

# Process swap events with typed iterator
event: DexSwapEvent
async for event in stream.events():
    print(f"Event: {event['eventName']}")
    print(f"BlockNumber: {event['blockNumber']}")
    print(f"Pool: {event['pool']}")
    print(f"Sender: {event['sender']}")
    print(f"Recipient: {event['recipient']}")
    print(f"Amount0: {event['amount0']}")
    print(f"Amount1: {event['amount1']}")
    print(f"Liquidity: {event['liquidity']}")
    print(f"Tick: {event['tick']}")
    print(f"Price (sqrt X96): {event['sqrtPriceX96']}")
    print(f"Tx: {event['transactionHash']}")
    print("-" * 50)
```

### 📚 Historical Event Indexing

Index historical blockchain events for analysis:

#### Curve Indexer

```python
from nadfun_sdk import CurveIndexer, EventType

# Initialize indexer
indexer = CurveIndexer(rpc_url)

# Get current block number
latest_block = await indexer.get_block_number()
from_block = latest_block - 1000  # Last 1000 blocks

# Fetch all events
all_events = await indexer.fetch_events(from_block, latest_block)

# Filter by event types
trade_events = await indexer.fetch_events(
    from_block,
    latest_block,
    event_types=[EventType.BUY, EventType.SELL]
)

# Filter by token
token_events = await indexer.fetch_events(
    from_block,
    latest_block,
    token_filter="0x1234..."
)
```

#### DEX Indexer

```python
from nadfun_sdk import DexIndexer

# Initialize indexer
indexer = DexIndexer(rpc_url)

# Get current block number
latest_block = await indexer.get_block_number()

# Fetch swap events by tokens (automatically finds pools)
swap_events = await indexer.fetch_events(
    from_block,
    latest_block,
    tokens=["0x1234...", "0x5678..."]
)

# Or fetch by specific pool addresses
pool_events = await indexer.fetch_events(
    from_block,
    latest_block,
    pools="0xabcd..."
)
```

## API Reference

### Trade Class

```python
trade = Trade(rpc_url: str, private_key: str)
```

#### Methods

- `async get_amount_out(token: str, amount_in: int, is_buy: bool) -> QuoteResult`

  - Get expected output amount for a trade
  - Returns `QuoteResult` with `router` address and `amount`

- `async get_amount_in(token: str, amount_out: int, is_buy: bool) -> QuoteResult`

  - Get required input amount for desired output
  - Returns `QuoteResult` with `router` address and `amount`

- `async buy(params: BuyParams, router: str, nonce: int = None, gas: int = None) -> str`

  - Execute buy transaction
  - Returns transaction hash

- `async sell(params: SellParams, router: str, nonce: int = None, gas: int = None) -> str`

  - Execute sell transaction
  - Returns transaction hash

- `async is_listed(token: str) -> bool`

  - Check if token is listed on bonding curve

- `async get_curves(token: str) -> CurveData`

  - Get bonding curve reserves
  - Returns `CurveData` with `reserve_mon` and `reserve_token`

- `async wait_for_transaction(tx_hash: str, timeout: int = 60) -> Dict`
  - Wait for transaction confirmation

### Token Class

```python
token = Token(rpc_url: str, private_key: str)
```

#### Methods

- `async get_balance(token: str, address: str = None) -> int`

  - Get token balance (defaults to own address)

- `async get_allowance(token: str, spender: str, owner: str = None) -> int`

  - Get approved amount (defaults to own address as owner)

- `async get_metadata(token: str) -> TokenMetadata`

  - Get token metadata (name, symbol, decimals, totalSupply)

- `async approve(token: str, spender: str, amount: int) -> str`

  - Approve tokens for spending

- `async transfer(token: str, to: str, amount: int) -> str`

  - Transfer tokens

- `async check_and_approve(token: str, spender: str, required: int, buffer_percent: float = 10) -> Optional[str]`
  - Smart approval - only approves if current allowance is insufficient

### Stream Classes

#### CurveStream

```python
stream = CurveStream(ws_url: str)
```

- `subscribe(event_types: List[EventType] = None)` - Set events to subscribe to
- `async events() -> AsyncIterator[Dict]` - Async iterator yielding parsed events

#### DexStream

```python
stream = DexStream(ws_url: str)
```

- `subscribe_tokens(token_addresses: Union[str, List[str]])` - Set tokens to monitor
- `async events() -> AsyncIterator[Dict]` - Async iterator yielding swap events

### Indexer Classes

#### CurveIndexer

Historical event indexer for bonding curve events:

```python
indexer = CurveIndexer(rpc_url: str)
```

- `async fetch_events(from_block: int, to_block: int, event_types: List[EventType] = None, token_filter: str = None) -> List[Dict]`
  - Fetch historical curve events in a block range
  - Optionally filter by event types (CREATE, BUY, SELL, SYNC, LOCK, LISTED)
  - Optionally filter by token address
- `async get_block_number() -> int`
  - Get current block number

#### DexIndexer

Historical event indexer for DEX swap events:

```python
indexer = DexIndexer(rpc_url: str)
```

- `async fetch_events(from_block: int, to_block: int, pools: Union[str, List[str]] = None, tokens: Union[str, List[str]] = None) -> List[Dict]`
  - Fetch historical swap events in a block range
  - Optionally filter by pool address(es) or token address(es)
  - When filtering by tokens, automatically finds pools from V3 factory
- `async get_block_number() -> int`
  - Get current block number

### Type Definitions

```python
class BuyParams:
    token: str          # Token address to buy
    to: str            # Recipient address
    amount_in: int     # MON amount to spend
    amount_out_min: int # Minimum tokens to receive
    deadline: Optional[int] = None  # Transaction deadline
    nonce: Optional[int] = None     # Transaction nonce
    gas: Optional[int] = None       # Gas limit
    gas_price: Optional[int] = None # Gas price

class SellParams:
    token: str          # Token address to sell
    to: str            # Recipient address
    amount_in: int     # Token amount to sell
    amount_out_min: int # Minimum MON to receive
    deadline: Optional[int] = None
    nonce: Optional[int] = None
    gas: Optional[int] = None
    gas_price: Optional[int] = None

class QuoteResult:
    router: str        # Router contract address
    amount: int        # Expected amount

class CurveData:
    reserve_mon: int   # MON reserves in curve
    reserve_token: int # Token reserves in curve

class TokenMetadata:
    name: str
    symbol: str
    decimals: int
    totalSupply: int

# Event Types (TypedDict for type hints)
class CurveEvent:
    eventName: str          # "BUY" or "SELL"
    blockNumber: int        # Block number
    transactionHash: str    # Transaction hash
    trader: str            # Buyer/Seller address
    token: str             # Token address
    amountIn: int          # Amount in
    amountOut: int         # Amount out

class DexSwapEvent:
    eventName: str          # "Swap"
    blockNumber: int        # Block number
    transactionHash: str    # Transaction hash
    pool: str              # Pool address
    sender: str            # Sender address
    recipient: str         # Recipient address
    amount0: int           # Token0 amount (can be negative)
    amount1: int           # Token1 amount (can be negative)
    sqrtPriceX96: int      # Square root price
    liquidity: int         # Liquidity
    tick: int              # Price tick
```

### Utilities

- `calculate_slippage(amount: int, percent: float) -> int`
  - Calculate minimum output amount with slippage tolerance
- `parseMon(amount: float | str) -> int`
  - Convert MON amount to wei (18 decimals)

## Configuration

Create a `.env` file in your project root. You can copy from `.env.example`:

```bash
cp .env.example .env
```

### Environment Variables

```bash
# Network endpoints
RPC_URL=                                   # HTTP RPC endpoint for Monad testnet
WS_URL=                                    # WebSocket endpoint for real-time event streaming

# Wallet configuration
PRIVATE_KEY=your_private_key_here         # Private key (without 0x prefix)

# Token addresses
TOKEN=0x...                                # Single token address for trading
TOKENS=0x...                               # Multiple token addresses for DEX monitoring (comma-separated)

# Trading parameters
AMOUNT=                                    # Amount in MON for trading (e.g., 0.1)
SLIPPAGE=                                  # Slippage tolerance percentage (e.g., 5)
```

### Network Information

- **Chain**: Monad Testnet
- **Chain ID**: 10143
- **Native Token**: MON
- **Block Explorer**: https://explorer.monad.net

## Examples

The SDK includes comprehensive examples in the `examples/` directory. First, set up your environment:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Trading Examples

#### Buy Tokens (`examples/trade/buy.py`)

```bash
python examples/trade/buy.py
```

Demonstrates buying tokens on the bonding curve with slippage protection.

#### Sell Tokens (`examples/trade/sell.py`)

```bash
python examples/trade/sell.py
```

Shows selling tokens back to the bonding curve.

### Token Operations (`examples/token_operations.py`)

```bash
python examples/token_operations.py
```

Examples of token interactions:

- Checking balances
- Approving spending
- Transferring tokens
- Getting token metadata

### Real-time Event Streaming

#### Curve Events (`examples/stream/curve_stream.py`)

```bash
python examples/stream/curve_stream.py
```

Stream real-time bonding curve Buy/Sell events with filtering options.

#### DEX Swaps (`examples/stream/dex_stream.py`)

```bash
python examples/stream/dex_stream.py
```

Monitor DEX swap events for specified tokens in real-time.

### Historical Event Indexing

#### Curve Indexer (`examples/stream/curve_indexer.py`)

```bash
python examples/stream/curve_indexer.py
```

Index historical bonding curve events:

- Fetch all event types or filter specific ones
- Filter by token address
- Analyze event patterns

#### DEX Indexer (`examples/stream/dex_indexer.py`)

```bash
python examples/stream/dex_indexer.py
```

Index historical DEX swap events:

- Fetch swap events from V3 pools
- Filter by pool addresses or token addresses
- Analyze swap patterns

## Contract Addresses

All contract addresses are defined in `src/nadfun_sdk/constants.py`:

- **Wrapper Contract**: `0x4F5A3518F082275edf59026f72B66AC2838c0414`
- **Curve Contract**: `0x52D34d8536350Cd997bCBD0b9E9d722452f341F5`
- **Lens Contract**: `0x4F5A3518F082275edf59026f72B66AC2838c0414`
- **V3 Factory**: `0x4f6F577e3bfB25dF11f635d93E5ff645d30CB474`
- **WMON Token**: `0x88CCF31322CEc314E36D0c993651cE14e4AE7B2d`

## Requirements

- Python 3.11+
- web3.py >= 7.0.0
- eth-account
- eth-abi
- python-dotenv

## Development

```bash
# Clone the repository
git clone https://github.com/naddotfun/nadfun-sdk-python.git
cd nadfun-sdk-python

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Format code
black src/ examples/

# Type checking
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📖 [Examples](examples/) - Comprehensive usage examples
- 🐛 [Issues](https://github.com/naddotfun/nadfun-sdk-python/issues) - Bug reports and feature requests
