"""
Token module for ERC20 operations.
"""
from __future__ import annotations
import asyncio
from typing import Optional, Tuple, Dict, Any
from eth_abi import encode
from eth_account import Account
from eth_utils import function_signature_to_4byte_selector, to_checksum_address
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.types import TxParams, Wei

from .utils import load_default_abis
from .constants import CHAIN_ID
from .types import TokenMetadata

def _cs(addr: str) -> str:
    """Convert address to checksum format."""
    return to_checksum_address(addr)


class Token:
    """Token helper class for ERC20 operations."""
    
    def __init__(self, rpc_url: str, private_key: str):
        """Initialize Token helper.
        
        Args:
            rpc_url: RPC endpoint URL
            private_key: Private key for signing transactions
        """
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.address: str = self.account.address
        self.chain_id = CHAIN_ID
        
        # Load ERC20 ABI
        abis = load_default_abis()
        self.erc20_abi = abis["erc20Permit"]
        
        # Pre-compute function selectors for efficiency
        self.approve_sel = function_signature_to_4byte_selector("approve(address,uint256)")
        self.transfer_sel = function_signature_to_4byte_selector("transfer(address,uint256)")
    
    # ─────────────────────────────────────
    # Read operations (view functions)
    # ─────────────────────────────────────
    
    async def get_balance(self, token: str, address: Optional[str] = None) -> int:
        """Get token balance for an address.
        
        Args:
            token: Token contract address
            address: Address to check (defaults to wallet address)
            
        Returns:
            Token balance
        """
        try:
            addr = _cs(address) if address else self.address
            contract = self.w3.eth.contract(address=_cs(token), abi=self.erc20_abi)
            balance = await contract.functions.balanceOf(addr).call()
            return int(balance)
        except Exception as e:
            raise RuntimeError(f"Failed to get balance: {e}")
    
    async def get_allowance(self, token: str, spender: str, owner: Optional[str] = None) -> int:
        """Get token allowance.
        
        Args:
            token: Token contract address
            spender: Spender address
            owner: Owner address (defaults to wallet address)
            
        Returns:
            Allowance amount
        """
        try:
            owner_addr = _cs(owner) if owner else self.address
            contract = self.w3.eth.contract(address=_cs(token), abi=self.erc20_abi)
            allowance = await contract.functions.allowance(owner_addr, _cs(spender)).call()
            return int(allowance)
        except Exception as e:
            raise RuntimeError(f"Failed to get allowance: {e}")
    
    async def get_metadata(self, token: str) -> TokenMetadata:
        """Get token metadata.
        
        Args:
            token: Token contract address
            
        Returns:
            TokenMetadata object
        """
        try:
            contract = self.w3.eth.contract(address=_cs(token), abi=self.erc20_abi)
            
            # Fetch all metadata in parallel for efficiency
            name, symbol, decimals, total_supply = await asyncio.gather(
                contract.functions.name().call(),
                contract.functions.symbol().call(),
                contract.functions.decimals().call(),
                contract.functions.totalSupply().call()
            )
            
            return TokenMetadata(
                name=str(name),
                symbol=str(symbol),
                decimals=int(decimals),
                total_supply=int(total_supply),
                address=_cs(token)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get metadata: {e}")
    
    # ─────────────────────────────────────
    # Write operations (transactions)
    # ─────────────────────────────────────
    
    async def approve(self, token: str, spender: str, amount: int) -> str:
        """Approve token spending.
        
        Args:
            token: Token contract address
            spender: Spender address
            amount: Amount to approve
            
        Returns:
            Transaction hash
        """
        try:
            # Encode approve(address,uint256)
            calldata = self.approve_sel + encode(
                ["address", "uint256"],
                [_cs(spender), int(amount)]
            )
            
            return await self._send_transaction(_cs(token), calldata)
        except Exception as e:
            raise RuntimeError(f"Approval failed: {e}")
    
    async def transfer(self, token: str, to: str, amount: int) -> str:
        """Transfer tokens to another address.
        
        Args:
            token: Token contract address
            to: Recipient address
            amount: Amount to transfer
            
        Returns:
            Transaction hash
        """
        try:
            # Encode transfer(address,uint256)
            calldata = self.transfer_sel + encode(
                ["address", "uint256"],
                [_cs(to), int(amount)]
            )
            
            return await self._send_transaction(_cs(token), calldata)
        except Exception as e:
            raise RuntimeError(f"Transfer failed: {e}")
    
    async def _send_transaction(self, to: str, calldata: bytes, *, value: int = 0) -> str:
        """Internal method to send transactions.
        
        Args:
            to: Recipient address
            calldata: Encoded function call data
            value: ETH value to send
            
        Returns:
            Transaction hash
        """
        # Get current gas price and nonce
        gas_price = int(await self.w3.eth.gas_price)
        nonce = await self.w3.eth.get_transaction_count(self.address, "pending")
        
        # Build transaction
        tx: TxParams = {
            "from": self.address,
            "to": to,
            "data": "0x" + calldata.hex(),
            "value": Wei(value),
            "chainId": self.chain_id,
            "nonce": nonce,
            "gasPrice": Wei(gas_price),
        }
        
        # Estimate gas with buffer
        estimated_gas = await self.w3.eth.estimate_gas(tx)
        tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
        
        # Sign and send
        signed = self.account.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = await self.w3.eth.send_raw_transaction(raw)
        return tx_hash.hex()
    
    # ─────────────────────────────────────
    # Utility methods
    # ─────────────────────────────────────
    
    async def check_and_approve(
        self,
        token: str,
        spender: str,
        required_amount: int,
        *,
        force_new: bool = False
    ) -> Optional[str]:
        """Check allowance and approve if needed.
        
        Args:
            token: Token contract address
            spender: Spender address
            required_amount: Required allowance amount
            force_new: Force new approval even if allowance exists
        
        Returns:
            Transaction hash if approval was needed, None otherwise
        """
        if not force_new:
            current_allowance = await self.get_allowance(token, spender)
            if current_allowance >= required_amount:
                return None
        
        # Use max uint256 for infinite approval if amount is large
        max_uint256 = 2**256 - 1
        approval_amount = max_uint256 if required_amount > 10**24 else required_amount
        
        return await self.approve(token, spender, approval_amount)
    
    async def get_balance_formatted(self, token: str, address: Optional[str] = None) -> Tuple[int, str]:
        """Get token balance with formatted display value.
        
        Args:
            token: Token contract address
            address: Address to check (defaults to wallet address)
        
        Returns:
            Tuple of (raw_balance, formatted_balance_string)
        """
        balance = await self.get_balance(token, address)
        
        # Get decimals for formatting
        contract = self.w3.eth.contract(address=_cs(token), abi=self.erc20_abi)
        decimals = await contract.functions.decimals().call()
        
        # Format with proper decimal places
        formatted = balance / (10 ** decimals)
        formatted_str = f"{formatted:.{decimals}f}".rstrip('0').rstrip('.')
        
        return balance, formatted_str
    
    async def wait_for_transaction(self, tx_hash: str, timeout: int = 60) -> Dict[str, Any]:
        """Wait for a transaction to be mined.
        
        Args:
            tx_hash: Transaction hash to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Transaction receipt
        """
        try:
            receipt = await self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout
            )
            return dict(receipt)
        except Exception as e:
            raise RuntimeError(f"Failed to get transaction receipt: {e}")
    
    @property
    def wallet_address(self) -> str:
        """Get the wallet address."""
        return self.address