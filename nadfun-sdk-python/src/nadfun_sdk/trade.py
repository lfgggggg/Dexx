"""
Trade module for interacting with NADFUN trading contracts.
"""
from __future__ import annotations
import time
from typing import Dict, Any

from eth_abi import encode
from eth_account import Account
from eth_utils import function_signature_to_4byte_selector, to_checksum_address
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.types import TxParams, Wei

from .utils import load_default_abis
from .constants import CONTRACTS, CHAIN_ID, DEFAULT_DEADLINE_SECONDS
from .types import BuyParams, SellParams, QuoteResult, CurveData

def _cs(addr: str) -> str:
    return to_checksum_address(addr)

class Trade:
    """Main class for executing trades on NADFUN."""
    
    def __init__(self, rpc_url: str, private_key: str):

        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.address: str = self.account.address
        self.chain_id = CHAIN_ID
        
        # Pre-compute function selectors for efficiency
        self.buy_sel = function_signature_to_4byte_selector(
            "buy((uint256,address,address,uint256))"
        )
        self.sell_sel = function_signature_to_4byte_selector(
            "sell((uint256,uint256,address,address,uint256))"
        )
        
        # Load ABIs and initialize contracts
        abis = load_default_abis()
        self.lens = self.w3.eth.contract(
            address=_cs(CONTRACTS["lens"]), 
            abi=abis["lens"]
        )
        self.curve = self.w3.eth.contract(
            address=_cs(CONTRACTS["curve"]), 
            abi=abis["curve"]
        )
        self.erc20_abi = abis["erc20Permit"]

    async def get_amount_out(self, token: str, amount_in: int, is_buy: bool) -> QuoteResult:
        try:
            result = await self.lens.functions.getAmountOut(
                _cs(token), int(amount_in), bool(is_buy)
            ).call()
            return QuoteResult(
                router=_cs(result[0]),
                amount=int(result[1])
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get amount out: {e}")

    async def get_amount_in(self, token: str, amount_out: int, is_buy: bool) -> QuoteResult:
        try:
            result = await self.lens.functions.getAmountIn(
                _cs(token), int(amount_out), bool(is_buy)
            ).call()
            return QuoteResult(
                router=_cs(result[0]),
                amount=int(result[1])
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get amount in: {e}")

    async def get_curves(self, token: str) -> CurveData:

        try:
            data = await self.curve.functions.curves(_cs(token)).call()
            return CurveData(
                reserve_mon=int(data[0]),
                reserve_token=int(data[1]),
                token_supply=int(data[2]),
                virtual_mon=int(data[3]),
                virtual_token=int(data[4]),
                k=int(data[5]),
                target_token_amount=int(data[6]),
                init_virtual_mon_reserve=int(data[7]),
                init_virtual_token_reserve=int(data[8])
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get curve data: {e}")
    
    async def is_listed(self, token: str) -> bool:
        try:
            return bool(await self.curve.functions.isListed(_cs(token)).call())
        except Exception as e:
            raise RuntimeError(f"Failed to check listing status: {e}")

    async def _send_transaction(self, to: str, calldata: bytes, *, value: int = 0, nonce: int = None, gas: int = None, gas_price: int = None) -> str:
        try:
            # Get current gas price and nonce
            if gas_price is None:
                gas_price = int(await self.w3.eth.gas_price)

            if nonce is None:
                nonce = await self.w3.eth.get_transaction_count(self.address, "pending")
            
            # Build transaction
            tx: TxParams = {
                "from": self.address,
                "to": _cs(to),
                "data": "0x" + calldata.hex(),
                "value": Wei(value),
                "chainId": self.chain_id,
                "nonce": nonce,
                "gasPrice": Wei(gas_price),
            }
            
            if gas is None:
                estimated_gas = await self.w3.eth.estimate_gas(tx)
                tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
            
            # Sign and send transaction
            signed = self.account.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
            tx_hash = await self.w3.eth.send_raw_transaction(raw)
            return tx_hash.hex()
            
        except Exception as e:
            raise RuntimeError(f"Transaction failed: {e}")

    async def buy(self, params: BuyParams, router_addr: str) -> str:
        nonce = params.nonce
        gas = params.gas
        gas_price = params.gas_price
        
        # Set deadline if not provided
        deadline = (
            int(time.time()) + DEFAULT_DEADLINE_SECONDS 
            if params.deadline is None 
            else int(params.deadline)
        )
        
        # Encode buy parameters
        encoded_params = encode(
            ["(uint256,address,address,uint256)"],
            [(
                int(params.amount_out_min),
                _cs(params.token),
                _cs(params.to or self.address),
                deadline
            )],
        )
        
        # Send transaction
        return await self._send_transaction(
            router_addr, 
            self.buy_sel + encoded_params,
            value=int(params.amount_in),
            nonce=nonce,
            gas=gas,
            gas_price=gas_price
        )

    async def sell(self, params: SellParams, router_addr: str) -> str:

        nonce = params.nonce
        gas = params.gas
        gas_price = params.gas_price
        
        # Set deadline if not provided
        deadline = (
            int(time.time()) + DEFAULT_DEADLINE_SECONDS
            if params.deadline is None
            else int(params.deadline)
        )
        
        # Encode sell parameters
        encoded_params = encode(
            ["(uint256,uint256,address,address,uint256)"],
            [(
                int(params.amount_in),
                int(params.amount_out_min),
                _cs(params.token),
                _cs(params.to or self.address),
                deadline
            )],
        )
        
        # Send transaction
        return await self._send_transaction(
            router_addr,
            self.sell_sel + encoded_params,
            nonce=nonce,
            gas=gas,
            gas_price=gas_price
        )
    
    async def wait_for_transaction(self, tx_hash: str, timeout: int = 60) -> Dict[str, Any]:
        try:
            receipt = await self.w3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=timeout
            )
            return dict(receipt)
        except Exception as e:
            raise RuntimeError(f"Failed to get transaction receipt: {e}")
