"""
Wallet Manager for Telegram DEX Bot
Handles wallet creation, import, encryption, and key management
"""

import os
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from eth_account import Account
from web3 import Web3

logger = logging.getLogger(__name__)

class WalletManager:
    """Manages wallet operations including creation, encryption, and key handling"""
    
    def __init__(self, encryption_key: str = None):
        """Initialize wallet manager with encryption key"""
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            # Generate a new encryption key if none provided
            self.encryption_key = Fernet.generate_key()
        
        self.fernet = Fernet(self.encryption_key)
    
    def create_wallet(self, wallet_name: str = "Main Wallet") -> Dict[str, Any]:
        """Create a new wallet with private key and address"""
        try:
            # Generate new account
            account = Account.create()
            
            # Extract private key and address
            private_key = account.key.hex()
            address = account.address
            
            # Encrypt private key
            encrypted_private_key = self.encrypt_private_key(private_key)
            
            return {
                'wallet_name': wallet_name,
                'address': address,
                'encrypted_private_key': encrypted_private_key,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to create wallet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_wallet_from_private_key(self, private_key: str, wallet_name: str = "Imported Wallet") -> Dict[str, Any]:
        """Import wallet from private key"""
        try:
            # Validate and clean private key
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Validate private key format
            if len(private_key) != 64:
                raise ValueError("Invalid private key length")
            
            # Create account from private key
            account = Account.from_key(private_key)
            address = account.address
            
            # Encrypt private key
            encrypted_private_key = self.encrypt_private_key(private_key)
            
            return {
                'wallet_name': wallet_name,
                'address': address,
                'encrypted_private_key': encrypted_private_key,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to import wallet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def encrypt_private_key(self, private_key: str) -> str:
        """Encrypt private key for storage"""
        try:
            # Ensure private key is in bytes
            if isinstance(private_key, str):
                private_key = private_key.encode()
            
            encrypted_key = self.fernet.encrypt(private_key)
            return encrypted_key.decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt private key: {e}")
            raise
    
    def decrypt_private_key(self, encrypted_private_key: str) -> str:
        """Decrypt private key for use"""
        try:
            encrypted_key = encrypted_private_key.encode()
            decrypted_key = self.fernet.decrypt(encrypted_key)
            return decrypted_key.decode()
            
        except Exception as e:
            logger.error(f"Failed to decrypt private key: {e}")
            raise
    
    def get_account_from_wallet(self, encrypted_private_key: str) -> Account:
        """Get Web3 account object from encrypted private key"""
        try:
            private_key = self.decrypt_private_key(encrypted_private_key)
            return Account.from_key(private_key)
        except Exception as e:
            logger.error(f"Failed to get account from wallet: {e}")
            raise
    
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        try:
            return Web3.is_address(address)
        except:
            return False
    
    def get_wallet_balance(self, web3: Web3, address: str) -> Dict[str, Any]:
        """Get wallet balance in ETH and Wei"""
        try:
            balance_wei = web3.eth.get_balance(address)
            balance_eth = web3.from_wei(balance_wei, 'ether')
            
            return {
                'address': address,
                'balance_wei': str(balance_wei),
                'balance_eth': float(balance_eth),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get wallet balance for {address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()