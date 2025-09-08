from __future__ import annotations
import json
import os
import time
from typing import Dict, Any, Optional
from eth_utils import to_checksum_address
from web3 import AsyncWeb3

def to_cs(addr: str) -> str:
    """Convert address to checksum format."""
    return to_checksum_address(addr)

def now_ts() -> int:
    """Get current timestamp in seconds."""
    return int(time.time())

def parseMon(amount) -> int:
    return AsyncWeb3.to_wei(amount, "ether")

# ─────────────────────────────────────
# Slippage utilities
# ─────────────────────────────────────
def calculate_slippage(amount: int, slippage_percent: int = 0) -> int:
    """Calculate minimum output amount with slippage tolerance."""
    if slippage_percent < 0 or slippage_percent > 100:
        raise ValueError("slippage_percent must be between 0 and 100")
    return int(amount * (100 - slippage_percent) / 100)


# ─────────────────────────────────────
# ABI loading
# ─────────────────────────────────────
_ABI_DIR = os.path.join(os.path.dirname(__file__), "abis")

_FILEMAP = {
    "router":       "Router.json",
    "lens":         "lens.json",
    "erc20Permit":  "erc20Permit.json",
    "curve":        "curve.json",
    "v3factory":    "v3factory.json",
    "v3pool":       "v3pool.json",
}

def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        raise FileNotFoundError(f"ABI file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_default_abis() -> Dict[str, Any]:
    """Load all default ABI files."""
    out: Dict[str, Any] = {}
    for key, fname in _FILEMAP.items():
        out[key] = _load_json(os.path.join(_ABI_DIR, fname))
    return out
